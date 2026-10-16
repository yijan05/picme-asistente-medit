from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from mysql.connector import IntegrityError
from pydantic import BaseModel
from werkzeug.security import check_password_hash, generate_password_hash

from backend.admin_repository import listar_usuarios
from backend.auth import (
    crear_access_token,
    verificar_access_token,
    verificar_rol,
)
from backend.biometric_repository import (
    eliminar_plantilla_biometrica,
    guardar_plantilla_biometrica,
    obtener_plantilla_biometrica,
)
from backend.config import HOST, PORT
from backend.database import get_connection
from backend.users_repository import (
    crear_usuario,
    obtener_usuario_por_correo,
    obtener_usuario_por_id,
)


app = FastAPI(
    title="PicMe Backend",
    version="1.0.0",
)


security = HTTPBearer(
    auto_error=False,
)


class UserCreateRequest(BaseModel):
    """Datos necesarios para crear un usuario."""

    nombre: str
    correo: str
    password_hash: str
    rol: str = "USER"


class LoginRequest(BaseModel):
    """Datos necesarios para iniciar sesión."""

    correo: str
    password_hash: str


class BiometricTemplateRequest(BaseModel):
    """Datos necesarios para registrar una plantilla biométrica."""

    usuario_id: int
    ruta_svm: str
    num_muestras: int


def obtener_usuario_autenticado(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
) -> dict:
    """
    Obtiene y verifica el JWT enviado en la cabecera Authorization.

    Requiere:

        Authorization: Bearer <token>

    Devuelve el payload del JWT si es válido.

    Responde con 401 si:
    - no se envía token,
    - el esquema de autenticación no es válido,
    - el token está mal formado,
    - el token está expirado,
    - o el token no puede verificarse.
    """

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Autenticación requerida.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:
        payload = verificar_access_token(
            credentials.credentials
        )

    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    return payload


def requerir_admin(
    usuario_actual: dict = Depends(
        obtener_usuario_autenticado
    ),
) -> dict:
    

    try:
        return verificar_rol(
            usuario_actual,
            {"ADMIN"},
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        ) from exc


@app.get("/health")
def health_check():
    """
    Comprueba que el backend y la base de datos estén funcionando.

    Este endpoint es público.
    """

    connection = None

    try:
        connection = get_connection()

        if not connection.is_connected():
            return {
                "status": "error",
                "database": "disconnected",
            }

        return {
            "status": "ok",
            "database": "connected",
        }

    except RuntimeError:
        return {
            "status": "error",
            "database": "disconnected",
        }

    finally:
        if connection is not None and connection.is_connected():
            connection.close()


@app.get("/users")
def get_users(
    usuario_actual: dict = Depends(
        requerir_admin
    ),
):
    """
    Devuelve la lista de usuarios registrados.

    Requiere:
    - JWT válido.
    - Rol ADMIN.

    En este endpoint la autorización administrativa
    se aplica mediante la dependencia requerir_admin.
    """

    return listar_usuarios()


@app.get("/users/{usuario_id}")
def get_user(
    usuario_id: int,
    usuario_actual: dict = Depends(
        obtener_usuario_autenticado
    ),
):


    rol = usuario_actual.get("rol")

    if not isinstance(rol, str):
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    rol = rol.strip().upper()

    if rol not in {"USER", "ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    if rol == "USER":
        try:
            usuario_autenticado_id = int(
                usuario_actual.get("sub")
            )

        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            ) from exc

        if usuario_autenticado_id != usuario_id:
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            )

    usuario = obtener_usuario_por_id(usuario_id)

    if usuario is None:
        return None

    return {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "correo": usuario["correo"],
        "rol": usuario["rol"],
        "creado_en": usuario["creado_en"],
    }


@app.get("/users/by-email/{correo}")
def get_user_by_email(
    correo: str,
    usuario_actual: dict = Depends(
        obtener_usuario_autenticado
    ),
):
    """
    Devuelve los datos públicos de un usuario por su correo.

    Requiere un JWT válido.

    Los usuarios USER solamente pueden consultar
    su propio correo.

    Los usuarios ADMIN pueden consultar cualquier correo.

    El hash de contraseña no se devuelve.
    """

    rol = usuario_actual.get("rol")

    if not isinstance(rol, str):
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    rol = rol.strip().upper()

    if rol not in {"USER", "ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    correo_solicitado = correo.strip()

    if rol == "USER":
        correo_autenticado = usuario_actual.get("correo")

        if not isinstance(correo_autenticado, str):
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            )

        if (
            correo_autenticado.strip().lower()
            != correo_solicitado.lower()
        ):
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            )

    usuario = obtener_usuario_por_correo(
        correo_solicitado
    )

    if usuario is None:
        return None

    return {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "correo": usuario["correo"],
        "rol": usuario["rol"],
        "creado_en": usuario["creado_en"],
    }


