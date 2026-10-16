"""
Vector de características biométrico a partir de los 468 puntos 3D.

El PGC original guarda directamente las 468*3 = 1404 coordenadas crudas.
Aquí se añade un paso de normalización que el documento original no
tenía y que es importante para que el clasificador generalice bien:

  1. Centrado: se resta la posición de un punto de referencia estable
     (el puente de la nariz, índice 168 en la malla canónica) para que
     el vector no dependa de en qué parte del cuadro esté la cara.
  2. Escalado: se divide por la distancia interocular (distancia entre
     las esquinas externas de los ojos, índices 33 y 263), para que el
     vector no dependa de qué tan cerca esté la persona de la cámara ni
     de la resolución del frame.

Sin este paso, el mismo rostro capturado a distinta distancia de la
cámara produce vectores muy distintos en magnitud, lo que puede
degradar la frontera de decisión del One-Class SVM (esto es una causa
plausible del tipo de asimetría de precisión entre usuarios que se
observó en las pruebas del PGC).
"""
from __future__ import annotations

import numpy as np

from ..config import FEATURE_DIM, LANDMARK_COUNT

NOSE_BRIDGE_IDX = 168
LEFT_EYE_OUTER_IDX = 263
RIGHT_EYE_OUTER_IDX = 33


class InvalidLandmarksError(ValueError):
    pass


def normalize_landmarks(landmarks: np.ndarray) -> np.ndarray:
    """
    landmarks: array (468, 3) en coordenadas de imagen (x, y en píxeles o
    normalizado 0-1, z relativo, tal como los entrega MediaPipe).

    Devuelve un array (468, 3) centrado y escalado, listo para aplanarse
    en el vector de características.
    """
    if landmarks.shape != (LANDMARK_COUNT, 3):
        raise InvalidLandmarksError(
            f"Se esperaban landmarks de forma ({LANDMARK_COUNT}, 3), se recibió {landmarks.shape}"
        )

    center = landmarks[NOSE_BRIDGE_IDX]
    centered = landmarks - center

    interocular = np.linalg.norm(landmarks[LEFT_EYE_OUTER_IDX] - landmarks[RIGHT_EYE_OUTER_IDX])
    if interocular < 1e-8:
        raise InvalidLandmarksError(
            "Distancia interocular ~0: los landmarks parecen degenerados o el rostro no fue detectado correctamente"
        )

    return centered / interocular


def landmarks_to_feature_vector(landmarks: np.ndarray) -> np.ndarray:
    """Aplana los landmarks normalizados a un vector 1D de 1404 dimensiones."""
    normalized = normalize_landmarks(landmarks)
    vector = normalized.flatten()
    assert vector.shape == (FEATURE_DIM,)
    return vector
