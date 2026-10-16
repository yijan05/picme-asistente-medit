"""
Ventana principal del programa.

Actúa como un "enrutador" muy simple: mantiene una sola vista visible a
la vez, cambia entre ellas destruyendo la anterior (llamando a su
`on_leave()` si la define, para por ejemplo liberar la cámara) y creando
la nueva. Cada vista recibe `app` (esta misma ventana) para poder pedir
la siguiente navegación (`self.app.show_view(...)`).
"""
from __future__ import annotations

import tkinter as tk
import sys
from typing import Any

from .. import auth
from . import theme

MIN_WIDTH = 900
MIN_HEIGHT = 640


class AppWindow(tk.Tk):
    def __init__(self, chatbot_only: bool = False):
        super().__init__()
        self.chatbot_only = chatbot_only
        self.title("PicMe — Universidad de Cundinamarca")
        self.geometry(f"{MIN_WIDTH}x{MIN_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        theme.apply(self)

        self._current_view: tk.Widget | None = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if chatbot_only:
            from .views.chatbot_view import ChatbotView
            self.show_view(ChatbotView)
        else:
            from .views.home_view import HomeView
            self.show_view(HomeView)

    def show_view(self, view_class: type[tk.Widget], **kwargs: Any) -> None:
        # Importante: se construye la vista NUEVA primero, y solo si eso
        # tiene éxito se destruye la anterior. Si se hiciera al revés (destruir
        # y luego construir), un error al construir la vista nueva dejaría
        # la ventana sin ninguna vista visible (en blanco), que es
        # exactamente lo que pasaba antes de esta corrección.
        try:
            view = view_class(self, app=self, **kwargs)
        except Exception as exc:
            import traceback

            traceback.print_exc()
            self._show_error_dialog(exc)
            return

        if self._current_view is not None:
            leave = getattr(self._current_view, "on_leave", None)
            if callable(leave):
                leave()
            self._current_view.destroy()

        view.pack(fill="both", expand=True)
        self._current_view = view

    def _show_error_dialog(self, exc: Exception) -> None:
        from tkinter import messagebox

        messagebox.showerror(
            "No se pudo abrir esa pantalla",
            f"Ocurrió un problema y la pantalla no se pudo mostrar:\n\n{exc}\n\n"
            "Revisa la consola para más detalles técnicos.",
        )

    def _on_close(self) -> None:
        leave = getattr(self._current_view, "on_leave", None)
        if callable(leave):
            leave()
        # El chatbot también funciona sin instalar el motor biométrico.
        service = sys.modules.get("app.vision_service")
        if service is not None:
            service.close_extractor()
        self.destroy()
