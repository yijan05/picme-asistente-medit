from backend.database import get_connection


def guardar_modelo_3d(
    usuario_id: int,
    ruta_archivo: str,
) -> None:

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO models_3d (
                usuario_id,
                ruta_archivo
            )
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                ruta_archivo = VALUES(ruta_archivo)
            """,
            (
                usuario_id,
                ruta_archivo,
            ),
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def obtener_modelo_3d(usuario_id: int):
    """
    Obtiene la referencia al modelo 3D de un usuario.

    Devuelve un diccionario con los datos o None si no existe.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                usuario_id,
                ruta_archivo,
                actualizado_en
            FROM models_3d
            WHERE usuario_id = %s
            LIMIT 1
            """,
            (usuario_id,),
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def eliminar_modelo_3d(usuario_id: int) -> None:
    """
    Elimina la referencia al modelo 3D de un usuario.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM models_3d
            WHERE usuario_id = %s
            """,
            (usuario_id,),
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()