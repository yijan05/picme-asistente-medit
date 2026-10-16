"""Persistencia de la base de conocimiento. Solo usa la biblioteca estándar."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from .. import config

HERE = Path(__file__).resolve().parent
SEED_PATH = config.BASE_DIR / "conocimiento" / "base_conocimiento.json"
DEFAULT_DB_PATH = config.DATA_DIR / "chatbot.db"


def read_seed(path: Path) -> tuple[dict, str]:
    raw = Path(path).read_bytes()
    seed = json.loads(raw.decode("utf-8-sig"))
    sources = seed.get("fuentes", [])
    articles = seed.get("articulos", [])
    if not sources or not articles:
        raise ValueError("El archivo debe contener fuentes y artículos.")
    source_ids = {s["id"] for s in sources}
    if len(source_ids) != len(sources):
        raise ValueError("Hay identificadores de fuente repetidos.")
    ids, numbers = set(), set()
    for source in sources:
        for key in ("id", "titulo", "url", "consultada_el"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise ValueError(f"Fuente sin {key} válido.")
        if not source["url"].startswith("https://"):
            raise ValueError("Las fuentes deben tener una URL HTTPS.")
    for article in articles:
        for key in ("id", "categoria", "titulo", "contenido", "fuente_id"):
            if not isinstance(article.get(key), str) or not article[key].strip():
                raise ValueError(f"Artículo sin {key} válido.")
        if article["id"] in ids or article["fuente_id"] not in source_ids:
            raise ValueError("Artículo duplicado o fuente inexistente.")
        ids.add(article["id"])
        number = article.get("principio")
        if number is not None:
            if type(number) is not int or number not in range(1, 13) or number in numbers:
                raise ValueError("Número de principio inválido o repetido.")
            numbers.add(number)
        for key in ("preguntas", "palabras_clave"):
            if not isinstance(article.get(key, []), list) or any(
                not isinstance(value, str) or not value.strip() for value in article.get(key, [])
            ):
                raise ValueError(f"{key} debe ser una lista de textos.")
    if numbers != set(range(1, 13)):
        raise ValueError("La base debe conservar los doce principios de la declaración.")
    return seed, hashlib.sha256(raw).hexdigest()


class KnowledgeRepository:
    def __init__(self, db_path: Path | None = None, seed_path: Path | None = None):
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.seed_path = Path(seed_path or SEED_PATH)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self, force: bool = False) -> None:
        # Validar todo antes de tocar una base existente.
        seed, digest = read_seed(self.seed_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = self.connect()
        try:
            connection.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
            row = connection.execute(
                "SELECT valor FROM metadato WHERE clave = 'seed_sha256'"
            ).fetchone()
            # Una base ya importada es la fuente de respuesta hasta que se
            # solicite actualizarla explícitamente. Así una importación propia
            # no es borrada por la siguiente apertura de la aplicación.
            if row and not force:
                return
            # Un fallo en la importación revierte todas las filas.
            with connection:
                connection.execute("DELETE FROM pregunta_ejemplo")
                connection.execute("DELETE FROM articulo")
                connection.execute("DELETE FROM fuente")
                for source in seed["fuentes"]:
                    connection.execute(
                        "INSERT INTO fuente VALUES (?, ?, ?, ?, ?)",
                        tuple(source[k] for k in ("id", "titulo", "url", "consultada_el"))
                        + (source.get("nota", ""),),
                    )
                for article in seed["articulos"]:
                    connection.execute(
                        "INSERT INTO articulo VALUES (?, ?, ?, ?, ?, ?, ?)",
                        tuple(article[k] for k in ("id", "categoria", "titulo", "contenido"))
                        + (" ".join(article.get("palabras_clave", [])),
                           article["fuente_id"], article.get("principio")),
                    )
                    connection.executemany(
                        "INSERT INTO pregunta_ejemplo (articulo_id, texto) VALUES (?, ?)",
                        [(article["id"], q) for q in article.get("preguntas", [])],
                    )
                connection.execute(
                    "INSERT OR REPLACE INTO metadato VALUES ('seed_sha256', ?)", (digest,)
                )
                connection.execute(
                    "INSERT OR REPLACE INTO metadato VALUES ('version', ?)",
                    (str(seed.get("version", "1")),),
                )
        finally:
            connection.close()

    def articles(self) -> list[dict]:
        connection = self.connect()
        try:
            rows = connection.execute(
                "SELECT a.*, f.titulo AS fuente_titulo, f.url AS fuente_url, "
                "f.consultada_el FROM articulo a JOIN fuente f ON f.id = a.fuente_id "
                "ORDER BY a.id"
            ).fetchall()
            questions: dict[str, list[str]] = {}
            for row in connection.execute("SELECT articulo_id, texto FROM pregunta_ejemplo"):
                questions.setdefault(row[0], []).append(row[1])
            return [dict(row, preguntas=questions.get(row["id"], [])) for row in rows]
        finally:
            connection.close()

    def sources(self) -> list[dict]:
        connection = self.connect()
        try:
            return [dict(row) for row in connection.execute("SELECT * FROM fuente ORDER BY id")]
        finally:
            connection.close()