@app.post("/users")
def create_user(
    user: UserCreateRequest,
    usuario_actual: dict = Depends(
        requerir_admin
    ),
):
   

    nombre = user.nombre.strip()
    correo = user.correo.strip()
    password = user.password_hash.strip()
    rol = user.rol.strip().upper()

    if not nombre:
        raise HTTPException(
            status_code=400,
            detail="El nombre es obligatorio.",
        )

    if not correo:
        raise HTTPException(
            status_code=400,
            detail="El correo electrónico es obligatorio.",
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="El password_hash es obligatorio.",
        )

    if rol not in {"USER", "ADMIN"}:
        raise HTTPException(
            status_code=400,
            detail="El rol debe ser USER o ADMIN.",
        )

    password_hash = generate_password_hash(password)

    try:
        usuario_id = crear_usuario(
            nombre=nombre,
            correo=correo,
            password_hash=password_hash,
            rol=rol,
        )

    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="El correo electrónico ya está registrado.",
        ) from exc

    return {
        "id": usuario_id,
        "nombre": nombre,
        "correo": correo,
        "rol": rol,
    }


@app.post("/biometric-templates")
def create_biometric_template(
    template: BiometricTemplateRequest,
    usuario_actual: dict = Depends(
        obtener_usuario_autenticado
    ),
):


    rol = usuario_actual.get("rol")

    if not isinstance(rol, str):
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    rol = rol.strip().upper()

    if rol not in {"USER", "ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    if template.usuario_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="El usuario_id debe ser válido.",
        )

    ruta_svm = template.ruta_svm.strip()

    if not ruta_svm:
        raise HTTPException(
            status_code=400,
            detail="La ruta_svm es obligatoria.",
        )

    if template.num_muestras < 0:
        raise HTTPException(
            status_code=400,
            detail="El número de muestras no puede ser negativo.",
        )

    if rol == "USER":
        try:
            usuario_autenticado_id = int(
                usuario_actual.get("sub")
            )

        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            ) from exc

        if usuario_autenticado_id != template.usuario_id:
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            )

    guardar_plantilla_biometrica(
        usuario_id=template.usuario_id,
        ruta_svm=ruta_svm,
        num_muestras=template.num_muestras,
    )

    return {
        "usuario_id": template.usuario_id,
        "ruta_svm": ruta_svm,
        "num_muestras": template.num_muestras,
    }


@app.get("/biometric-templates/{usuario_id}")
def get_biometric_template(
    usuario_id: int,
    usuario_actual: dict = Depends(
        obtener_usuario_autenticado
    ),
):
    """
    Obtiene la plantilla biométrica de un usuario.

    Requiere:
    - JWT válido.
    - Un usuario USER solamente puede consultar su propia plantilla.
    - Un usuario ADMIN puede consultar cualquier plantilla.
    """

    rol = usuario_actual.get("rol")

    if not isinstance(rol, str):
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    rol = rol.strip().upper()

    if rol not in {"USER", "ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    if usuario_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="El usuario_id debe ser válido.",
        )

    if rol == "USER":
        try:
            usuario_autenticado_id = int(
                usuario_actual.get("sub")
            )

        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            ) from exc

        if usuario_autenticado_id != usuario_id:
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            )

    plantilla = obtener_plantilla_biometrica(
        usuario_id
    )

    if plantilla is None:
        return None

    return {
        "usuario_id": plantilla["usuario_id"],
        "ruta_svm": plantilla["ruta_svm"],
        "num_muestras": plantilla["num_muestras"],
        "actualizado_en": plantilla["actualizado_en"],
    }


@app.delete("/biometric-templates/{usuario_id}")
def delete_biometric_template(
    usuario_id: int,
    usuario_actual: dict = Depends(
        obtener_usuario_autenticado
    ),
):
   

    rol = usuario_actual.get("rol")

    if not isinstance(rol, str):
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    rol = rol.strip().upper()

    if rol not in {"USER", "ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    if usuario_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="El usuario_id debe ser válido.",
        )

    if rol == "USER":
        try:
            usuario_autenticado_id = int(
                usuario_actual.get("sub")
            )

        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            ) from exc

        if usuario_autenticado_id != usuario_id:
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            )

    eliminar_plantilla_biometrica(
        usuario_id
    )

    return {
        "usuario_id": usuario_id,
        "eliminado": True,
    }


@app.post("/auth/login")
def login(user: LoginRequest):
    

    correo = user.correo.strip()
    password = user.password_hash.strip()

    if not correo:
        raise HTTPException(
            status_code=400,
            detail="El correo electrónico es obligatorio.",
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="El password_hash es obligatorio.",
        )

    usuario = obtener_usuario_por_correo(correo)

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas.",
        )

    if not check_password_hash(
        usuario["password_hash"],
        password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas.",
        )

    access_token = crear_access_token(
        usuario_id=usuario["id"],
        correo=usuario["correo"],
        rol=usuario["rol"],
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "correo": usuario["correo"],
        "rol": usuario["rol"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=False,
    )