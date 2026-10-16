from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ... import auth, db, security
from .. import theme
from ..widgets.mesh_viewer import MeshViewer


class ProfileView(tk.Frame):
    def __init__(self, master: tk.Misc, app, **kwargs):
        super().__init__(
            master,
            bg=theme.COLOR_BG,
            **kwargs,
        )

        self.app = app
        self.user = auth.current_user()

        self._build_layout()
        self._load_data()

    def _build_layout(self) -> None:
        header = tk.Frame(
            self,
            bg=theme.COLOR_BG,
        )

        header.pack(
            fill="x",
            padx=32,
            pady=(24, 8),
        )

        ttk.Label(
            header,
            text="Mi perfil",
            style="Heading.TLabel",
        ).pack(side="left")

        ttk.Button(
            header,
            text="Volver al panel",
            style="Secondary.TButton",
            command=self._volver,
        ).pack(side="right")

        body = tk.Frame(
            self,
            bg=theme.COLOR_BG,
        )

        body.pack(
            fill="both",
            expand=True,
            padx=32,
            pady=(8, 24),
        )

        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # --------------------------------------------------------------
        # Información personal + historial.
        # --------------------------------------------------------------
        info_panel = ttk.Frame(
            body,
            style="Card.TFrame",
        )

        info_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 12),
        )

        ttk.Label(
            info_panel,
            text="Datos",
            style="Card.TLabel",
            font=theme.FONT_SUBHEADING,
        ).pack(
            anchor="w",
            padx=16,
            pady=(16, 8),
        )

        self.info_labels_frame = tk.Frame(
            info_panel,
            bg=theme.COLOR_BG_ALT,
        )

        self.info_labels_frame.pack(
            fill="x",
            padx=16,
        )

        ttk.Label(
            info_panel,
            text="Mis últimos ingresos",
            style="Card.TLabel",
            font=theme.FONT_SUBHEADING,
        ).pack(
            anchor="w",
            padx=16,
            pady=(16, 8),
        )

        self.historial_tree = ttk.Treeview(
            info_panel,
            columns=("resultado", "fecha"),
            show="headings",
            height=8,
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
            width=110,
            anchor="center",
        )

        self.historial_tree.column(
            "fecha",
            width=160,
            anchor="center",
        )

        self.historial_tree.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=(0, 16),
        )

        # --------------------------------------------------------------
        # Modelo 3D.
        # --------------------------------------------------------------
        mesh_panel = ttk.Frame(
            body,
            style="Card.TFrame",
        )

        mesh_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(12, 0),
        )

        ttk.Label(
            mesh_panel,
            text="Mi modelo 3D",
            style="Card.TLabel",
            font=theme.FONT_SUBHEADING,
        ).pack(
            anchor="w",
            padx=16,
            pady=(16, 8),
        )

        self.mesh_viewer = MeshViewer(mesh_panel)

        self.mesh_viewer.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=(0, 8),
        )

        ttk.Label(
            mesh_panel,
            text="Arrastra con el clic izquierdo para rotar.",
            style="CardMuted.TLabel",
        ).pack(
            anchor="w",
            padx=16,
            pady=(0, 16),
        )

    # ------------------------------------------------------------------
    def _load_data(self) -> None:
        if self.user is None:
            return

        # --------------------------------------------------------------
        # Datos personales.
        # --------------------------------------------------------------
        for label, value in [
            ("Nombre", self.user.nombre),
            ("Correo", self.user.correo),
            ("Registrado el", self.user.creado_en[:10]),
        ]:
            row = tk.Frame(
                self.info_labels_frame,
                bg=theme.COLOR_BG_ALT,
            )

            row.pack(
                fill="x",
                pady=3,
            )

            ttk.Label(
                row,
                text=f"{label}:",
                style="Card.TLabel",
                font=theme.FONT_SUBHEADING,
                width=14,
            ).pack(side="left")

            ttk.Label(
                row,
                text=value,
                style="Card.TLabel",
            ).pack(side="left")

        # --------------------------------------------------------------
        # Historial personal.
        # --------------------------------------------------------------
        for h in db.historial_ingresos(
            usuario_id=self.user.id,
            limit=20,
        ):
            fecha = (
                (h["creado_en"] or "")[:19]
                .replace("T", " ")
            )

            self.historial_tree.insert(
                "",
                "end",
                values=(
                    h["resultado"],
                    fecha,
                ),
            )

        # --------------------------------------------------------------
        # Modelo 3D.
        # --------------------------------------------------------------
        plantillas = {
            p["usuario_id"]: p
            for p in db.obtener_plantillas_activas()
        }

        plantilla = plantillas.get(self.user.id)

        if not plantilla or not plantilla["ruta_mesh_obj"]:
            self.mesh_viewer.show_error(
                "Todavía no hay un modelo 3D disponible"
            )
            return

        bundle_path = plantilla["ruta_mesh_obj"]

        try:
            from pathlib import Path

            bundle_path = db.resolve_data_path(bundle_path)

            with security.decrypted_mesh_bundle(
                bundle_path=bundle_path,
                user_id=self.user.id,
                cipher=security.BiometricCipher(),
            ) as (obj_path, texture_path):
                self.mesh_viewer.load(
                    obj_path,
                    texture_path,
                )

            # Al salir del contexto anterior, OBJ + MTL + textura
            # temporales ya fueron eliminados.

        except Exception:
            self.mesh_viewer.show_error(
                "No se pudo cargar el modelo 3D"
            )

    # ------------------------------------------------------------------
    def _volver(self) -> None:
        from .dashboard_view import DashboardView

        self.app.show_view(DashboardView)

