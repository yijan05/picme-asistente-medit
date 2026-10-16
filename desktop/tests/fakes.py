"""
Infraestructura de prueba compartida: permite simular el pipeline
completo (registro + login) sin cámara real ni el modelo `.task` de
MediaPipe, inyectando un extractor falso que devuelve nubes de puntos
sintéticas pero "consistentes por identidad" (para que el SVM de cada
usuario realmente pueda aprender a distinguirlos) y con el estado de
parpadeo controlado explícitamente por el test.
"""
from __future__ import annotations

import numpy as np

from app.vision.face_topology import LEFT_EYE_EAR, NUM_LANDMARKS, RIGHT_EYE_EAR
from app.vision.features import NOSE_BRIDGE_IDX

_EYE_OPEN_OFFSETS = np.array(
    [[0, 0, 0], [1, 1, 0], [2, 1, 0], [3, 0, 0], [2, -1, 0], [1, -1, 0]], dtype=np.float64
)
_EYE_CLOSED_OFFSETS = np.array(
    [[0, 0, 0], [1, 0.05, 0], [2, 0.05, 0], [3, 0, 0], [2, -0.05, 0], [1, -0.05, 0]], dtype=np.float64
)


def synthetic_landmarks(identity_seed: int, frame_seed: int, eye_state: str = "open") -> np.ndarray:
    """
    Genera una nube de 468 puntos "propia" de una identidad sintética
    (determinada por identity_seed), con pequeño ruido por frame
    (simulando la variación natural entre capturas de la MISMA persona),
    y con la geometría de los ojos controlada explícitamente para poder
    simular parpadeos a demanda.
    """
    identity_rng = np.random.default_rng(identity_seed)
    center = identity_rng.uniform(-3.0, 3.0, size=(NUM_LANDMARKS, 3))

    frame_rng = np.random.default_rng(identity_seed * 100_000 + frame_seed)
    pts = center + 0.05 * frame_rng.standard_normal((NUM_LANDMARKS, 3))

    # Punto de referencia estable para el centrado en features.py
    pts[NOSE_BRIDGE_IDX] = np.array([0.0, 0.0, 0.0])

    offsets = _EYE_OPEN_OFFSETS if eye_state == "open" else _EYE_CLOSED_OFFSETS
    right_eye_base = np.array([-5.0, 0.0, 0.0])
    left_eye_base = np.array([5.0, 0.0, 0.0])
    for i, idx in enumerate(RIGHT_EYE_EAR):
        pts[idx] = right_eye_base + offsets[i]
    for i, idx in enumerate(LEFT_EYE_EAR):
        pts[idx] = left_eye_base + offsets[i]

    return pts


class FakeLandmarkExtractor:
    """
    Extractor inyectable: en vez de leer la imagen, consulta una cola de
    "próximos landmarks a devolver" que el test controla directamente.
    Si la cola está vacía, repite el último valor entregado (o None).
    """

    def __init__(self):
        self._queue: list[np.ndarray | None] = []
        self._last: np.ndarray | None = None

    def queue(self, landmarks: np.ndarray | None) -> None:
        self._queue.append(landmarks)

    def queue_many(self, landmarks_list: list[np.ndarray | None]) -> None:
        self._queue.extend(landmarks_list)

    def extract(self, frame_bgr: np.ndarray) -> np.ndarray | None:
        if self._queue:
            self._last = self._queue.pop(0)
        return self._last
