"""
Consultas de estadísticas para el backend de PicMe.

Este módulo contiene únicamente operaciones de consulta
sobre los registros de acceso.
"""

from backend.database import get_connection


def obtener_estadisticas_accesos():
    """
    Obtiene estadísticas generales de los accesos registrados.

    Devuelve un diccionario con:
        - total
        - exitosos
        - fallidos
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(
                    SUM(
                        CASE
                            WHEN resultado = 'EXITO' THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS exitosos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN resultado = 'FALLO' THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS fallidos
            FROM access_logs
            """
        )

        resultado = cursor.fetchone()

        return {
            "total": int(resultado["total"]),
            "exitosos": int(resultado["exitosos"]),
            "fallidos": int(resultado["fallidos"]),
        }

    finally:
        cursor.close()
        connection.close()