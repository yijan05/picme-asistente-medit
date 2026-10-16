from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ... import model_downloader
from .. import theme


class HomeView(tk.Frame):
    def __init__(self, master: tk.Misc, app, **kwargs):
        super().__init__(master, bg=theme.COLOR_BG, **kwargs)
        self.app = app

        wrapper = tk.Frame(self, bg=theme.COLOR_BG)
        wrapper.place(relx=0.5, rely=0.42, anchor="center")

        brand = tk.Frame(wrapper, bg=theme.COLOR_BG)
        brand.pack(pady=(0, 8))
        tk.Label(
            brand, text="Pic", bg=theme.COLOR_BG, fg=theme.COLOR_TEXT, font=(theme.FONT_FAMILY, 30, "bold")
        ).pack(side="left")
        tk.Label(
            brand, text="Me", bg=theme.COLOR_BG, fg=theme.COLOR_ACCENT, font=(theme.FONT_FAMILY, 30, "bold")
        ).pack(side="left")

        ttk.Label(
            wrapper,
            text="Control de acceso por reconocimiento facial",
            style="Subheading.TLabel",
            anchor="center",
        ).pack(pady=(0, 4))
        ttk.Label(
            wrapper,
            text="Registra tu rostro una vez: el sistema construye tu modelo 3D\ny aprende a reconocerte, con verificación de vida por parpadeo.",
            style="Muted.TLabel",
            justify="center",
            anchor="center",
        ).pack(pady=(0, 28))

        buttons = tk.Frame(wrapper, bg=theme.COLOR_BG)
        buttons.pack()
        ttk.Button(
            buttons, text="Registrarme", style="Accent.TButton", command=self._ir_a_registro
        ).pack(side="left", padx=8)
        ttk.Button(
            buttons, text="Ya tengo cuenta — Ingresar", style="Secondary.TButton", command=self._ir_a_login
        ).pack(side="left", padx=8)

        ttk.Button(
            wrapper, text="Chatbot UCundinamarca y MEDIT", style="Accent.TButton",
            command=self._ir_a_chatbot,
        ).pack(pady=(18, 6))
        ttk.Label(
            wrapper, text="Consulta los doce principios y sus ejemplos. Sin cuenta ni cámara.",
            style="Muted.TLabel",
        ).pack()

    def _ir_a_chatbot(self) -> None:
        from .chatbot_view import ChatbotView

        self.app.show_view(ChatbotView)

    def _ir_a_registro(self) -> None:
        try:
            from .register_view import RegisterView
        except ImportError as exc:
            self.app._show_error_dialog(RuntimeError(
                "Faltan dependencias del reconocimiento facial. Ejecuta INSTALAR_WINDOWS.bat.\n"
                f"Detalle: {exc}"
            ))
            return

        if not model_downloader.is_model_downloaded():
            from .setup_view import SetupRequiredView

            self.app.show_view(SetupRequiredView, next_view_class=RegisterView)
            return
        self.app.show_view(RegisterView)

    def _ir_a_login(self) -> None:
        try:
            from .login_view import LoginView
        except ImportError as exc:
            self.app._show_error_dialog(RuntimeError(
                "Faltan dependencias del reconocimiento facial. Ejecuta INSTALAR_WINDOWS.bat.\n"
                f"Detalle: {exc}"
            ))
            return

        if not model_downloader.is_model_downloaded():
            from .setup_view import SetupRequiredView

            self.app.show_view(SetupRequiredView, next_view_class=LoginView)
            return
        self.app.show_view(LoginView)
