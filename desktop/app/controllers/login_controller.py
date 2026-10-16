"""
Controlador de login: exige al menos un parpadeo real y reconoce al
usuario contra todas las plantillas guardadas, frame a frame.

Misma lógica que la versión web (`api_login.py` + `LoginSession`), ahora
como una clase Python normal que la vista de Tkinter alimenta con cada
frame que llega de la cámara.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .. import config, db, vision_service
from ..vision.features import InvalidLandmarksError, landmarks_to_feature_vector
from ..vision.landmark_extractor import LandmarkExtractorProtocol
from ..vision.liveness import BlinkDetector
from ..vision.recognizer import Recognizer

RECENT_WINDOW = 5


@dataclass
class LoginFrameResult:
    status: str  # 'sin_rostro' | 'esperando_parpadeo' | 'verificando' | 'rostro_no_valido' | 'permitido' | 'desconocido'
    ear: Optional[float] = None
    parpadeos: int = 0
    usuario_id: Optional[int] = None
    usuario_nombre: Optional[str] = None


class LoginController:
    def __init__(
        self,
        extractor: Optional[LandmarkExtractorProtocol] = None,
        recognizer: Optional[Recognizer] = None,
    ):
        self.extractor = extractor or vision_service.get_extractor()
        self._recognizer_override = recognizer
        self.blink_detector = BlinkDetector()
        self.recent_user_ids: list[Optional[int]] = []
        self.frames_seen = 0

        # Evita registrar múltiples veces el mismo intento cuando se
        # continúa llamando a process_frame() después de alcanzar el límite.
        self._finished = False
        self._final_result: Optional[LoginFrameResult] = None
        self._last_score: Optional[float] = None

    def _recognizer(self) -> Recognizer:
        return self._recognizer_override or vision_service.get_recognizer()

    def _push_identification(self, user_id: Optional[int]) -> None:
        self.recent_user_ids.append(user_id)
        if len(self.recent_user_ids) > RECENT_WINDOW:
            self.recent_user_ids.pop(0)

    def _stable_user_id(self) -> Optional[int]:
        """Exige que la identificación sea consistente en varios frames
        recientes antes de aceptarla (evita conceder acceso por un solo
        frame afortunado/ruidoso)."""
        if len(self.recent_user_ids) < 3:
            return None

        last_three = self.recent_user_ids[-3:]

        if (
            last_three[0] is not None
            and last_three[0] == last_three[1] == last_three[2]
        ):
            return last_three[0]

        return None

    def _finish_unknown(
        self,
        ear: Optional[float] = None,
        score: Optional[float] = None,
    ) -> LoginFrameResult:
        """
        Finaliza el intento como desconocido y registra el acceso una sola vez.
        """
        if self._finished and self._final_result is not None:
            return self._final_result

        final_score = score if score is not None else self._last_score

        db.registrar_ingreso(
            None,
            "desconocido",
            final_score,
        )

        self._finished = True

        self._final_result = LoginFrameResult(
            status="desconocido",
            ear=ear,
            parpadeos=self.blink_detector.blink_count,
        )

        return self._final_result

    def process_frame(self, frame_bgr) -> LoginFrameResult:
        """
        Procesa un frame de cámara.

        Cada frame cuenta para LOGIN_MAX_FRAMES, incluso cuando no se
        encuentra un rostro. Esto evita que una sesión de login quede
        ejecutándose indefinidamente si la persona se aleja de la cámara,
        no aparece frente a ella o nunca completa el desafío de liveness.
        """
        if self._finished and self._final_result is not None:
            return self._final_result

        self.frames_seen += 1

        landmarks = self.extractor.extract(frame_bgr)

        if landmarks is None:
            if self.frames_seen >= config.LOGIN_MAX_FRAMES:
                return self._finish_unknown()

            return LoginFrameResult(
                status="sin_rostro",
                parpadeos=self.blink_detector.blink_count,
            )

        ear = self.blink_detector.update(landmarks)

        try:
            feature_vector = landmarks_to_feature_vector(landmarks)
        except InvalidLandmarksError:
            if self.frames_seen >= config.LOGIN_MAX_FRAMES:
                return self._finish_unknown(ear=ear)

            return LoginFrameResult(
                status="rostro_no_valido",
                ear=ear,
                parpadeos=self.blink_detector.blink_count,
            )

        result = self._recognizer().identify(feature_vector)
        self._last_score = result.score

        self._push_identification(
            result.user_id if result.is_known else None
        )

        if self.blink_detector.blink_count < config.BLINKS_REQUIRED_LOGIN:
            if self.frames_seen >= config.LOGIN_MAX_FRAMES:
                return self._finish_unknown(
                    ear=ear,
                    score=result.score,
                )

            return LoginFrameResult(
                status="esperando_parpadeo",
                ear=ear,
                parpadeos=self.blink_detector.blink_count,
            )

        stable_user_id = self._stable_user_id()

        if stable_user_id is not None:
            usuario = db.obtener_usuario_por_id(stable_user_id)

            db.registrar_ingreso(
                stable_user_id,
                "permitido",
                result.score,
            )

            self._finished = True

            self._final_result = LoginFrameResult(
                status="permitido",
                ear=ear,
                usuario_id=stable_user_id,
                usuario_nombre=usuario.nombre if usuario else None,
                parpadeos=self.blink_detector.blink_count,
            )

            return self._final_result

        if self.frames_seen >= config.LOGIN_MAX_FRAMES:
            return self._finish_unknown(
                ear=ear,
                score=result.score,
            )

        return LoginFrameResult(
            status="verificando",
            ear=ear,
            parpadeos=self.blink_detector.blink_count,
        )