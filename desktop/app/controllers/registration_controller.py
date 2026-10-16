"""
Controlador de registro de PicMe.

Responsabilidades:
- Capturar muestras faciales por ángulo.
- Validar que el rostro esté presente.
- Validar el yaw solicitado para cada ángulo.
- Construir el vector biométrico.
- Crear el usuario.
- Entrenar y cifrar la plantilla biométrica.
- Construir y cifrar el modelo 3D facial.
- Persistir la plantilla en SQLite.
- Limpiar completamente los artefactos si cualquier paso falla.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np

from .. import config, db, security, vision_service
from ..vision.features import InvalidLandmarksError, landmarks_to_feature_vector
from ..vision.head_pose import estimate_yaw_degrees, yaw_is_in_range
from ..vision.landmark_extractor import LandmarkExtractorProtocol
from ..vision.mesh_builder import build_face_mesh
from ..vision.recognizer import train_user_template


@dataclass
class FrameResult:
    rostro_detectado: bool
    current_angle: Optional[dict]
    frames_current_angle: int
    frames_required: int
    total_samples: int
    angle_completed: bool
    is_complete: bool
    detalle: Optional[str] = None


class RegistrationError(ValueError):
    """
    Error controlado del proceso de registro.

    args[0] contiene un código corto que la vista puede traducir a un
    mensaje amigable.
    """


class RegistrationController:
    def __init__(
        self,
        extractor: Optional[LandmarkExtractorProtocol] = None,
        yaw_estimator: Optional[Callable[[np.ndarray, int, int], float]] = None,
    ):
        self.extractor = extractor or vision_service.get_extractor()
        self.yaw_estimator = yaw_estimator or estimate_yaw_degrees

        self.angle_index = 0
        self.samples_by_angle: dict[str, list[np.ndarray]] = {}

        self.frontal_image: Optional[np.ndarray] = None
        self.frontal_landmarks: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # Estado de captura
    # ------------------------------------------------------------------
    @property
    def current_angle(self) -> Optional[dict]:
        if self.angle_index >= len(config.CAPTURE_ANGLES):
            return None

        return config.CAPTURE_ANGLES[self.angle_index]

    @property
    def is_complete(self) -> bool:
        return self.angle_index >= len(config.CAPTURE_ANGLES)

    def frames_for_current_angle(self) -> int:
        angle = self.current_angle

        if angle is None:
            return 0

        return len(
            self.samples_by_angle.get(
                angle["id"],
                [],
            )
        )

    def total_samples(self) -> int:
        return sum(
            len(samples)
            for samples in self.samples_by_angle.values()
        )

    def all_feature_vectors(self) -> np.ndarray:
        vectors = [
            vector
            for samples in self.samples_by_angle.values()
            for vector in samples
        ]

        if not vectors:
            raise RegistrationError("sin_muestras")

        return np.stack(
            vectors,
            axis=0,
        )

    # ------------------------------------------------------------------
    # Resultado de frame
    # ------------------------------------------------------------------
    def _frame_result(
        self,
        *,
        rostro_detectado: bool,
        angle: Optional[dict],
        angle_completed: bool = False,
        is_complete: bool = False,
        detalle: Optional[str] = None,
    ) -> FrameResult:
        return FrameResult(
            rostro_detectado=rostro_detectado,
            current_angle=angle,
            frames_current_angle=self.frames_for_current_angle(),
            frames_required=config.FRAMES_PER_ANGLE,
            total_samples=self.total_samples(),
            angle_completed=angle_completed,
            is_complete=is_complete,
            detalle=detalle,
        )

    # ------------------------------------------------------------------
    # Procesamiento de cámara
    # ------------------------------------------------------------------
    def process_frame(
        self,
        frame_bgr: np.ndarray,
    ) -> FrameResult:
        if self.is_complete:
            return self._frame_result(
                rostro_detectado=False,
                angle=None,
                detalle="captura_ya_completa",
                is_complete=True,
            )

        angle = self.current_angle

        landmarks = self.extractor.extract(
            frame_bgr
        )

        if landmarks is None:
            return self._frame_result(
                rostro_detectado=False,
                angle=angle,
            )

        # --------------------------------------------------------------
        # Convertir landmarks a vector biométrico.
        # --------------------------------------------------------------
        try:
            feature_vector = landmarks_to_feature_vector(
                landmarks
            )
        except InvalidLandmarksError as exc:
            return self._frame_result(
                rostro_detectado=False,
                angle=angle,
                detalle=str(exc),
            )

        # --------------------------------------------------------------
        # Validar pose de cabeza.
        # --------------------------------------------------------------
        try:
            frame_height, frame_width = frame_bgr.shape[:2]

            yaw = self.yaw_estimator(
                landmarks,
                frame_width,
                frame_height,
            )

        except Exception:
            return self._frame_result(
                rostro_detectado=True,
                angle=angle,
                detalle="pose_no_valida",
            )

        if not yaw_is_in_range(
            yaw,
            angle["yaw_range"],
            tolerance=config.CAPTURE_YAW_TOLERANCE,
        ):
            return self._frame_result(
                rostro_detectado=True,
                angle=angle,
                detalle="angulo_incorrecto",
            )

        # --------------------------------------------------------------
        # Muestra válida.
        # --------------------------------------------------------------
        self.samples_by_angle.setdefault(
            angle["id"],
            [],
        ).append(
            feature_vector
        )

        # --------------------------------------------------------------
        # Guardar una captura frontal para el modelo 3D.
        # --------------------------------------------------------------
        if (
            angle["id"] == "frontal"
            and self.frontal_image is None
        ):
            self.frontal_image = frame_bgr.copy()

            self.frontal_landmarks = np.asarray(
                landmarks,
                dtype=float,
            ).copy()

        angle_completed = False

        # --------------------------------------------------------------
        # Completar ángulo cuando se alcanza el número requerido.
        # --------------------------------------------------------------
        if (
            self.frames_for_current_angle()
            >= config.FRAMES_PER_ANGLE
        ):
            self.angle_index += 1
            angle_completed = True

        return self._frame_result(
            rostro_detectado=True,
            angle=self.current_angle,
            angle_completed=angle_completed,
            is_complete=self.is_complete,
        )

    # ------------------------------------------------------------------
    # Limpieza
    # ------------------------------------------------------------------
    @staticmethod
    def _remove_file(
        path: Optional[Path],
    ) -> None:
        if path is None:
            return

        try:
            path.unlink(
                missing_ok=True
            )
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Finalización
    # ------------------------------------------------------------------
    def finalize(
        self,
        nombre: str,
        correo: str,
        password: str,
    ) -> int:
        """
        Finaliza el registro.

        Si entrenamiento, cifrado, generación del mesh o persistencia
        falla, se elimina el usuario y todos los artefactos creados
        durante este intento.
        """
        if not self.is_complete:
            raise RegistrationError(
                "captura_incompleta"
            )

        if (
            self.frontal_image is None
            or self.frontal_landmarks is None
        ):
            raise RegistrationError(
                "falta_captura_frontal"
            )

        nombre = (
            nombre or ""
        ).strip()

        correo = (
            correo or ""
        ).strip().lower()

        if (
            not nombre
            or not correo
            or len(password or "") < 8
        ):
            raise RegistrationError(
                "datos_invalidos"
            )

        if db.correo_existe(correo):
            raise RegistrationError(
                "correo_ya_registrado"
            )

        feature_vectors = self.all_feature_vectors()

        usuario_id: Optional[int] = None
        svm_path: Optional[Path] = None
        mesh_bundle_path: Optional[Path] = None

        generated_mesh_files: list[Path] = []

        try:
            # ----------------------------------------------------------
            # 1. Hash de contraseña.
            # ----------------------------------------------------------
            password_hash = security.hash_password(
                password
            )

            # ----------------------------------------------------------
            # 2. Crear usuario.
            # ----------------------------------------------------------
            usuario_id = db.crear_usuario(
                nombre,
                correo,
                password_hash,
            )

            # ----------------------------------------------------------
            # 3. Entrenar plantilla biométrica.
            # ----------------------------------------------------------
            template = train_user_template(
                usuario_id,
                feature_vectors,
            )

            templates_dir = (
                config.DATA_DIR
                / "plantillas"
            )

            templates_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            svm_path = (
                templates_dir
                / f"usuario_{usuario_id}.bin"
            )

            template.save(
                svm_path,
                security.BiometricCipher(),
            )

            # ----------------------------------------------------------
            # 4. Construir modelo 3D temporal.
            # ----------------------------------------------------------
            mesh_asset = build_face_mesh(
                self.frontal_landmarks,
                self.frontal_image,
                config.MESH_DIR,
                name=f"usuario_{usuario_id}",
            )

            generated_mesh_files = [
                mesh_asset.obj_path,
                mesh_asset.mtl_path,
                mesh_asset.texture_path,
            ]

            # ----------------------------------------------------------
            # 5. Cifrar OBJ + MTL + textura.
            # ----------------------------------------------------------
            mesh_bundle_path = (
                config.MESH_DIR
                / f"usuario_{usuario_id}.mesh.enc"
            )

            security.encrypt_mesh_bundle(
                obj_path=mesh_asset.obj_path,
                mtl_path=mesh_asset.mtl_path,
                texture_path=mesh_asset.texture_path,
                output_path=mesh_bundle_path,
                user_id=usuario_id,
                cipher=security.BiometricCipher(),
            )

            # ----------------------------------------------------------
            # 6. Eliminar inmediatamente los archivos visuales
            #    originales.
            # ----------------------------------------------------------
            for path in generated_mesh_files:
                self._remove_file(path)

            # ----------------------------------------------------------
            # 7. Guardar únicamente las rutas del material cifrado.
            # ----------------------------------------------------------
            db.guardar_plantilla(
                usuario_id,
                ruta_svm=db.portable_data_path(svm_path),
                ruta_mesh_obj=db.portable_data_path(mesh_bundle_path),
                num_muestras=int(
                    feature_vectors.shape[0]
                ),
            )

            # ----------------------------------------------------------
            # 8. Invalidar cache del reconocedor.
            # ----------------------------------------------------------
            vision_service.invalidate_recognizer_cache()

            return usuario_id

        except Exception as exc:
            # ----------------------------------------------------------
            # Limpiar archivos OBJ/MTL/JPG.
            # ----------------------------------------------------------
            for path in generated_mesh_files:
                self._remove_file(path)

            # ----------------------------------------------------------
            # Limpiar paquete cifrado.
            # ----------------------------------------------------------
            self._remove_file(
                mesh_bundle_path
            )

            # ----------------------------------------------------------
            # Limpiar plantilla biométrica.
            # ----------------------------------------------------------
            self._remove_file(
                svm_path
            )

            # ----------------------------------------------------------
            # Eliminar usuario y su plantilla asociada.
            # ----------------------------------------------------------
            if usuario_id is not None:
                try:
                    db.eliminar_usuario(
                        usuario_id
                    )
                except Exception:
                    pass

            # ----------------------------------------------------------
            # Invalidar cache incluso después de un fallo.
            # ----------------------------------------------------------
            vision_service.invalidate_recognizer_cache()

            if isinstance(
                exc,
                RegistrationError,
            ):
                raise

            # IMPORTANTE:
            # Conservamos el código de error que ya utilizaba el
            # proyecto antes de esta corrección. Los tests y la capa GUI
            # dependen de este contrato.
            raise RegistrationError(
                "error_finalizando_registro"
            ) from exc

