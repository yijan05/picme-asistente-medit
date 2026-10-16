"""
Acceso a usuarios de la base de datos central de PicMe.

Este módulo contiene únicamente operaciones de persistencia.
La lógica HTTP y la autenticación se implementarán posteriormente.
"""

from backend.database import get_connection


def crear_usuario(
    nombre: str,
    correo: str,
    password_hash: str,
    rol: str = "USER",
) -> int:
    """
    Crea un usuario y devuelve su ID.

    La base de datos se encarga de impedir correos duplicados.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO usuarios (
                nombre,
                correo,
                password_hash,
                rol
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                nombre,
                correo,
                password_hash,
                rol,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()


def obtener_usuario_por_correo(correo: str):
    """
    Obtiene un usuario por su correo.

    Devuelve un diccionario con sus datos o None si no existe.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                nombre,
                correo,
                password_hash,
                rol,
                creado_en
            FROM usuarios
            WHERE correo = %s
            LIMIT 1
            """,
            (correo,),
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def obtener_usuario_por_id(usuario_id: int):
    """
    Obtiene un usuario por su ID.

    Devuelve un diccionario con sus datos o None si no existe.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                nombre,
                correo,
                password_hash,
                rol,
                creado_en
            FROM usuarios
            WHERE id = %s
            LIMIT 1
            """,
            (usuario_id,),
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()