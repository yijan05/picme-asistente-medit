"""
Descarga del modelo de MediaPipe FaceLandmarker.

Separado de la interfaz a propósito: así lo puede usar tanto
`download_model.py` (para quien prefiera la terminal) como un botón
dentro de la propia ventana (`SetupRequiredView`), y así se puede probar
la lógica de descarga con una respuesta HTTP simulada, sin necesitar
conexión real a internet.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Callable, Optional

from . import config

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)

ProgressCallback = Callable[[int, int], None]  # (bytes_descargados, bytes_totales)


class ModelDownloadError(RuntimeError):
    pass


def is_model_downloaded(model_path: Optional[Path] = None) -> bool:
    path = model_path or config.FACE_LANDMARKER_MODEL_PATH
    return path.exists() and path.stat().st_size > 0


def download_model(
    model_path: Optional[Path] = None,
    url: str = MODEL_URL,
    progress_callback: Optional[ProgressCallback] = None,
    chunk_size: int = 65536,
    opener: Optional[Callable] = None,
) -> Path:
    """
    Descarga el modelo a `model_path` (por defecto, la ruta de
    config.FACE_LANDMARKER_MODEL_PATH). Si ya existe, no hace nada.

    `opener` es inyectable para pruebas: por defecto es
    `urllib.request.urlopen`, pero un test puede pasar una función falsa
    que simule una respuesta HTTP sin tocar la red real.
    """
    path = model_path or config.FACE_LANDMARKER_MODEL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    if is_model_downloaded(path):
        if progress_callback:
            progress_callback(1, 1)
        return path

    open_url = opener or urllib.request.urlopen
    tmp_path = path.with_suffix(path.suffix + ".part")

    try:
        with open_url(url, timeout=30) as response:
            total = int(response.headers.get("Content-Length", 0) or 0)
            downloaded = 0
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)
        tmp_path.replace(path)
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise ModelDownloadError(f"No se pudo descargar el modelo: {exc}") from exc

    return path
