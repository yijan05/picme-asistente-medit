import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import model_downloader  # noqa: E402


class _FakeResponse:


    def __init__(self, data: bytes, content_length: int | None = None, fail_after_bytes: int | None = None):
        self._data = data
        self._pos = 0
        self._fail_after_bytes = fail_after_bytes
        self._read_so_far = 0
        self.headers = {"Content-Length": str(content_length if content_length is not None else len(data))}

    def read(self, n: int) -> bytes:
        if self._fail_after_bytes is not None and self._read_so_far >= self._fail_after_bytes:
            raise ConnectionError("conexión interrumpida (simulada)")
        chunk = self._data[self._pos : self._pos + n]
        self._pos += len(chunk)
        self._read_so_far += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _fake_opener(fake_response):
    def opener(url, timeout=30):
        return fake_response

    return opener


class TestModelDownloader(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.model_path = self.tmpdir / "modelo_falso.task"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_is_model_downloaded_false_when_missing(self):
        self.assertFalse(model_downloader.is_model_downloaded(self.model_path))

    def test_is_model_downloaded_false_when_empty_file(self):
        self.model_path.write_bytes(b"")
        self.assertFalse(model_downloader.is_model_downloaded(self.model_path))

    def test_is_model_downloaded_true_when_present(self):
        self.model_path.write_bytes(b"contenido")
        self.assertTrue(model_downloader.is_model_downloaded(self.model_path))

    def test_download_writes_full_content(self):
        contenido = b"x" * 500_000
        fake_response = _FakeResponse(contenido)

        result_path = model_downloader.download_model(
            model_path=self.model_path, opener=_fake_opener(fake_response)
        )
        self.assertEqual(result_path, self.model_path)
        self.assertTrue(self.model_path.exists())
        self.assertEqual(self.model_path.read_bytes(), contenido)

    def test_download_reports_progress(self):
        contenido = b"y" * 300_000
        fake_response = _FakeResponse(contenido)
        eventos = []

        model_downloader.download_model(
            model_path=self.model_path,
            opener=_fake_opener(fake_response),
            progress_callback=lambda d, t: eventos.append((d, t)),
        )

        self.assertGreater(len(eventos), 1)  # varios chunks reportados
        self.assertEqual(eventos[-1][0], len(contenido))  # el último = todo descargado
        self.assertTrue(all(total == len(contenido) for _, total in eventos))
        # el progreso debe ser monótonamente creciente
        descargados = [d for d, _ in eventos]
        self.assertEqual(descargados, sorted(descargados))

    def test_download_skips_if_already_present(self):
        self.model_path.write_bytes(b"ya-estaba-aqui")
        eventos = []

        def opener_que_no_deberia_llamarse(url, timeout=30):
            raise AssertionError("no debería intentar descargar si el archivo ya existe")

        model_downloader.download_model(
            model_path=self.model_path,
            opener=opener_que_no_deberia_llamarse,
            progress_callback=lambda d, t: eventos.append((d, t)),
        )
        self.assertEqual(self.model_path.read_bytes(), b"ya-estaba-aqui")
        self.assertEqual(eventos, [(1, 1)])

    def test_download_failure_raises_clean_error_and_cleans_tmp_file(self):
        contenido = b"z" * 200_000
        fake_response = _FakeResponse(contenido, fail_after_bytes=50_000)

        with self.assertRaises(model_downloader.ModelDownloadError):
            model_downloader.download_model(model_path=self.model_path, opener=_fake_opener(fake_response))

        self.assertFalse(self.model_path.exists())
        tmp_path = self.model_path.with_suffix(self.model_path.suffix + ".part")
        self.assertFalse(tmp_path.exists())  # el archivo parcial se limpia, no queda basura

    def test_download_uses_default_config_path_when_none_given(self):
        from app import config

        original = config.FACE_LANDMARKER_MODEL_PATH
        try:
            config.FACE_LANDMARKER_MODEL_PATH = self.model_path
            fake_response = _FakeResponse(b"contenido-por-defecto")
            result_path = model_downloader.download_model(opener=_fake_opener(fake_response))
            self.assertEqual(result_path, self.model_path)
        finally:
            config.FACE_LANDMARKER_MODEL_PATH = original


if __name__ == "__main__":
    unittest.main()
