"""
Conexión básica a la base de datos MySQL del backend de PicMe.

Este módulo solamente prepara la conexión.
Todavía no crea tablas ni modifica datos.
"""

import os

import mysql.connector
from mysql.connector import Error


DB_HOST = os.getenv("PICME_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("PICME_DB_PORT", "3306"))
DB_NAME = os.getenv("PICME_DB_NAME", "picme")
DB_USER = os.getenv("PICME_DB_USER", "root")
DB_PASSWORD = os.getenv("PICME_DB_PASSWORD", "")


def get_connection():
    """
    Crea y devuelve una conexión a MySQL.

    La conexión se crea únicamente cuando se solicita.
    """
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    except Error as exc:
        raise RuntimeError(
            "No se pudo conectar a la base de datos MySQL."
        ) from exc