import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.security import BiometricCipher  # noqa: E402
from app.vision.recognizer import (  # noqa: E402
    Recognizer,
    UserTemplate,
    train_user_template,
)


def _cluster(center: np.ndarray, n: int, spread: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return center + spread * rng.standard_normal((n, center.shape[0]))


class TestRecognizer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.dim = 1404
        rng = np.random.default_rng(0)
        # Tres "usuarios" sintéticos: nubes bien separadas en el espacio
        # de características, simulando rostros distintos ya normalizados.
        self.center_a = rng.uniform(-1, 1, self.dim)
        self.center_b = self.center_a + 6.0  # separado
        self.center_c = self.center_a - 6.0

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_train_requires_minimum_samples(self):
        with self.assertRaises(ValueError):
            train_user_template(1, _cluster(self.center_a, 4, 0.05, seed=1))

    def test_template_accepts_own_samples(self):
        train_data = _cluster(self.center_a, 40, 0.05, seed=1)
        tpl = train_user_template(user_id=1, feature_vectors=train_data)
        # una muestra nueva del MISMO usuario (misma nube, otra semilla)
        new_sample = _cluster(self.center_a, 1, 0.05, seed=2)[0]
        self.assertGreater(tpl.decision_score(new_sample), 0)

    def test_recognizer_identifies_correct_user_among_several(self):
        tpl_a = train_user_template(1, _cluster(self.center_a, 40, 0.05, seed=1))
        tpl_b = train_user_template(2, _cluster(self.center_b, 40, 0.05, seed=3))
        tpl_c = train_user_template(3, _cluster(self.center_c, 40, 0.05, seed=5))
        recognizer = Recognizer([tpl_a, tpl_b, tpl_c])

        sample_from_b = _cluster(self.center_b, 1, 0.05, seed=99)[0]
        result = recognizer.identify(sample_from_b)
        self.assertTrue(result.is_known)
        self.assertEqual(result.user_id, 2)

    def test_recognizer_rejects_unknown_face(self):
        tpl_a = train_user_template(1, _cluster(self.center_a, 40, 0.05, seed=1))
        tpl_b = train_user_template(2, _cluster(self.center_b, 40, 0.05, seed=3))
        recognizer = Recognizer([tpl_a, tpl_b])

        # un rostro "desconocido": muy lejos de ambas nubes
        unknown = self.center_a + 40.0
        result = recognizer.identify(unknown)
        self.assertFalse(result.is_known)
        self.assertIsNone(result.user_id)

    def test_recognizer_empty_returns_unknown(self):
        recognizer = Recognizer([])
        result = recognizer.identify(np.zeros(self.dim))
        self.assertFalse(result.is_known)

    def test_template_encrypted_save_load_roundtrip(self):
        cipher = BiometricCipher(key=__import__("os").urandom(32))
        tpl = train_user_template(1, _cluster(self.center_a, 30, 0.05, seed=1))
        path = self.tmpdir / "user1.bin"
        tpl.save(path, cipher)

        self.assertTrue(path.exists())
        raw = path.read_bytes()
        # no debe haber texto plano de pickle reconocible en el archivo cifrado
        self.assertNotIn(b"sklearn", raw)

        loaded = UserTemplate.load(path, cipher, user_id=1)
        self.assertEqual(loaded.user_id, 1)
        self.assertEqual(loaded.num_samples, 30)

        sample = _cluster(self.center_a, 1, 0.05, seed=7)[0]
        self.assertAlmostEqual(loaded.decision_score(sample), tpl.decision_score(sample), places=6)

    def test_wrong_user_id_fails_authenticated_decryption(self):
        """El cifrado usa el user_id como 'associated data' de AES-GCM:
        intentar descifrar la plantilla de un usuario con el id de otro
        debe fallar (protege contra mezclar/sustituir plantillas)."""
        cipher = BiometricCipher(key=__import__("os").urandom(32))
        tpl = train_user_template(1, _cluster(self.center_a, 30, 0.05, seed=1))
        path = self.tmpdir / "user1.bin"
        tpl.save(path, cipher)

        with self.assertRaises(Exception):
            UserTemplate.load(path, cipher, user_id=999)


if __name__ == "__main__":
    unittest.main()
