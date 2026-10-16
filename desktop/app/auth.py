"""
Sesión del usuario dentro del programa de escritorio.

A diferencia de una aplicación web (donde cada request es independiente
y necesita una cookie para saber "quién eres"), acá todo corre en un
solo proceso: basta con guardar el usuario que inició sesión en una
variable del módulo mientras el programa esté abierto.
"""
from __future__ import annotations

from typing import Optional

from . import db

_current_user: Optional[db.Usuario] = None


def login_user(usuario_id: int) -> db.Usuario:
    global _current_user
    usuario = db.obtener_usuario_por_id(usuario_id)
    if usuario is None:
        raise ValueError(f"Usuario {usuario_id} no existe")
    _current_user = usuario
    return usuario


def logout_user() -> None:
    global _current_user
    _current_user = None


def current_user() -> Optional[db.Usuario]:
    return _current_user
