"""
Funciones de autenticación y autorización mediante JWT
para el backend de PicMe.
"""

from datetime import datetime, timedelta, timezone

import jwt

from backend.config import (
    JWT_ALGORITHM,
    JWT_EXPIRATION_MINUTES,
    JWT_SECRET,
)


def crear_access_token(
    usuario_id: int,
    correo: str,
    rol: str,
) -> str:
    """
    Crea un token JWT para un usuario autenticado.

    El token contiene:
    - sub: ID del usuario
    - correo: correo electrónico
    - rol: rol del usuario
    - iat: fecha de emisión
    - exp: fecha de expiración
    """

    ahora = datetime.now(timezone.utc)

    expiracion = ahora + timedelta(
        minutes=JWT_EXPIRATION_MINUTES
    )

    payload = {
        "sub": str(usuario_id),
        "correo": correo,
        "rol": rol,
        "iat": ahora,
        "exp": expiracion,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def verificar_access_token(token: str) -> dict:
    """
    Verifica y decodifica un token JWT.

    Devuelve el payload si es válido.

    Lanza jwt.InvalidTokenError si el token:
    - está mal formado,
    - fue firmado con otra clave,
    - utiliza otro algoritmo,
    - está expirado,
    - o no puede validarse correctamente.
    """

    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )


def verificar_rol(
    payload: dict,
    roles_permitidos: set[str],
) -> dict:
    """
    Verifica que el usuario autenticado tenga un rol permitido.

    Parámetros:
    - payload: contenido previamente validado del JWT.
    - roles_permitidos: conjunto de roles autorizados.

    Devuelve el payload si el rol está permitido.

    Lanza PermissionError si:
    - el payload no contiene un rol,
    - el rol no es válido,
    - o el rol no está autorizado.
    """

    rol = payload.get("rol")

    if not isinstance(rol, str):
        raise PermissionError(
            "El usuario no tiene un rol válido."
        )

    rol = rol.strip().upper()

    if rol not in {"USER", "ADMIN"}:
        raise PermissionError(
            "El usuario no tiene un rol válido."
        )

    if rol not in roles_permitidos:
        raise PermissionError(
            "El usuario no tiene permisos suficientes."
        )

    return payload