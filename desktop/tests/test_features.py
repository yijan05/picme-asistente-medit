import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.vision.features import (  # noqa: E402
    InvalidLandmarksError,
    landmarks_to_feature_vector,
    normalize_landmarks,
)
from app.config import FEATURE_DIM, LANDMARK_COUNT  # noqa: E402


def _synthetic_face(seed: int = 0, scale: float = 1.0, offset=(0.0, 0.0, 0.0)) -> np.ndarray:
    """Genera una nube de puntos determinista con forma de 'rostro' burda
    (una elipsoide con algo de variación), suficiente para probar las
    propiedades matemáticas de la normalización sin necesitar una cámara
    ni el modelo real de MediaPipe."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, LANDMARK_COUNT)
    x = 0.5 * np.cos(t) + 0.02 * rng.standard_normal(LANDMARK_COUNT)
    y = 0.7 * np.sin(t) + 0.02 * rng.standard_normal(LANDMARK_COUNT)
    z = 0.1 * np.sin(2 * t) + 0.01 * rng.standard_normal(LANDMARK_COUNT)
    pts = np.stack([x, y, z], axis=1)
    return pts * scale + np.array(offset)


class TestFeatures(unittest.TestCase):
    def test_output_shape(self):
        lm = _synthetic_face()
        vec = landmarks_to_feature_vector(lm)
        self.assertEqual(vec.shape, (FEATURE_DIM,))

    def test_rejects_wrong_shape(self):
        with self.assertRaises(InvalidLandmarksError):
            normalize_landmarks(np.zeros((10, 3)))

    def test_rejects_degenerate_points(self):
        # todos los puntos iguales -> distancia interocular 0
        lm = np.ones((LANDMARK_COUNT, 3))
        with self.assertRaises(InvalidLandmarksError):
            normalize_landmarks(lm)

    def test_translation_invariance(self):
        """El mismo rostro desplazado en el cuadro debe dar el mismo vector
        normalizado (invarianza a dónde está posicionada la cara)."""
        base = _synthetic_face(seed=1)
        shifted = _synthetic_face(seed=1, offset=(50.0, -30.0, 2.0))
        v1 = landmarks_to_feature_vector(base)
        v2 = landmarks_to_feature_vector(shifted)
        np.testing.assert_allclose(v1, v2, atol=1e-8)

    def test_scale_invariance(self):
        """El mismo rostro capturado 'más cerca' (todas las coordenadas
        escaladas) debe producir el mismo vector normalizado (invarianza
        a la distancia a la cámara)."""
        base = _synthetic_face(seed=2)
        closer = _synthetic_face(seed=2, scale=3.0)
        v1 = landmarks_to_feature_vector(base)
        v2 = landmarks_to_feature_vector(closer)
        np.testing.assert_allclose(v1, v2, atol=1e-6)

    def test_different_faces_give_different_vectors(self):
        v1 = landmarks_to_feature_vector(_synthetic_face(seed=10))
        v2 = landmarks_to_feature_vector(_synthetic_face(seed=99))
        self.assertGreater(np.linalg.norm(v1 - v2), 0.01)


if __name__ == "__main__":
    unittest.main()
