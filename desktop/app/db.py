"""
Capa de datos de PicMe sobre SQLite.

Diseño:
  usuario(id, nombre, correo, password_hash, creado_en)
  plantilla_biometrica(
      usuario_id,
      ruta_svm,
      ruta_mesh_obj,
      num_muestras,
      actualizado_en
  )
  ingreso(id, usuario_id NULL, resultado, score, creado_en)

Las plantillas biométricas y los modelos 3D se almacenan cifrados en
archivos externos. SQLite únicamente conserva las rutas.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Iterator, Optional

from . import config


SCHEMA = """
CREATE TABLE IF NOT EXISTS usuario (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    correo          TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    creado_en       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plantilla_biometrica (
    usuario_id      INTEGER PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
    ruta_svm        TEXT NOT NULL,
    ruta_mesh_obj   TEXT,
    num_muestras    INTEGER NOT NULL DEFAULT 0,
    actualizado_en  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingreso (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    resultado       TEXT NOT NULL,
    score           REAL,
    creado_en       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ingreso_usuario
ON ingreso(usuario_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def portable_data_path(path: Path) -> str:
    """Guarda rutas relativas al proyecto para poder moverlo a otro PC."""
    try:
        return path.resolve().relative_to(config.BASE_DIR.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_data_path(value: str) -> Path:
    """Resuelve rutas nuevas y antiguas sin depender de la carpeta del terminal."""
    path = Path(value)
    if path.is_absolute() and path.exists():
        return path
    parts = PureWindowsPath(value).parts if "\\" in value else path.parts
    # Las bases antiguas incluían C:\\Users\\...\\data\\plantillas\\archivo.bin.
    for index in range(len(parts) - 1, -1, -1):
        if parts[index].casefold() == "data":
            candidate = config.DATA_DIR.joinpath(*parts[index + 1:])
            if candidate.exists():
                return candidate
    if not path.is_absolute() and not PureWindowsPath(value).is_absolute():
        return config.BASE_DIR / path
    return path


@contextmanager
def get_connection(
    db_path: Optional[Path] = None,
) -> Iterator[sqlite3.Connection]:
    path = db_path or config.DB_PATH

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(path)

    conn.execute("PRAGMA foreign_keys = ON;")

    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(
    db_path: Optional[Path] = None,
) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


@dataclass
class Usuario:
    id: int
    nombre: str
    correo: str
    password_hash: str
    creado_en: str


# ------------------------------------------------------------------
# Usuarios
# ------------------------------------------------------------------
def crear_usuario(
    nombre: str,
    correo: str,
    password_hash: str,
    *,
    db_path: Optional[Path] = None,
) -> int:
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO usuario
                (nombre, correo, password_hash, creado_en)
            VALUES (?, ?, ?, ?)
            """,
            (
                nombre,
                correo,
                password_hash,
                _now(),
            ),
        )

        return cur.lastrowid


def eliminar_usuario(
    usuario_id: int,
    *,
    db_path: Optional[Path] = None,
) -> None:
    """
    Elimina un usuario.

    La FK ON DELETE CASCADE elimina su plantilla biométrica asociada.
    Los registros de ingreso conservan la auditoría y pasan a
    usuario_id NULL mediante ON DELETE SET NULL.
    """
    with get_connection(db_path) as conn:
        conn.execute(
            "DELETE FROM usuario WHERE id = ?",
            (usuario_id,),
        )


def obtener_usuario_por_correo(
    correo: str,
    *,
    db_path: Optional[Path] = None,
) -> Optional[Usuario]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM usuario WHERE correo = ?",
            (correo,),
        ).fetchone()

        return Usuario(**dict(row)) if row else None


def obtener_usuario_por_id(
    usuario_id: int,
    *,
    db_path: Optional[Path] = None,
) -> Optional[Usuario]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM usuario WHERE id = ?",
            (usuario_id,),
        ).fetchone()

        return Usuario(**dict(row)) if row else None


def listar_usuarios(
    *,
    db_path: Optional[Path] = None,
) -> list[Usuario]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM usuario ORDER BY id"
        ).fetchall()

        return [
            Usuario(**dict(row))
            for row in rows
        ]


def correo_existe(
    correo: str,
    *,
    db_path: Optional[Path] = None,
) -> bool:
    return (
        obtener_usuario_por_correo(
            correo,
            db_path=db_path,
        )
        is not None
    )


# ------------------------------------------------------------------
# Plantillas biométricas
# ------------------------------------------------------------------
def guardar_plantilla(
    usuario_id: int,
    ruta_svm: str,
    ruta_mesh_obj: Optional[str],
    num_muestras: int,
    *,
    db_path: Optional[Path] = None,
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO plantilla_biometrica
                (
                    usuario_id,
                    ruta_svm,
                    ruta_mesh_obj,
                    num_muestras,
                    actualizado_en
                )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(usuario_id) DO UPDATE SET
                ruta_svm = excluded.ruta_svm,
                ruta_mesh_obj = excluded.ruta_mesh_obj,
                num_muestras = excluded.num_muestras,
                actualizado_en = excluded.actualizado_en
            """,
            (
                usuario_id,
                ruta_svm,
                ruta_mesh_obj,
                num_muestras,
                _now(),
            ),
        )


def obtener_plantillas_activas(
    *,
    db_path: Optional[Path] = None,
) -> list[sqlite3.Row]:
    with get_connection(db_path) as conn:
        return conn.execute(
            """
            SELECT
                u.id AS usuario_id,
                u.nombre,
                p.ruta_svm,
                p.ruta_mesh_obj,
                p.num_muestras
            FROM plantilla_biometrica p
            JOIN usuario u
                ON u.id = p.usuario_id
            """
        ).fetchall()


# ------------------------------------------------------------------
# Registro de accesos
# ------------------------------------------------------------------
def registrar_ingreso(
    usuario_id: Optional[int],
    resultado: str,
    score: Optional[float],
    *,
    db_path: Optional[Path] = None,
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO ingreso
                (usuario_id, resultado, score, creado_en)
            VALUES (?, ?, ?, ?)
            """,
            (
                usuario_id,
                resultado,
                score,
                _now(),
            ),
        )


def historial_ingresos(
    usuario_id: Optional[int] = None,
    limit: int = 50,
    *,
    db_path: Optional[Path] = None,
):
    with get_connection(db_path) as conn:
        if usuario_id is not None:
            rows = conn.execute(
                """
                SELECT *
                FROM ingreso
                WHERE usuario_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    usuario_id,
                    limit,
                ),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM ingreso
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]
