"""
Acceso a las plantillas biométricas de la base de datos central de PicMe.

Este módulo contiene únicamente operaciones de persistencia.
La lógica HTTP, autenticación y reconocimiento se implementarán
posteriormente.
"""

from backend.database import get_connection


def guardar_plantilla_biometrica(
    usuario_id: int,
    ruta_svm: str,
    num_muestras: int,
) -> None:
    """
    Guarda o actualiza la plantilla biométrica de un usuario.

    Existe como máximo una plantilla biométrica por usuario.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO biometric_templates (
                usuario_id,
                ruta_svm,
                num_muestras
            )
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                ruta_svm = VALUES(ruta_svm),
                num_muestras = VALUES(num_muestras)
            """,
            (
                usuario_id,
                ruta_svm,
                num_muestras,
            ),
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def obtener_plantilla_biometrica(usuario_id: int):
    """
    Obtiene la plantilla biométrica de un usuario.

    Devuelve un diccionario con los datos o None si no existe.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                usuario_id,
                ruta_svm,
                num_muestras,
                actualizado_en
            FROM biometric_templates
            WHERE usuario_id = %s
            LIMIT 1
            """,
            (usuario_id,),
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def eliminar_plantilla_biometrica(usuario_id: int) -> None:
    """
    Elimina la plantilla biométrica de un usuario.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM biometric_templates
            WHERE usuario_id = %s
            """,
            (usuario_id,),
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()