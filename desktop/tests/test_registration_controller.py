import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

from tests.fakes import (  # noqa: E402
    FakeLandmarkExtractor,
    synthetic_landmarks,
)


class TestRegistrationController(unittest.TestCase):

    def setUp(self):
        self._tmpdir = Path(
            tempfile.mkdtemp()
        )

        from app import config

        self._orig = {
            "DATA_DIR": config.DATA_DIR,
            "MODELS_DIR": config.MODELS_DIR,
            "MESH_DIR": config.MESH_DIR,
            "DB_PATH": config.DB_PATH,
        }

        config.DATA_DIR = (
            self._tmpdir / "data"
        )
        config.MODELS_DIR = (
            self._tmpdir / "models"
        )
        config.MESH_DIR = (
            self._tmpdir
            / "data"
            / "meshes"
        )
        config.DB_PATH = (
            self._tmpdir
            / "data"
            / "picme.db"
        )

        config.ensure_directories()

        from app import db, vision_service

        db.init_db()
        vision_service.invalidate_recognizer_cache()

        self.fake_extractor = (
            FakeLandmarkExtractor()
        )

    def tearDown(self):
        from app import config

        for key, value in self._orig.items():
            setattr(config, key, value)

        shutil.rmtree(
            self._tmpdir,
            ignore_errors=True,
        )

    # ------------------------------------------------------------------
    def _fake_yaw(
        self,
        landmarks,
        frame_width,
        frame_height,
    ):
        """
        Devuelve un yaw válido para el ángulo actual.

        Esto evita que las pruebas unitarias dependan de solvePnP.
        La estimación real de yaw se prueba por separado.
        """
        from app import config

        angle_index = (
            self._current_test_angle_index
        )

        yaw_by_angle = [
            0.0,     # frontal
            30.0,    # izquierda 45
            -30.0,   # derecha 45
            60.0,    # izquierda 90
            -60.0,   # derecha 90
        ]

        return yaw_by_angle[
            angle_index
        ]

    # ------------------------------------------------------------------
    def _completar_captura(
        self,
        controller,
        identity_seed: int,
    ):
        from app import config

        frame_seed = 0

        for angle_index in range(
            len(config.CAPTURE_ANGLES)
        ):
            self._current_test_angle_index = (
                angle_index
            )

            for _ in range(
                config.FRAMES_PER_ANGLE
            ):
                frame = synthetic_landmarks(
                    identity_seed,
                    frame_seed,
                    "open",
                )

                self.fake_extractor.queue(
                    frame
                )

                dummy_frame = np.zeros(
                    (10, 10, 3),
                    dtype="uint8",
                )

                result = (
                    controller.process_frame(
                        dummy_frame
                    )
                )

                self.assertTrue(
                    result.rostro_detectado
                )

                self.assertEqual(
                    result.detalle,
                    None,
                )

                frame_seed += 1

    # ------------------------------------------------------------------
    def test_full_capture_and_finalize(self):
        from app import db
        from app.controllers.registration_controller import (
            RegistrationController,
        )

        controller = RegistrationController(
            extractor=self.fake_extractor,
            yaw_estimator=self._fake_yaw,
        )

        self.assertFalse(
            controller.is_complete
        )

        self._completar_captura(
            controller,
            identity_seed=1,
        )

        self.assertTrue(
            controller.is_complete
        )

        usuario_id = controller.finalize(
            "Evelin Virguez",
            "evelin@test.com",
            "clave-segura-1",
        )

        self.assertIsInstance(
            usuario_id,
            int,
        )

        usuario = (
            db.obtener_usuario_por_correo(
                "evelin@test.com"
            )
        )

        self.assertIsNotNone(
            usuario
        )

        plantillas = (
            db.obtener_plantillas_activas()
        )

        self.assertEqual(
            len(plantillas),
            1,
        )

        mesh_path = Path(
            plantillas[0][
                "ruta_mesh_obj"
            ]
        )

        self.assertTrue(
            mesh_path.exists()
        )

    # ------------------------------------------------------------------
    def test_finalize_before_complete_raises(self):
        from app.controllers.registration_controller import (
            RegistrationController,
            RegistrationError,
        )

        controller = RegistrationController(
            extractor=self.fake_extractor,
            yaw_estimator=self._fake_yaw,
        )

        with self.assertRaises(
            RegistrationError
        ) as ctx:
            controller.finalize(
                "Nombre",
                "correo@test.com",
                "clave-segura-1",
            )

        self.assertEqual(
            ctx.exception.args[0],
            "captura_incompleta",
        )

    # ------------------------------------------------------------------
    def test_finalize_rejects_duplicate_email(self):
        from app.controllers.registration_controller import (
            RegistrationController,
            RegistrationError,
        )

        c1 = RegistrationController(
            extractor=self.fake_extractor,
            yaw_estimator=self._fake_yaw,
        )

        self._completar_captura(
            c1,
            identity_seed=1,
        )

        c1.finalize(
            "Uno",
            "dup@test.com",
            "clave-segura-1",
        )

        c2 = RegistrationController(
            extractor=self.fake_extractor,
            yaw_estimator=self._fake_yaw,
        )

        self._completar_captura(
            c2,
            identity_seed=2,
        )

        with self.assertRaises(
            RegistrationError
        ) as ctx:
            c2.finalize(
                "Dos",
                "dup@test.com",
                "otra-clave-1",
            )

        self.assertEqual(
            ctx.exception.args[0],
            "correo_ya_registrado",
        )

    # ------------------------------------------------------------------
    def test_finalize_rejects_short_password(self):
        from app.controllers.registration_controller import (
            RegistrationController,
            RegistrationError,
        )

        controller = RegistrationController(
            extractor=self.fake_extractor,
            yaw_estimator=self._fake_yaw,
        )

        self._completar_captura(
            controller,
            identity_seed=3,
        )

        with self.assertRaises(
            RegistrationError
        ) as ctx:
            controller.finalize(
                "Nombre",
                "corto@test.com",
                "1234567",
            )

        self.assertEqual(
            ctx.exception.args[0],
            "datos_invalidos",
        )

    # ------------------------------------------------------------------
    def test_no_face_detected_does_not_advance_angle(self):
        from app.controllers.registration_controller import (
            RegistrationController,
        )

        controller = RegistrationController(
            extractor=self.fake_extractor,
            yaw_estimator=self._fake_yaw,
        )

        angle_inicial = (
            controller.current_angle["id"]
        )

        self.fake_extractor.queue(None)

        result = controller.process_frame(
            np.zeros(
                (10, 10, 3),
                dtype="uint8",
            )
        )

        self.assertFalse(
            result.rostro_detectado
        )

        self.assertEqual(
            controller.current_angle["id"],
            angle_inicial,
        )

        self.assertEqual(
            controller.total_samples(),
            0,
        )

    # ------------------------------------------------------------------
    def test_wrong_yaw_does_not_capture_sample(self):
        from app.controllers.registration_controller import (
            RegistrationController,
        )

        wrong_yaw = lambda landmarks, width, height: 45.0

        controller = RegistrationController(
            extractor=self.fake_extractor,
            yaw_estimator=wrong_yaw,
        )

        landmarks = synthetic_landmarks(
            identity_seed=10,
            frame_seed=0,
            eye_state="open",
        )

        self.fake_extractor.queue(
            landmarks
        )

        result = controller.process_frame(
            np.zeros(
                (10, 10, 3),
                dtype="uint8",
            )
        )

        self.assertTrue(
            result.rostro_detectado
        )

        self.assertEqual(
            result.detalle,
            "angulo_incorrecto",
        )

        self.assertEqual(
            controller.total_samples(),
            0,
        )

        self.assertEqual(
            controller.current_angle["id"],
            "frontal",
        )

    # ------------------------------------------------------------------
    def test_failed_training_rolls_back_user_and_files(self):
        from app import db
        from app.controllers.registration_controller import (
            RegistrationController,
            RegistrationError,
        )

        controller = RegistrationController(
            extractor=self.fake_extractor,
            yaw_estimator=self._fake_yaw,
        )

        self._completar_captura(
            controller,
            identity_seed=20,
        )

        with patch(
            "app.controllers.registration_controller.train_user_template",
            side_effect=RuntimeError(
                "fallo simulado de entrenamiento"
            ),
        ):
            with self.assertRaises(
                RegistrationError
            ) as ctx:
                controller.finalize(
                    "Usuario Fallido",
                    "fallo@test.com",
                    "clave-segura-1",
                )

        self.assertEqual(
            ctx.exception.args[0],
            "error_finalizando_registro",
        )

        # El usuario NO debe quedar en SQLite.
        usuario = (
            db.obtener_usuario_por_correo(
                "fallo@test.com"
            )
        )

        self.assertIsNone(
            usuario
        )

        # No debe existir plantilla biométrica.
        plantillas = (
            db.obtener_plantillas_activas()
        )

        self.assertEqual(
            len(plantillas),
            0,
        )

        templates_dir = (
            self._tmpdir
            / "data"
            / "plantillas"
        )

        if templates_dir.exists():
            self.assertEqual(
                list(
                    templates_dir.iterdir()
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()