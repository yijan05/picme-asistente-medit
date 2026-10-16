"""
Seguridad: hashing de contraseñas y cifrado en reposo de las plantillas
biométricas y de los modelos 3D faciales.

Diseño:
- Las contraseñas nunca se guardan en texto plano: se guarda un hash
  PBKDF2 mediante werkzeug.security.
- Las plantillas biométricas se cifran con AES-256-GCM.
- El modelo 3D completo (OBJ + MTL + textura JPG) también se cifra con
  AES-256-GCM antes de permanecer en disco.
- La clave se obtiene de PICME_ENCRYPTION_KEY o, solo en desarrollo,
  de data/.dev_encryption_key.
"""
from __future__ import annotations

import base64
import io
import os
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from werkzeug.security import check_password_hash, generate_password_hash

from . import config


def _dev_key_file_path() -> Path:
    """
    Devuelve la ruta de la clave de desarrollo.

    Se calcula en cada llamada porque config.DATA_DIR puede cambiar durante
    las pruebas automatizadas.
    """
    return config.DATA_DIR / ".dev_encryption_key"


# --------------------------------------------------------------------
# Contraseñas
# --------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    """Genera un hash PBKDF2 salteado de la contraseña."""
    return generate_password_hash(
        plain_password,
        method="pbkdf2:sha256",
        salt_length=16,
    )


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Comprueba una contraseña contra su hash."""
    return check_password_hash(password_hash, plain_password)


# --------------------------------------------------------------------
# Clave de cifrado
# --------------------------------------------------------------------
def _load_or_create_dev_key() -> bytes:
    """
    Solo para desarrollo local.

    Si no existe una clave persistente, genera una clave AES-256 y la
    guarda en data/.dev_encryption_key.

    En producción se debe utilizar PICME_ENCRYPTION_KEY.
    """
    config.ensure_directories()

    key_file = _dev_key_file_path()

    if key_file.exists():
        try:
            key = base64.urlsafe_b64decode(key_file.read_text().strip())
        except Exception as exc:
            raise ValueError("La clave de desarrollo no tiene un formato válido") from exc

        if len(key) != 32:
            raise ValueError("La clave de desarrollo debe tener exactamente 32 bytes")

        return key

    key = AESGCM.generate_key(bit_length=256)

    key_file.write_text(
        base64.urlsafe_b64encode(key).decode(),
        encoding="utf-8",
    )

    return key


def get_encryption_key() -> bytes:
    """
    Obtiene la clave AES-256 desde el entorno o desde la clave de
    desarrollo local.
    """
    env_value = os.environ.get(config.ENCRYPTION_KEY_ENV_VAR)

    if env_value:
        try:
            key = base64.urlsafe_b64decode(env_value)
        except Exception as exc:
            raise ValueError(
                f"{config.ENCRYPTION_KEY_ENV_VAR} no contiene una clave Base64 válida"
            ) from exc

        if len(key) != 32:
            raise ValueError(
                f"{config.ENCRYPTION_KEY_ENV_VAR} debe representar exactamente 32 bytes"
            )

        return key

    return _load_or_create_dev_key()


# --------------------------------------------------------------------
# Cifrado AES-256-GCM de blobs
# --------------------------------------------------------------------
class BiometricCipher:
    """
    Envuelve AES-GCM para cifrar datos biométricos.

    Formato en disco:

        nonce(12 bytes) || ciphertext || authentication_tag
    """

    NONCE_SIZE = 12

    def __init__(self, key: bytes | None = None):
        selected_key = key or get_encryption_key()

        if len(selected_key) != 32:
            raise ValueError("AES-256 requiere una clave de exactamente 32 bytes")

        self._aesgcm = AESGCM(selected_key)

    def encrypt(
        self,
        plaintext: bytes,
        associated_data: bytes | None = None,
    ) -> bytes:
        """Cifra un blob y devuelve nonce + ciphertext + tag."""
        nonce = os.urandom(self.NONCE_SIZE)

        ciphertext = self._aesgcm.encrypt(
            nonce,
            plaintext,
            associated_data,
        )

        return nonce + ciphertext

    def decrypt(
        self,
        blob: bytes,
        associated_data: bytes | None = None,
    ) -> bytes:
        """Descifra un blob y valida su autenticidad."""
        if len(blob) < self.NONCE_SIZE + 16:
            raise ValueError("Blob cifrado inválido o incompleto")

        nonce = blob[: self.NONCE_SIZE]
        ciphertext = blob[self.NONCE_SIZE :]

        return self._aesgcm.decrypt(
            nonce,
            ciphertext,
            associated_data,
        )

    def encrypt_file(
        self,
        plaintext: bytes,
        path: Path,
        associated_data: bytes | None = None,
    ) -> None:
        """Cifra un blob y lo escribe en disco."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            self.encrypt(
                plaintext,
                associated_data,
            )
        )

    def decrypt_file(
        self,
        path: Path,
        associated_data: bytes | None = None,
    ) -> bytes:
        """Lee y descifra un archivo."""
        return self.decrypt(
            path.read_bytes(),
            associated_data,
        )


