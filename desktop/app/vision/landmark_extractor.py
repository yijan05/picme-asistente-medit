"""
Extractor de landmarks faciales sobre MediaPipe Tasks (FaceLandmarker).

Esta es la ÚNICA pieza del sistema que depende de:
  (a) el archivo de modelo `face_landmarker.task` (se descarga una vez,
      ver README / download_model.sh — no viaja con el código porque es
      un binario de varios MB que Google distribuye aparte), y
  (b) una cámara real.

Todo el resto del pipeline (features, mesh_builder, recognizer, liveness)
trabaja sobre arrays de numpy y no sabe ni le importa de dónde salieron
los landmarks — por eso en los tests se usa un extractor falso que
devuelve landmarks sintéticos, y aquí se prueba solo lo que se puede
probar sin cámara: que la clase falla con un mensaje claro si el modelo
no está descargado.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from ..config import FACE_LANDMARKER_MODEL_PATH, LANDMARK_COUNT


class LandmarkExtractorProtocol(Protocol):
    """Interfaz mínima que necesita el resto del sistema. Permite
    inyectar un extractor falso en pruebas/rutas sin tocar MediaPipe."""

    def extract(self, frame_bgr: np.ndarray) -> Optional[np.ndarray]:
        ...


class ModelNotDownloadedError(RuntimeError):
    pass


class FaceLandmarkExtractor:
    """Extractor real, respaldado por MediaPipe FaceLandmarker."""

    def __init__(self, model_path: Path | None = None, num_faces: int = 1):
        path = model_path or FACE_LANDMARKER_MODEL_PATH
        if not path.exists():
            raise ModelNotDownloadedError(
                f"No se encontró el modelo de MediaPipe en {path}.\n"
                "Este archivo no viene incluido en el repositorio (es un binario "
                "de Google de unos MB). Descárgalo una sola vez con:\n\n"
                "  python download_model.py\n\n"
                "(o 'bash download_model.sh' si prefieres bash), o manualmente desde:\n"
                "  https://storage.googleapis.com/mediapipe-models/face_landmarker/"
                "face_landmarker/float16/1/face_landmarker.task"
            )

        base_options = mp_python.BaseOptions(model_asset_path=str(path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=num_faces,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def extract(self, frame_bgr: np.ndarray) -> Optional[np.ndarray]:
        """
        frame_bgr: imagen (H, W, 3) en formato BGR (como la entrega OpenCV,
        p. ej. cv2.imread o un frame decodificado desde el navegador).

        Devuelve un array (468, 3) en coordenadas de PÍXEL (x, y según el
        tamaño de la imagen; z en la misma escala relativa que entrega
        MediaPipe), o None si no se detectó ningún rostro.
        """
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self._landmarker.detect(mp_image)
        if not result.face_landmarks:
            return None

        return _landmarks_to_array(result.face_landmarks[0], w, h)

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> "FaceLandmarkExtractor":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def _landmarks_to_array(face_landmarks, width: int, height: int) -> Optional[np.ndarray]:
    """
    Convierte la lista de landmarks que devuelve MediaPipe al array
    (468, 3) que usa el resto del sistema.

    El modelo `face_landmarker.task` siempre devuelve 478 puntos, no 468:
    los primeros 468 son la malla facial (la misma topología canónica que
    usa el resto del sistema) y los últimos 10 son puntos del iris (5 por
    ojo) que este proyecto no usa. Aislado en su propia función para
    poder probarlo con datos falsos, sin necesitar el modelo real de
    MediaPipe ni una cámara.
    """
    if len(face_landmarks) < LANDMARK_COUNT:
        return None
    face_landmarks = face_landmarks[:LANDMARK_COUNT]

    pts = np.array([[p.x * width, p.y * height, p.z * width] for p in face_landmarks], dtype=np.float64)
    if pts.shape != (LANDMARK_COUNT, 3):
        return None
    return pts
