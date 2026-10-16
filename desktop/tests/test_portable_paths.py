from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import config, db


class PortablePathsTest(unittest.TestCase):
    def test_ruta_windows_de_otro_equipo_se_resuelve(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            model = root / "data" / "plantillas" / "usuario_1.bin"
            model.parent.mkdir(parents=True)
            model.write_bytes(b"test")
            with patch.object(config, "BASE_DIR", root), patch.object(config, "DATA_DIR", root / "data"):
                self.assertEqual(db.resolve_data_path(r"C:\Users\otro\picme_desktop\data\plantillas\usuario_1.bin"), model)
                self.assertEqual(db.portable_data_path(model), "data/plantillas/usuario_1.bin")

    def test_ruta_relativa_no_depende_del_terminal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(config, "BASE_DIR", root):
                self.assertEqual(db.resolve_data_path("data/plantillas/nuevo.bin"), root / "data/plantillas/nuevo.bin")