# --------------------------------------------------------------------
# Modelo 3D facial cifrado
# --------------------------------------------------------------------
def _mesh_associated_data(user_id: int) -> bytes:
    """
    Associated Data para el paquete 3D.

    Vincular criptográficamente el paquete al usuario evita que un archivo
    cifrado de un usuario pueda reutilizarse silenciosamente como si fuera
    el modelo de otro usuario.
    """
    return f"picme-mesh:user:{user_id}".encode("utf-8")


def encrypt_mesh_bundle(
    obj_path: Path,
    mtl_path: Path,
    texture_path: Path,
    output_path: Path,
    user_id: int,
    cipher: BiometricCipher | None = None,
) -> Path:
    """
    Empaqueta OBJ + MTL + textura JPG en memoria y cifra el paquete
    completo con AES-GCM.

    El archivo resultante NO contiene ninguna extensión de archivo
    individual accesible directamente sin descifrar.

    Devuelve output_path.
    """
    obj_path = Path(obj_path)
    mtl_path = Path(mtl_path)
    texture_path = Path(texture_path)
    output_path = Path(output_path)

    required_files = (obj_path, mtl_path, texture_path)

    for path in required_files:
        if not path.is_file():
            raise FileNotFoundError(f"No existe el archivo del modelo 3D: {path}")

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.write(obj_path, arcname=obj_path.name)
        archive.write(mtl_path, arcname=mtl_path.name)
        archive.write(texture_path, arcname=texture_path.name)

    cipher = cipher or BiometricCipher()

    encrypted = cipher.encrypt(
        buffer.getvalue(),
        associated_data=_mesh_associated_data(user_id),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encrypted)

    return output_path


@contextmanager
def decrypted_mesh_bundle(
    bundle_path: Path,
    user_id: int,
    cipher: BiometricCipher | None = None,
) -> Iterator[tuple[Path, Path]]:
    """
    Descifra temporalmente un paquete de modelo 3D.

    Produce:
        (obj_path_temporal, texture_path_temporal)

    Los archivos existen únicamente dentro del contexto y se eliminan
    automáticamente al salir.

    El MTL también se extrae porque el OBJ lo referencia.
    """
    bundle_path = Path(bundle_path)

    if not bundle_path.is_file():
        raise FileNotFoundError(f"No existe el modelo 3D cifrado: {bundle_path}")

    cipher = cipher or BiometricCipher()

    encrypted = bundle_path.read_bytes()

    plaintext = cipher.decrypt(
        encrypted,
        associated_data=_mesh_associated_data(user_id),
    )

    with tempfile.TemporaryDirectory(prefix="picme_mesh_") as temp_dir:
        temp_path = Path(temp_dir)

        with zipfile.ZipFile(io.BytesIO(plaintext), mode="r") as archive:
            names = set(archive.namelist())

            obj_names = [name for name in names if name.lower().endswith(".obj")]
            mtl_names = [name for name in names if name.lower().endswith(".mtl")]
            texture_names = [
                name
                for name in names
                if name.lower().endswith((".jpg", ".jpeg", ".png"))
            ]

            if len(obj_names) != 1:
                raise ValueError("El paquete 3D debe contener exactamente un archivo OBJ")

            if len(mtl_names) != 1:
                raise ValueError("El paquete 3D debe contener exactamente un archivo MTL")

            if len(texture_names) != 1:
                raise ValueError(
                    "El paquete 3D debe contener exactamente una textura"
                )

            obj_name = Path(obj_names[0]).name
            mtl_name = Path(mtl_names[0]).name
            texture_name = Path(texture_names[0]).name

            obj_path = temp_path / obj_name
            mtl_path = temp_path / mtl_name
            texture_path = temp_path / texture_name

            archive.extract(obj_names[0], temp_path)
            archive.extract(mtl_names[0], temp_path)
            archive.extract(texture_names[0], temp_path)

            # Validación adicional: evitamos aceptar rutas anidadas o
            # traversal dentro del ZIP.
            if (
                obj_path.parent != temp_path
                or mtl_path.parent != temp_path
                or texture_path.parent != temp_path
            ):
                raise ValueError("El paquete 3D contiene rutas internas no permitidas")

            yield obj_path, texture_path

        # Al abandonar el contexto, TemporaryDirectory elimina OBJ,
        # MTL y textura.
