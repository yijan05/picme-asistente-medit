"""
Widget de cámara reutilizable entre las vistas de registro y login.

Encapsula el patrón estándar para mostrar video de OpenCV dentro de
Tkinter: `cv2.VideoCapture` lee un frame, se convierte a `PIL.Image` y
luego a `ImageTk.PhotoImage` para poder mostrarlo en un `tk.Label`,
todo disparado por `after()` (el temporizador propio de Tkinter).

El callback `on_frame(frame_bgr)` es donde se conecta la lógica de
negocio (los controladores de registro/login): se llama una vez por
frame, ANTES de dibujarlo en pantalla, con la imagen en formato BGR.
"""

from __future__ import annotations

import tkinter as tk
import sys
from typing import Callable, Optional

import cv2
import numpy as np
from PIL import Image, ImageTk

from ... import config


class CameraView(tk.Label):
    def __init__(
        self,
        master: tk.Misc,
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
        mirror: bool = True,
        on_frame: Optional[Callable[[np.ndarray], None]] = None,
        **kwargs,
    ):
        super().__init__(master, bg="#000000", **kwargs)

        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.mirror = mirror
        self.on_frame = on_frame

        self._photo_image: Optional[ImageTk.PhotoImage] = None
        self._running = False
        self._after_id: Optional[str] = None

        self._cap: Optional[cv2.VideoCapture] = None

        self._open_camera()

    def _open_camera(self) -> bool:
        """
        Abre la cámara y aplica la configuración solicitada.

        Devuelve True si la cámara quedó abierta correctamente.
        """
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass

        # DirectShow suele evitar la pantalla negra de algunas cámaras en Windows.
        if sys.platform == "win32":
            self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self._cap.isOpened():
                self._cap.release()
                self._cap = cv2.VideoCapture(self.camera_index)
        else:
            self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Intentamos configurar el FPS, pero no asumimos que la cámara
        # necesariamente lo soporte.
        self._cap.set(
            cv2.CAP_PROP_FPS,
            config.CAMERA_FPS_TARGET,
        )

        return True

    def is_opened(self) -> bool:
        """Indica si la cámara está actualmente abierta."""
        return self._cap is not None and self._cap.isOpened()

    def start(self, interval_ms: int = 40) -> None:
        """
        Inicia la lectura periódica de frames.

        Si la cámara no está abierta, no intenta iniciar el ciclo.
        """
        if not self.is_opened():
            return

        if self._running:
            return

        self._running = True
        self._tick(interval_ms)

    def stop(self) -> None:
        """
        Detiene la lectura de frames y libera la cámara.
        """
        self._running = False

        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except tk.TclError:
                pass

            self._after_id = None

        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass

    def reopen(self) -> bool:
        """
        Vuelve a abrir la cámara después de haber sido cerrada.

        Es especialmente útil para el botón "Intentar de nuevo":
        `stop()` libera VideoCapture y, por tanto, necesitamos crear
        una nueva instancia antes de volver a llamar a `start()`.

        Devuelve True si la cámara pudo abrirse correctamente.
        """
        # Primero nos aseguramos de detener cualquier ciclo anterior.
        self.stop()

        # Intentamos abrir nuevamente el dispositivo.
        return self._open_camera()

    def _tick(self, interval_ms: int) -> None:
        """
        Lee un frame y programa el siguiente ciclo mediante Tkinter.after().
        """
        if not self._running:
            return

        if self._cap is None or not self._cap.isOpened():
            self._running = False
            self._after_id = None
            return

        ok, frame = self._cap.read()

        if ok:
            if self.mirror:
                frame = cv2.flip(frame, 1)

            if self.on_frame is not None:
                self.on_frame(frame)

            self._render(frame)

        self._after_id = self.after(
            interval_ms,
            lambda: self._tick(interval_ms),
        )

    def _render(self, frame_bgr: np.ndarray) -> None:
        """
        Convierte el frame BGR a RGB y lo muestra en el Label.
        """
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)

        # Ajustar al tamaño actual del widget si ya tiene uno asignado.
        target_w = self.winfo_width()
        target_h = self.winfo_height()

        if target_w > 10 and target_h > 10:
            image = image.resize((target_w, target_h))

        self._photo_image = ImageTk.PhotoImage(image=image)
        self.configure(image=self._photo_image)
