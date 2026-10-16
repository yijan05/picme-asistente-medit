from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ... import auth, config
from ...controllers.login_controller import LoginController
from .. import theme
from ..widgets.camera_view import CameraView


MENSAJES = {
    "sin_rostro": "No se detecta tu rostro. Céntrate frente a la cámara.",
    "esperando_parpadeo": "Parpadea con naturalidad para confirmar que estás presente.",
    "verificando": "Verificando identidad…",
    "rostro_no_valido": "No se pudo procesar el rostro, ajusta el encuadre.",
    "desconocido": "No se reconoce tu rostro.",
    "permitido": "¡Identidad verificada!",
}


class LoginView(tk.Frame):
    def __init__(self, master: tk.Misc, app, **kwargs):
        super().__init__(master, bg=theme.COLOR_BG, **kwargs)

        self.app = app
        self.controller = LoginController()
        self._finished = False

        self._build_layout()
        self._start_camera()

    def _build_layout(self) -> None:
        header = tk.Frame(self, bg=theme.COLOR_BG)
        header.pack(fill="x", padx=32, pady=(24, 8))

        ttk.Label(
            header,
            text="Ingresar",
            style="Heading.TLabel",
        ).pack(side="left")

        ttk.Button(
            header,
            text="Volver",
            style="Secondary.TButton",
            command=self._volver,
        ).pack(side="right")

        ttk.Label(
            self,
            text="Mira a la cámara y parpadea con naturalidad.",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=32, pady=(0, 16))

        center = tk.Frame(self, bg=theme.COLOR_BG)
        center.pack(expand=True)

        camera_panel = tk.Frame(
            center,
            bg="#000000",
            width=480,
            height=360,
        )
        camera_panel.pack()
        camera_panel.pack_propagate(False)

        self.camera_view = CameraView(
            camera_panel,
            camera_index=config.CAMERA_INDEX,
            width=config.CAMERA_WIDTH,
            height=config.CAMERA_HEIGHT,
            on_frame=self._on_frame,
        )
        self.camera_view.pack(fill="both", expand=True)

        self.status_var = tk.StringVar(
            value="Preparando cámara…"
        )

        ttk.Label(
            center,
            textvariable=self.status_var,
            style="Subheading.TLabel",
        ).pack(pady=(16, 4))

        self.hint_var = tk.StringVar(value="")

        ttk.Label(
            center,
            textvariable=self.hint_var,
            style="Muted.TLabel",
        ).pack()

        self.retry_button = ttk.Button(
            center,
            text="Intentar de nuevo",
            style="Secondary.TButton",
            command=self._reintentar,
        )

        # No se muestra hasta que sea necesario.
        self.retry_button.pack_forget()

        self.register_hint = tk.Frame(
            self,
            bg=theme.COLOR_BG,
        )
        self.register_hint.pack(
            side="bottom",
            pady=16,
        )

        ttk.Label(
            self.register_hint,
            text="¿No tienes cuenta todavía?",
            style="Muted.TLabel",
        ).pack(side="left")

        ttk.Button(
            self.register_hint,
            text="Regístrate aquí",
            style="Secondary.TButton",
            command=self._ir_a_registro,
        ).pack(side="left", padx=8)

    def _start_camera(self) -> None:
        """
        Comprueba que la cámara esté abierta y comienza la captura.
        """
        if not self.camera_view.is_opened():
            self.status_var.set(
                "No se pudo acceder a la cámara"
            )

            self.hint_var.set(
                "Revisa que esté conectada y que ningún otro "
                "programa la esté usando."
            )
            return

        self.camera_view.start(
            interval_ms=max(
                1,
                1000 // config.CAMERA_FPS_TARGET,
            )
        )

    def _on_frame(self, frame_bgr) -> None:
        """
        Procesa cada frame recibido desde CameraView.
        """
        if self._finished:
            return

        result = self.controller.process_frame(frame_bgr)

        self.status_var.set(
            MENSAJES.get(
                result.status,
                "Analizando…",
            )
        )

        if result.status == "permitido":
            self._finished = True

            self.camera_view.stop()

            auth.login_user(result.usuario_id)

            self.after(
                600,
                self._ir_a_dashboard,
            )

        elif result.status == "desconocido":
            self._finished = True

            self.camera_view.stop()

            self.hint_var.set(
                "¿No reconoce tu rostro? "
                "Puedes intentarlo de nuevo."
            )

            self.retry_button.pack(
                pady=(8, 0)
            )

    def _reintentar(self) -> None:
        """
        Reinicia completamente el intento de login.

        Antes de esta corrección, `camera_view.stop()` liberaba
        VideoCapture y `_start_camera()` intentaba reutilizar esa
        instancia ya cerrada.

        Ahora `reopen()` crea nuevamente el VideoCapture.
        """
        self.retry_button.pack_forget()

        self.hint_var.set("")

        self._finished = False

        self.controller = LoginController()

        self.status_var.set(
            "Preparando cámara…"
        )

        # Volvemos a abrir físicamente el dispositivo.
        if not self.camera_view.reopen():
            self.status_var.set(
                "No se pudo acceder a la cámara"
            )

            self.hint_var.set(
                "No se pudo volver a abrir la cámara. "
                "Revisa que esté conectada y que ningún "
                "otro programa la esté usando."
            )

            self.retry_button.pack(
                pady=(8, 0)
            )

            return

        # La cámara volvió a abrirse correctamente.
        self._start_camera()

    def _ir_a_dashboard(self) -> None:
        from .dashboard_view import DashboardView

        self.app.show_view(DashboardView)

    def _ir_a_registro(self) -> None:
        from .register_view import RegisterView

        # Registro abre el mismo dispositivo al construirse. Hay que
        # liberarlo antes, aunque show_view destruya esta vista después.
        self.camera_view.stop()
        self.app.show_view(RegisterView)
        if self.app._current_view is self:
            # Si la nueva pantalla falló, recuperar el intento anterior.
            self._reintentar()

    def _volver(self) -> None:
        from .home_view import HomeView

        self.app.show_view(HomeView)

    def on_leave(self) -> None:
        """
        Libera la cámara al abandonar la vista.
        """
        self.camera_view.stop()

