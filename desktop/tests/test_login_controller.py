import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.fakes import FakeLandmarkExtractor, synthetic_landmarks  # noqa: E402


DUMMY_FRAME = np.zeros((10, 10, 3), dtype="uint8")


class TestLoginController(unittest.TestCase):
    def setUp(self):
        self._tmpdir = Path(tempfile.mkdtemp())

        from app import config

        self._orig = {
            "DATA_DIR": config.DATA_DIR,
            "MODELS_DIR": config.MODELS_DIR,
            "MESH_DIR": config.MESH_DIR,
            "DB_PATH": config.DB_PATH,
        }

        config.DATA_DIR = self._tmpdir / "data"
        config.MODELS_DIR = self._tmpdir / "models"
        config.MESH_DIR = self._tmpdir / "data" / "meshes"
        config.DB_PATH = self._tmpdir / "data" / "picme.db"

        config.ensure_directories()

        from app import db, vision_service

        db.init_db()
        vision_service.invalidate_recognizer_cache()

        self.fake_extractor = FakeLandmarkExtractor()

        # El controlador de registro ahora exige que cada captura tenga
        # un yaw compatible con el ángulo solicitado. Los landmarks
        # sintéticos de estos tests no contienen una pose física real,
        # así que inyectamos un estimador determinista.
        self._current_test_angle_index = 0

    def tearDown(self):
        from app import config

        for key, value in self._orig.items():
            setattr(config, key, value)

        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _fake_yaw(self, landmarks, frame_width, frame_height):
        """
        Devuelve un yaw representativo del ángulo que se está registrando.

        Debe coincidir con los rangos definidos en config.CAPTURE_ANGLES:

        0 -> frontal
        1 -> izquierda 45°
        2 -> derecha 45°
        3 -> izquierda 90°
        4 -> derecha 90°
        """
        yaw_by_angle = {
            0: 0.0,
            1: 30.0,
            2: -30.0,
            3: 60.0,
            4: -60.0,
        }

        return yaw_by_angle[self._current_test_angle_index]

    def _registrar(
        self,
        identity_seed: int,
        nombre: str,
        correo: str,
    ) -> int:
        from app import config
        from app.controllers.registration_controller import RegistrationController

        controller = RegistrationController(
            extractor=self.fake_extractor,
            yaw_estimator=self._fake_yaw,
        )

        frame_seed = 0

        for angle_index in range(len(config.CAPTURE_ANGLES)):
            self._current_test_angle_index = angle_index

            for _ in range(config.FRAMES_PER_ANGLE):
                self.fake_extractor.queue(
                    synthetic_landmarks(
                        identity_seed,
                        frame_seed,
                        "open",
                    )
                )

                controller.process_frame(DUMMY_FRAME)
                frame_seed += 1

        return controller.finalize(
            nombre,
            correo,
            "clave-segura-1",
        )

    def test_login_recognizes_enrolled_user_after_blink(self):
        from app import db
        from app.controllers.login_controller import LoginController

        self._registrar(
            identity_seed=7,
            nombre="Cristian Rincon",
            correo="cristian@test.com",
        )

        controller = LoginController(
            extractor=self.fake_extractor
        )

        secuencia = [
            "open",
            "open",
            "closed",
            "closed",
            "open",
            "open",
            "open",
            "open",
        ]

        ultimo = None

        for i, estado in enumerate(secuencia):
            self.fake_extractor.queue(
                synthetic_landmarks(
                    7,
                    1000 + i,
                    estado,
                )
            )

            ultimo = controller.process_frame(DUMMY_FRAME)

            if ultimo.status in ("permitido", "desconocido"):
                break

        self.assertEqual(
            ultimo.status,
            "permitido",
        )

        self.assertEqual(
            ultimo.usuario_nombre,
            "Cristian Rincon",
        )

        historial = db.historial_ingresos(limit=1)

        self.assertEqual(
            historial[0]["resultado"],
            "permitido",
        )

    def test_login_requires_blink_before_granting_access(self):
        from app import config
        from app.controllers.login_controller import LoginController

        self._registrar(
            identity_seed=3,
            nombre="Ana",
            correo="ana@test.com",
        )

        controller = LoginController(
            extractor=self.fake_extractor
        )

        # No se hace ningún parpadeo. Antes del último frame debe seguir
        # esperando el desafío de liveness.
        for i in range(config.LOGIN_MAX_FRAMES - 1):
            self.fake_extractor.queue(
                synthetic_landmarks(
                    3,
                    2000 + i,
                    "open",
                )
            )

            result = controller.process_frame(DUMMY_FRAME)

            self.assertEqual(
                result.status,
                "esperando_parpadeo",
            )

        # El último frame alcanza el límite y debe terminar el intento.
        self.fake_extractor.queue(
            synthetic_landmarks(
                3,
                2000 + config.LOGIN_MAX_FRAMES,
                "open",
            )
        )

        result = controller.process_frame(DUMMY_FRAME)

        self.assertEqual(
            result.status,
            "desconocido",
        )

    def test_login_rejects_unenrolled_identity(self):
        from app import config, db
        from app.controllers.login_controller import LoginController

        self._registrar(
            identity_seed=9,
            nombre="Usuario Real",
            correo="real@test.com",
        )

        controller = LoginController(
            extractor=self.fake_extractor
        )

        secuencia = (
            [
                "open",
                "open",
                "closed",
                "closed",
            ]
            + ["open"] * config.LOGIN_MAX_FRAMES
        )

        ultimo = None

        for i, estado in enumerate(secuencia):
            self.fake_extractor.queue(
                synthetic_landmarks(
                    999,
                    3000 + i,
                    estado,
                )
            )

            ultimo = controller.process_frame(DUMMY_FRAME)

            if ultimo.status in ("permitido", "desconocido"):
                break

        self.assertEqual(
            ultimo.status,
            "desconocido",
        )

        historial = db.historial_ingresos(limit=1)

        self.assertEqual(
            historial[0]["resultado"],
            "desconocido",
        )

        self.assertIsNone(
            historial[0]["usuario_id"],
        )

    def test_identifies_correct_user_among_several(self):
        from app import vision_service
        from app.controllers.login_controller import LoginController

        self._registrar(
            identity_seed=1,
            nombre="Uno",
            correo="uno@test.com",
        )

        self._registrar(
            identity_seed=2,
            nombre="Dos",
            correo="dos@test.com",
        )

        vision_service.invalidate_recognizer_cache()

        controller = LoginController(
            extractor=self.fake_extractor
        )

        secuencia = [
            "open",
            "open",
            "closed",
            "closed",
            "open",
            "open",
            "open",
        ]

        ultimo = None

        for i, estado in enumerate(secuencia):
            self.fake_extractor.queue(
                synthetic_landmarks(
                    2,
                    5000 + i,
                    estado,
                )
            )

            ultimo = controller.process_frame(DUMMY_FRAME)

            if ultimo.status in ("permitido", "desconocido"):
                break

        self.assertEqual(
            ultimo.status,
            "permitido",
        )

        self.assertEqual(
            ultimo.usuario_nombre,
            "Dos",
        )

    def test_no_face_returns_sin_rostro(self):
        from app.controllers.login_controller import LoginController

        self._registrar(
            identity_seed=5,
            nombre="Alguien",
            correo="alguien@test.com",
        )

        controller = LoginController(
            extractor=self.fake_extractor
        )

        self.fake_extractor.queue(None)

        result = controller.process_frame(DUMMY_FRAME)

        self.assertEqual(
            result.status,
            "sin_rostro",
        )

    def test_no_face_eventually_times_out(self):
        from app import config, db
        from app.controllers.login_controller import LoginController

        self._registrar(
            identity_seed=20,
            nombre="Usuario",
            correo="usuario@test.com",
        )

        controller = LoginController(
            extractor=self.fake_extractor
        )

        ultimo = None

        for _ in range(config.LOGIN_MAX_FRAMES):
            self.fake_extractor.queue(None)

            ultimo = controller.process_frame(DUMMY_FRAME)

        self.assertEqual(
            ultimo.status,
            "desconocido",
        )

        self.assertEqual(
            controller.frames_seen,
            config.LOGIN_MAX_FRAMES,
        )

        historial = db.historial_ingresos(limit=1)

        self.assertEqual(
            historial[0]["resultado"],
            "desconocido",
        )

        self.assertIsNone(
            historial[0]["usuario_id"],
        )

    def test_timeout_does_not_register_multiple_unknown_attempts(self):
        from app import config, db
        from app.controllers.login_controller import LoginController

        self._registrar(
            identity_seed=21,
            nombre="Usuario",
            correo="usuario2@test.com",
        )

        controller = LoginController(
            extractor=self.fake_extractor
        )

        for _ in range(config.LOGIN_MAX_FRAMES):
            self.fake_extractor.queue(None)

            controller.process_frame(DUMMY_FRAME)

        # Las llamadas posteriores no deben generar nuevos registros.
        for _ in range(5):
            result = controller.process_frame(DUMMY_FRAME)

            self.assertEqual(
                result.status,
                "desconocido",
            )

        historial = db.historial_ingresos(limit=20)

        desconocidos = [
            ingreso
            for ingreso in historial
            if ingreso["resultado"] == "desconocido"
        ]

        self.assertEqual(
            len(desconocidos),
            1,
        )


if __name__ == "__main__":
    unittest.main()