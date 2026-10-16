import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestSecurity(unittest.TestCase):
    def setUp(self):
        # Aislar cada test en su propio directorio de datos temporal para
        # no interferir entre corridas ni con datos reales.
        self._tmp = tempfile.mkdtemp()
        from app import config
        self._orig_data_dir = config.DATA_DIR
        config.DATA_DIR = Path(self._tmp)
        config.ensure_directories()

    def tearDown(self):
        from app import config
        config.DATA_DIR = self._orig_data_dir
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_password_hash_roundtrip(self):
        from app import security
        h = security.hash_password("clave-super-segura-123")
        self.assertTrue(security.verify_password("clave-super-segura-123", h))
        self.assertFalse(security.verify_password("otra-clave", h))

    def test_password_hash_is_not_plaintext(self):
        from app import security
        h = security.hash_password("mi-contrasena")
        self.assertNotIn("mi-contrasena", h)

    def test_aes_gcm_roundtrip(self):
        from app import security
        # Forzar recarga del módulo security para que tome el DATA_DIR temporal
        import importlib
        importlib.reload(security)
        cipher = security.BiometricCipher()
        original = b"vector-de-puntos-faciales-simulado" * 10
        blob = cipher.encrypt(original)
        self.assertNotEqual(blob, original)
        recovered = cipher.decrypt(blob)
        self.assertEqual(recovered, original)

    def test_aes_gcm_detects_tampering(self):
        from app import security
        import importlib
        importlib.reload(security)
        cipher = security.BiometricCipher()
        blob = bytearray(cipher.encrypt(b"dato original"))
        blob[-1] ^= 0xFF  # corromper un byte del ciphertext/tag
        with self.assertRaises(Exception):
            cipher.decrypt(bytes(blob))

    def test_file_encrypt_decrypt(self):
        from app import security
        import importlib
        importlib.reload(security)
        cipher = security.BiometricCipher()
        path = Path(self._tmp) / "plantilla.bin"
        cipher.encrypt_file(b"contenido-secreto", path)
        self.assertTrue(path.exists())
        self.assertNotIn(b"contenido-secreto", path.read_bytes())
        self.assertEqual(cipher.decrypt_file(path), b"contenido-secreto")


if __name__ == "__main__":
    unittest.main()
