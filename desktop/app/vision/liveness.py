"""
Detección de vida (liveness) por parpadeo, usando el Eye Aspect Ratio (EAR).

Misma fórmula y el mismo propósito descritos en la documentación del
proyecto: evitar que una fotografía estática o una pantalla mostrando un
rostro puedan pasar por una persona real, exigiendo al menos un parpadeo
detectado durante la sesión de reconocimiento.

    EAR = (||P2-P6|| + ||P3-P5||) / (2 * ||P1-P4||)

Un EAR bajo y sostenido durante pocos frames indica ojo cerrado; un
parpadeo real es una caída breve seguida de una recuperación, no una
oclusión sostenida (que es más típica de un ojo cerrado de forma forzada
o de un fallo de detección).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import EAR_BLINK_THRESHOLD, EAR_CONSEC_FRAMES
from .face_topology import LEFT_EYE_EAR, RIGHT_EYE_EAR


def _eye_aspect_ratio(points: np.ndarray) -> float:
    """points: array (6, 2 o 3) en el orden P1..P6 de un mismo ojo."""
    p1, p2, p3, p4, p5, p6 = points[:, :2]  # solo x,y para el cálculo geométrico
    vertical = np.linalg.norm(p2 - p6) + np.linalg.norm(p3 - p5)
    horizontal = 2.0 * np.linalg.norm(p1 - p4)
    if horizontal == 0:
        return 0.0
    return float(vertical / horizontal)


def compute_ear(landmarks: np.ndarray) -> float:
    """
    landmarks: array (468, 3) con todos los puntos del frame actual.
    Devuelve el EAR promedio de ambos ojos.
    """
    right = landmarks[list(RIGHT_EYE_EAR)]
    left = landmarks[list(LEFT_EYE_EAR)]
    return (_eye_aspect_ratio(right) + _eye_aspect_ratio(left)) / 2.0


@dataclass
class BlinkDetector:
    """
    Máquina de estados simple para contar parpadeos a lo largo de una
    secuencia de frames.

    Se alimenta frame a frame con `update(landmarks)`. Un parpadeo se
    cuenta cuando el EAR cae por debajo del umbral durante al menos
    `consec_frames` seguidos y luego se recupera por encima del umbral
    (evita contar como parpadeo una oclusión sostenida, p. ej. alguien
    con los ojos cerrados de forma prolongada).
    """

    threshold: float = EAR_BLINK_THRESHOLD
    consec_frames: int = EAR_CONSEC_FRAMES

    _frames_below: int = field(default=0, init=False)
    _blink_count: int = field(default=0, init=False)
    _last_ear: float | None = field(default=None, init=False)

    @property
    def blink_count(self) -> int:
        return self._blink_count

    @property
    def last_ear(self) -> float | None:
        return self._last_ear

    def reset(self) -> None:
        self._frames_below = 0
        self._blink_count = 0
        self._last_ear = None

    def update(self, landmarks: np.ndarray) -> float:
        """Procesa un frame nuevo y devuelve el EAR calculado."""
        ear = compute_ear(landmarks)
        self._last_ear = ear

        if ear < self.threshold:
            self._frames_below += 1
        else:
            if self._frames_below >= self.consec_frames:
                self._blink_count += 1
            self._frames_below = 0

        return ear
