"""
Consultas administrativas sobre usuarios de PicMe.

Este módulo contiene únicamente operaciones de consulta.
La autorización de administrador se implementará posteriormente
en la capa de autenticación y API.
"""

from backend.database import get_connection


def listar_usuarios():
    """
    Obtiene todos los usuarios registrados.

    Devuelve una lista de diccionarios.
    No incluye la contraseña ni el hash de contraseña.
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
                rol,
                creado_en
            FROM usuarios
            ORDER BY id ASC
            """
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def contar_usuarios() -> int:
    """
    Devuelve la cantidad total de usuarios registrados.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM usuarios
            """
        )

        resultado = cursor.fetchone()

        return int(resultado[0])

    finally:
        cursor.close()
        connection.close()