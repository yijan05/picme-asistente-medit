"""
Acceso a los registros de acceso de la base de datos central de PicMe.

Este módulo contiene únicamente operaciones de persistencia.
La lógica HTTP y la autenticación se implementarán posteriormente.
"""

from backend.database import get_connection


def registrar_acceso(
    usuario_id: int | None,
    resultado: str,
    score: float | None = None,
) -> int:
    """
    Registra un intento de acceso y devuelve su ID.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO access_logs (
                usuario_id,
                resultado,
                score
            )
            VALUES (%s, %s, %s)
            """,
            (
                usuario_id,
                resultado,
                score,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()


def obtener_ultimo_acceso(usuario_id: int):
    """
    Obtiene el último registro de acceso de un usuario.

    Devuelve un diccionario con los datos o None si no existe.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                usuario_id,
                resultado,
                score,
                creado_en
            FROM access_logs
            WHERE usuario_id = %s
            ORDER BY creado_en DESC, id DESC
            LIMIT 1
            """,
            (usuario_id,),
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()