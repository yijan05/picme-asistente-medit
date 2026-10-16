"""
Estimación aproximada de la orientación de la cabeza.

Calcula el yaw (giro horizontal de la cabeza) a partir de landmarks
faciales mediante solvePnP.

El resultado se expresa en grados:

    yaw ~= 0°     -> rostro frontal
    yaw > 0°      -> giro hacia un lado
    yaw < 0°      -> giro hacia el otro lado

La estimación está pensada para validar los ángulos de captura del
registro, no para realizar una medición médica o metrológica precisa.
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


# Landmarks MediaPipe utilizados para estimar la pose.
#
# 1   = punta de la nariz
# 152 = barbilla
# 263 = esquina externa del ojo
# 33  = esquina externa del otro ojo
# 291 = esquina de la boca
# 61  = esquina de la boca
POSE_LANDMARK_INDICES = (
    1,
    152,
    263,
    33,
    291,
    61,
)


# Modelo 3D aproximado de una cara humana.
#
# No pretende reconstruir la cara del usuario.
# Solo proporciona una geometría de referencia para solvePnP.
MODEL_POINTS = np.array(
    [
        (0.0, 0.0, 0.0),          # nariz
        (0.0, -330.0, -65.0),     # barbilla
        (-225.0, 170.0, -135.0),  # ojo
        (225.0, 170.0, -135.0),   # ojo
        (-150.0, -150.0, -125.0), # boca
        (150.0, -150.0, -125.0),  # boca
    ],
    dtype=np.float64,
)


class HeadPoseError(ValueError):
    """Error al estimar la orientación de la cabeza."""


def estimate_yaw_degrees(
    landmarks: np.ndarray,
    frame_width: int,
    frame_height: int,
) -> Optional[float]:
    """
    Estima el yaw de la cabeza en grados.

    Parámetros
    ----------
    landmarks:
        Array de forma (468, 3) con los landmarks de MediaPipe.

    frame_width:
        Ancho real del frame de cámara.

    frame_height:
        Alto real del frame de cámara.

    Devuelve
    --------
    float | None
        Ángulo yaw aproximado.

        None significa que solvePnP no pudo encontrar una solución
        suficientemente estable.
    """
    if landmarks is None:
        return None

    if landmarks.shape != (468, 3):
        raise HeadPoseError(
            f"Se esperaban landmarks de forma (468, 3), "
            f"se recibió {landmarks.shape}"
        )

    if frame_width <= 0 or frame_height <= 0:
        raise HeadPoseError(
            "El tamaño del frame debe ser positivo."
        )

    image_points = landmarks[
        list(POSE_LANDMARK_INDICES),
        :2,
    ].astype(np.float64)

    # Matriz intrínseca aproximada de la cámara.
    #
    # No conocemos las características exactas de cada webcam,
    # por lo que usamos una aproximación razonable para una cámara
    # sin calibración previa.
    focal_length = float(frame_width)

    camera_matrix = np.array(
        [
            [focal_length, 0.0, frame_width / 2.0],
            [0.0, focal_length, frame_height / 2.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )

    distortion_coeffs = np.zeros(
        (4, 1),
        dtype=np.float64,
    )

    success, rotation_vector, translation_vector = cv2.solvePnP(
        MODEL_POINTS,
        image_points,
        camera_matrix,
        distortion_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )

    if not success:
        return None

    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

    yaw = _extract_yaw_from_rotation_matrix(rotation_matrix)

    if not np.isfinite(yaw):
        return None

    return float(yaw)


def _extract_yaw_from_rotation_matrix(
    rotation_matrix: np.ndarray,
) -> float:
    """
    Extrae el yaw de una matriz de rotación.

    Utilizamos una descomposición explícita para evitar depender de
    convenciones ambiguas de Euler de distintas funciones.
    """
    sy = np.sqrt(
        rotation_matrix[0, 0] ** 2
        + rotation_matrix[1, 0] ** 2
    )

    singular = sy < 1e-6

    if not singular:
        x_angle = np.arctan2(
            rotation_matrix[2, 1],
            rotation_matrix[2, 2],
        )
        y_angle = np.arctan2(
            -rotation_matrix[2, 0],
            sy,
        )
        z_angle = np.arctan2(
            rotation_matrix[1, 0],
            rotation_matrix[0, 0],
        )
    else:
        x_angle = np.arctan2(
            -rotation_matrix[1, 2],
            rotation_matrix[1, 1],
        )
        y_angle = np.arctan2(
            -rotation_matrix[2, 0],
            sy,
        )
        z_angle = 0.0

    # x_angle y z_angle no son necesarios para la validación,
    # pero mantener el cálculo completo hace explícita la
    # convención utilizada.
    _ = x_angle
    _ = z_angle

    return float(np.degrees(y_angle))


def yaw_is_in_range(
    yaw: Optional[float],
    yaw_range: tuple[float, float],
    tolerance: float = 5.0,
) -> bool:
    """
    Indica si un yaw está dentro del rango solicitado.

    La tolerancia permite pequeñas variaciones naturales del usuario
    y errores normales de estimación.

    Ejemplo:

        rango = (15, 45)
        tolerancia = 5

    acepta aproximadamente:

        10° ... 50°
    """
    if yaw is None:
        return False

    minimum, maximum = yaw_range

    return (
        minimum - tolerance
        <= yaw
        <= maximum + tolerance
    )

