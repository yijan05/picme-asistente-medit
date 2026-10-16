import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402


class TestDb(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test.db"
        db.init_db(self.db_path)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_crear_y_obtener_usuario(self):
        uid = db.crear_usuario("Evelin Virguez", "evelin@example.com", "hash123", db_path=self.db_path)
        self.assertIsInstance(uid, int)

        u = db.obtener_usuario_por_correo("evelin@example.com", db_path=self.db_path)
        self.assertIsNotNone(u)
        self.assertEqual(u.nombre, "Evelin Virguez")

        u2 = db.obtener_usuario_por_id(uid, db_path=self.db_path)
        self.assertEqual(u2.correo, "evelin@example.com")

    def test_correo_unico(self):
        db.crear_usuario("A", "dup@example.com", "h", db_path=self.db_path)
        with self.assertRaises(Exception):
            db.crear_usuario("B", "dup@example.com", "h2", db_path=self.db_path)

    def test_correo_existe(self):
        self.assertFalse(db.correo_existe("nadie@example.com", db_path=self.db_path))
        db.crear_usuario("A", "si@example.com", "h", db_path=self.db_path)
        self.assertTrue(db.correo_existe("si@example.com", db_path=self.db_path))

    def test_plantilla_biometrica_upsert(self):
        uid = db.crear_usuario("Javier", "javier@example.com", "h", db_path=self.db_path)
        db.guardar_plantilla(uid, "svm/1.bin", "mesh/1.obj", 40, db_path=self.db_path)
        activas = db.obtener_plantillas_activas(db_path=self.db_path)
        self.assertEqual(len(activas), 1)
        self.assertEqual(activas[0]["num_muestras"], 40)

        # Reentrenar (upsert) debe actualizar, no duplicar
        db.guardar_plantilla(uid, "svm/2.bin", "mesh/1.obj", 55, db_path=self.db_path)
        activas = db.obtener_plantillas_activas(db_path=self.db_path)
        self.assertEqual(len(activas), 1)
        self.assertEqual(activas[0]["num_muestras"], 55)
        self.assertEqual(activas[0]["ruta_svm"], "svm/2.bin")

    def test_historial_ingresos(self):
        uid = db.crear_usuario("Cristian", "c@example.com", "h", db_path=self.db_path)
        db.registrar_ingreso(uid, "permitido", 0.83, db_path=self.db_path)
        db.registrar_ingreso(None, "desconocido", -0.4, db_path=self.db_path)

        todos = db.historial_ingresos(db_path=self.db_path)
        self.assertEqual(len(todos), 2)

        solo_uid = db.historial_ingresos(usuario_id=uid, db_path=self.db_path)
        self.assertEqual(len(solo_uid), 1)
        self.assertEqual(solo_uid[0]["resultado"], "permitido")

    def test_listar_usuarios(self):
        db.crear_usuario("A", "a@example.com", "h", db_path=self.db_path)
        db.crear_usuario("B", "b@example.com", "h", db_path=self.db_path)
        self.assertEqual(len(db.listar_usuarios(db_path=self.db_path)), 2)


if __name__ == "__main__":
    unittest.main()
