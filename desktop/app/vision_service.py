"""
Punto único de acceso a los objetos "pesados" del pipeline de visión:

  - El extractor de landmarks (carga el modelo de MediaPipe una sola vez;
    crearlo en cada frame sería lentísimo y recargaría el modelo cada vez).
  - El reconocedor (carga y descifra todas las plantillas de usuario;
    se cachea y se invalida solo cuando cambia el conjunto de usuarios
    registrados, no en cada frame de login).

`set_extractor_override` existe para poder probar los controladores de
registro/login sin depender de una cámara real ni del modelo descargado
de MediaPipe: se inyecta un extractor falso que cumple el mismo
protocolo (`extract(frame_bgr) -> Optional[np.ndarray]`).
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from . import config, db
from .security import BiometricCipher
from .vision.landmark_extractor import FaceLandmarkExtractor, LandmarkExtractorProtocol
from .vision.recognizer import Recognizer, UserTemplate

_lock = threading.Lock()
_extractor: Optional[LandmarkExtractorProtocol] = None
_extractor_override: Optional[LandmarkExtractorProtocol] = None
_recognizer_cache: Optional[Recognizer] = None


def set_extractor_override(extractor: Optional[LandmarkExtractorProtocol]) -> None:
    """Solo para tests: fuerza qué extractor devuelve get_extractor()."""
    global _extractor_override
    _extractor_override = extractor


def get_extractor() -> LandmarkExtractorProtocol:
    global _extractor
    if _extractor_override is not None:
        return _extractor_override
    with _lock:
        if _extractor is None:
            _extractor = FaceLandmarkExtractor()
        return _extractor


def close_extractor() -> None:
    """Libera el modelo de MediaPipe (llamar al cerrar la aplicación)."""
    global _extractor
    with _lock:
        if _extractor is not None:
            _extractor.close()
            _extractor = None


def invalidate_recognizer_cache() -> None:
    global _recognizer_cache
    with _lock:
        _recognizer_cache = None


def get_recognizer() -> Recognizer:
    global _recognizer_cache
    with _lock:
        if _recognizer_cache is None:
            _recognizer_cache = _load_recognizer_from_disk()
        return _recognizer_cache


def _load_recognizer_from_disk() -> Recognizer:
    cipher = BiometricCipher()
    rows = db.obtener_plantillas_activas()
    templates: list[UserTemplate] = []
    for row in rows:
        path = db.resolve_data_path(row["ruta_svm"])
        try:
            templates.append(UserTemplate.load(path, cipher, row["usuario_id"]))
        except Exception:
            # Una plantilla corrupta o ilegible no debe tumbar el login de
            # TODOS los usuarios; se omite (se podría loguear el error).
            continue
    return Recognizer(templates)
