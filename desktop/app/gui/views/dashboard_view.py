from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ... import auth, db
from .. import theme


class DashboardView(tk.Frame):
    """
    Panel principal del usuario autenticado.

    El dashboard contiene únicamente información perteneciente a la
    sesión actual. No expone la lista de otros usuarios ni el historial
    global de accesos.
    """

    def __init__(self, master: tk.Misc, app, **kwargs):
        super().__init__(master, bg=theme.COLOR_BG, **kwargs)
        self.app = app
        self.user = auth.current_user()

        if self.user is None:
            self.after(0, self._volver_al_inicio)
            return

        self._build_layout()
        self._load_data()

    def _build_layout(self) -> None:
        header = tk.Frame(self, bg=theme.COLOR_BG)
        header.pack(fill="x", padx=32, pady=(24, 8))

        ttk.Label(
            header,
            text=f"Bienvenido, {self.user.nombre}",
            style="Heading.TLabel",
        ).pack(side="left")

        actions = tk.Frame(header, bg=theme.COLOR_BG)
        actions.pack(side="right")

        ttk.Button(
            actions, text="Chatbot", style="Secondary.TButton", command=self._ir_a_chatbot,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions,
            text="Mi perfil",
            style="Secondary.TButton",
            command=self._ir_a_perfil,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions,
            text="Cerrar sesión",
            style="Secondary.TButton",
            command=self._cerrar_sesion,
        ).pack(side="left")

        body = tk.Frame(self, bg=theme.COLOR_BG)
        body.pack(
            fill="both",
            expand=True,
            padx=32,
            pady=(8, 24),
        )

        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        historial_panel = ttk.Frame(
            body,
            style="Card.TFrame",
        )
        historial_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        ttk.Label(
            historial_panel,
            text="Mi actividad reciente",
            style="Card.TLabel",
            font=theme.FONT_SUBHEADING,
        ).pack(
            anchor="w",
            padx=16,
            pady=(16, 4),
        )

        ttk.Label(
            historial_panel,
            text="Aquí solo se muestran tus propios intentos de acceso.",
            style="CardMuted.TLabel",
        ).pack(
            anchor="w",
            padx=16,
            pady=(0, 8),
        )

        self.historial_tree = ttk.Treeview(
            historial_panel,
            columns=("resultado", "fecha"),
            show="headings",
            height=14,
        )

        self.historial_tree.heading(
            "resultado",
            text="Resultado",
        )
        self.historial_tree.heading(
            "fecha",
            text="Fecha",
        )

        self.historial_tree.column(
            "resultado",
            width=180,
            anchor="center",
        )
        self.historial_tree.column(
            "fecha",
            width=220,
            anchor="center",
        )

        scrollbar = ttk.Scrollbar(
            historial_panel,
            orient="vertical",
            command=self.historial_tree.yview,
        )

        self.historial_tree.configure(
            yscrollcommand=scrollbar.set,
        )

        self.historial_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(16, 0),
            pady=(0, 16),
        )

        scrollbar.pack(
            side="right",
            fill="y",
            padx=(0, 16),
            pady=(0, 16),
        )

    def _load_data(self) -> None:
        """
        Carga exclusivamente el historial del usuario autenticado.

        No se consulta listar_usuarios() ni historial_ingresos() global,
        por lo que esta vista no recibe información de otros usuarios.
        """
        if self.user is None:
            return

        for ingreso in db.historial_ingresos(
            usuario_id=self.user.id,
            limit=30,
        ):
            fecha = (
                ingreso.get("creado_en") or ""
            )[:19].replace("T", " ")

            resultado = ingreso.get(
                "resultado",
                "desconocido",
            )

            self.historial_tree.insert(
                "",
                "end",
                values=(
                    resultado,
                    fecha,
                ),
            )

    def _ir_a_perfil(self) -> None:
        from .profile_view import ProfileView

        self.app.show_view(ProfileView)

    def _ir_a_chatbot(self) -> None:
        from .chatbot_view import ChatbotView

        self.app.show_view(ChatbotView)

    def _cerrar_sesion(self) -> None:
        auth.logout_user()

        from .home_view import HomeView

        self.app.show_view(HomeView)

    def _volver_al_inicio(self) -> None:
        from .home_view import HomeView

        self.app.show_view(HomeView)
