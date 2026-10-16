import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.vision.landmark_extractor import (  # noqa: E402
    FaceLandmarkExtractor,
    ModelNotDownloadedError,
    _landmarks_to_array,
)


class _FakeLandmark:

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z


class TestLandmarksToArray(unittest.TestCase):
    """
    Regresión de un bug real: el modelo face_landmarker.task siempre
    devuelve 478 puntos (468 de malla facial + 10 de iris al final), no
    468. Sin recortar esos 10 puntos extra, toda comparación de forma
    exacta más adelante en el pipeline rechazaba CADA detección — la
    cámara abría pero nunca "detectaba" nada. Estos tests fijan el
    comportamiento correcto para que no se repita.
    """

    def test_478_landmarks_truncates_to_first_468(self):
        # 468 puntos "de malla" con valores identificables (índice como x),
        # más 10 puntos de iris al final con valores muy distintos, para
        # confirmar que efectivamente se descartan los últimos 10 y no,
        # por ejemplo, los primeros 10.
        malla = [_FakeLandmark(x=i / 1000.0, y=0.5, z=0.0) for i in range(468)]
        iris = [_FakeLandmark(x=999.0, y=999.0, z=999.0) for _ in range(10)]
        landmarks_478 = malla + iris

        result = _landmarks_to_array(landmarks_478, width=1000, height=1000)

        self.assertIsNotNone(result)
        self.assertEqual(result.shape, (468, 3))
        # el punto 0 debe seguir siendo el de la malla (x=0/1000 * 1000 = 0)
        self.assertAlmostEqual(result[0, 0], 0.0)
        # el punto 467 (último de la malla) debe ser 467, NO 999 (iris)
        self.assertAlmostEqual(result[467, 0], 467.0)

    def test_exactly_468_landmarks_still_works(self):
        """Por si en el futuro se usa una variante del modelo sin iris."""
        malla = [_FakeLandmark(x=i / 1000.0, y=0.5, z=0.0) for i in range(468)]
        result = _landmarks_to_array(malla, width=1000, height=1000)
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, (468, 3))

    def test_fewer_than_468_returns_none(self):
        pocos = [_FakeLandmark(x=0.1, y=0.1, z=0.0) for _ in range(100)]
        result = _landmarks_to_array(pocos, width=640, height=480)
        self.assertIsNone(result)

    def test_scaling_by_width_and_height(self):
        malla = [_FakeLandmark(x=0.5, y=0.25, z=-0.1) for _ in range(468)]
        result = _landmarks_to_array(malla, width=640, height=480)
        self.assertAlmostEqual(result[0, 0], 0.5 * 640)
        self.assertAlmostEqual(result[0, 1], 0.25 * 480)
        self.assertAlmostEqual(result[0, 2], -0.1 * 640)  # z se escala como x, según MediaPipe


class TestLandmarkExtractor(unittest.TestCase):
    def test_raises_clear_error_when_model_missing(self):
        fake_path = Path("/tmp/no_deberia_existir_este_modelo_picme.task")
        if fake_path.exists():
            fake_path.unlink()
        with self.assertRaises(ModelNotDownloadedError) as ctx:
            FaceLandmarkExtractor(model_path=fake_path)
        # el mensaje debe orientar a la persona sobre cómo resolverlo
        self.assertIn("download_model", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
