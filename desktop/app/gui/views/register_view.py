from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ... import auth, config
from ...controllers.registration_controller import (
    RegistrationController,
    RegistrationError,
)
from .. import theme
from ..widgets.camera_view import CameraView


ERROR_MESSAGES = {
    "correo_ya_registrado": (
        "Ese correo ya tiene una cuenta registrada."
    ),
    "datos_invalidos": (
        "Revisa los datos: la contraseña debe tener "
        "al menos 8 caracteres."
    ),
    "captura_incompleta": (
        "La captura biométrica no se completó, "
        "intenta de nuevo."
    ),
    "falta_captura_frontal": (
        "No se pudo capturar la foto frontal, "
        "intenta de nuevo."
    ),
    "error_finalizando_registro": (
        "No se pudo completar el registro. "
        "Intenta de nuevo."
    ),
}


class RegisterView(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        app,
        **kwargs,
    ):
        super().__init__(
            master,
            bg=theme.COLOR_BG,
            **kwargs,
        )

        self.app = app

        self.controller = (
            RegistrationController()
        )

        # Evita procesar nuevos frames durante la
        # transición de captura a formulario.
        self._capture_complete = False

        # Evita mostrar el formulario más de una vez.
        self._form_visible = False

        self._build_layout()
        self._start_camera()

    # ------------------------------------------------------------------
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
            text="Registro biométrico",
            style="Heading.TLabel",
        ).pack(side="left")

        ttk.Button(
            header,
            text="Cancelar",
            style="Secondary.TButton",
            command=self._cancelar,
        ).pack(side="right")

        ttk.Label(
            self,
            text=(
                "Sigue las indicaciones para capturar "
                "tu rostro en distintos ángulos.\n"
                "Mantén buena iluminación y evita "
                "accesorios que cubran tu cara."
            ),
            style="Muted.TLabel",
            justify="left",
        ).pack(
            anchor="w",
            padx=32,
            pady=(0, 16),
        )

        # --------------------------------------------------------------
        # Contenedor principal de captura.
        #
        # Se guarda como atributo porque, cuando termina la captura,
        # lo retiramos temporalmente para liberar espacio visual al
        # formulario final.
        # --------------------------------------------------------------

        self.body = tk.Frame(
            self,
            bg=theme.COLOR_BG,
        )

        self.body.pack(
            fill="both",
            expand=True,
            padx=32,
            pady=(0, 16),
        )

        self.body.columnconfigure(
            0,
            weight=3,
        )

        self.body.columnconfigure(
            1,
            weight=2,
        )

        self.body.rowconfigure(
            0,
            weight=1,
        )

        # --------------------------------------------------------------
        # Cámara
        # --------------------------------------------------------------

        camera_panel = tk.Frame(
            self.body,
            bg="#000000",
        )

        camera_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 16),
            rowspan=4,
        )

        self.camera_view = CameraView(
            camera_panel,
            camera_index=config.CAMERA_INDEX,
            width=config.CAMERA_WIDTH,
            height=config.CAMERA_HEIGHT,
            on_frame=self._on_frame,
        )

        self.camera_view.pack(
            fill="both",
            expand=True,
        )

        # --------------------------------------------------------------
        # Indicador de ángulo
        # --------------------------------------------------------------

        self.angle_label_var = tk.StringVar(
            value="Preparando cámara…"
        )

        ttk.Label(
            self,
            textvariable=self.angle_label_var,
            style="Subheading.TLabel",
        ).pack(
            anchor="w",
            padx=32,
            pady=(4, 4),
        )

        self.progress = ttk.Progressbar(
            self,
            style="Horizontal.TProgressbar",
            maximum=100,
            value=0,
        )

        self.progress.pack(
            fill="x",
            padx=32,
        )

        self.status_var = tk.StringVar(
            value=""
        )

        ttk.Label(
            self,
            textvariable=self.status_var,
            style="Muted.TLabel",
        ).pack(
            anchor="w",
            padx=32,
            pady=(6, 0),
        )

        # --------------------------------------------------------------
        # Panel lateral
        # --------------------------------------------------------------

        side_panel = ttk.Frame(
            self.body,
            style="Card.TFrame",
        )

        side_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            rowspan=4,
        )

        ttk.Label(
            side_panel,
            text="Progreso",
            style="Card.TLabel",
            font=theme.FONT_SUBHEADING,
        ).pack(
            anchor="w",
            padx=16,
            pady=(16, 8),
        )

        self.angle_rows: dict[
            str,
            tk.StringVar,
        ] = {}

        for angle in config.CAPTURE_ANGLES:
            row_var = tk.StringVar(
                value=f"○  {angle['label']}"
            )

            self.angle_rows[
                angle["id"]
            ] = row_var

            ttk.Label(
                side_panel,
                textvariable=row_var,
                style="CardMuted.TLabel",
            ).pack(
                anchor="w",
                padx=16,
                pady=4,
            )

        # --------------------------------------------------------------
        # Formulario final
        #
        # Inicialmente NO se muestra.
        # --------------------------------------------------------------

        self.form_frame = ttk.Frame(
            self,
            style="Card.TFrame",
        )

        self.form_frame.columnconfigure(
            1,
            weight=1,
        )

        self._build_form(
            self.form_frame
        )

    # ------------------------------------------------------------------
    def _build_form(
        self,
        parent: tk.Widget,
    ) -> None:
        ttk.Label(
            parent,
            text="Ya casi. Completa tus datos",
            style="Card.TLabel",
            font=theme.FONT_SUBHEADING,
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(20, 16),
        )

        self.nombre_var = tk.StringVar()
        self.correo_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self._form_field(
            parent,
            "Nombre completo",
            self.nombre_var,
            row=1,
        )

        self._form_field(
            parent,
            "Correo institucional",
            self.correo_var,
            row=2,
        )

        self._form_field(
            parent,
            "Contraseña (mínimo 8 caracteres)",
            self.password_var,
            row=3,
            show="•",
        )

        self.form_error_var = tk.StringVar(
            value=""
        )

        ttk.Label(
            parent,
            textvariable=self.form_error_var,
            style="Error.TLabel",
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(4, 0),
        )

        self.submit_button = ttk.Button(
            parent,
            text="Crear mi cuenta",
            style="Accent.TButton",
            command=self._submit_form,
        )

        self.submit_button.grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(12, 20),
        )

    # ------------------------------------------------------------------
    def _form_field(
        self,
        parent: tk.Widget,
        label: str,
        var: tk.StringVar,
        row: int,
        show: str | None = None,
    ) -> None:
        ttk.Label(
            parent,
            text=label,
            style="Card.TLabel",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(20, 8),
            pady=6,
        )

        ttk.Entry(
            parent,
            textvariable=var,
            width=32,
            show=show or "",
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(0, 20),
            pady=6,
        )

    # ------------------------------------------------------------------
    def _start_camera(self) -> None:
        if not self.camera_view.is_opened():
            self.angle_label_var.set(
                "No se pudo acceder a la cámara"
            )

            self.status_var.set(
                "Revisa que esté conectada y que "
                "ningún otro programa la esté usando."
            )

            return

        current_angle = (
            self.controller.current_angle
        )

        if current_angle is None:
            return

        self.angle_label_var.set(
            current_angle["label"]
        )

        self.camera_view.start(
            interval_ms=max(
                1,
                1000
                // config.CAMERA_FPS_TARGET,
            )
        )

    # ------------------------------------------------------------------
    def _on_frame(self, frame_bgr) -> None:
        # Una vez terminada la captura, no debemos procesar ningún
        # frame adicional mientras cambiamos de pantalla.
        if self._capture_complete:
            return

        result = (
            self.controller.process_frame(
                frame_bgr
            )
        )

        # --------------------------------------------------------------
        # Sin rostro
        # --------------------------------------------------------------

        if not result.rostro_detectado:
            if result.detalle == "captura_ya_completa":
                return

            self.status_var.set(
                "No se detecta tu rostro con claridad. "
                "Acércate o mejora la iluminación."
            )

            return

        # --------------------------------------------------------------
        # Pose no válida
        # --------------------------------------------------------------

        if result.detalle == "pose_no_valida":
            self.status_var.set(
                "No se pudo determinar el ángulo. "
                "Mantén el rostro visible."
            )

            return

        # --------------------------------------------------------------
        # Ángulo incorrecto
        # --------------------------------------------------------------

        if result.detalle == "angulo_incorrecto":
            current_angle = (
                result.current_angle
            )

            if current_angle is not None:
                self.status_var.set(
                    "Aún no estás en el ángulo correcto. "
                    f"{current_angle['label']}."
                )

            # Este frame NO fue guardado.
            return

        # --------------------------------------------------------------
        # Frame válido
        # --------------------------------------------------------------

        self.status_var.set("")

        pct = min(
            100,
            int(
                100
                * result.frames_current_angle
                / result.frames_required
            ),
        )

        self.progress["value"] = pct

        # --------------------------------------------------------------
        # Ángulo completado
        # --------------------------------------------------------------

        if (
            result.angle_completed
            and result.current_angle
        ):
            previous_id = (
                self._angle_id_before(
                    result.current_angle["id"]
                )
            )

            if previous_id is not None:
                self._mark_done(
                    previous_id
                )

            self.angle_label_var.set(
                result.current_angle["label"]
            )

            self.progress["value"] = 0

        # --------------------------------------------------------------
        # Captura completa
        # --------------------------------------------------------------

        if result.is_complete:
            self._show_registration_form()

    # ------------------------------------------------------------------
    def _show_registration_form(self) -> None:
        """
        Cambia la interfaz desde la captura biométrica al formulario.

        El body de captura usa expand=True y puede consumir todo el
        espacio disponible. Por eso no basta con hacer pack() del
        formulario debajo: primero retiramos el body y liberamos ese
        espacio.
        """

        if self._capture_complete:
            return

        self._capture_complete = True

        # --------------------------------------------------------------
        # Detener la cámara ANTES de cambiar la geometría de la UI.
        # --------------------------------------------------------------

        self.camera_view.stop()

        # --------------------------------------------------------------
        # Actualizar estado visual.
        # --------------------------------------------------------------

        for angle_id in self.angle_rows:
            self._mark_done(angle_id)

        self.angle_label_var.set(
            "¡Captura completa!"
        )

        self.progress["value"] = 100

        self.status_var.set(
            "Captura completada. "
            "Ahora completa tus datos para crear la cuenta."
        )

        # --------------------------------------------------------------
        # Retirar el panel expandido de captura.
        #
        # Esto es lo importante: body deja de consumir todo el espacio
        # disponible y el formulario puede ocupar una zona visible.
        # --------------------------------------------------------------

        self.body.pack_forget()

        # --------------------------------------------------------------
        # Mostrar formulario una sola vez.
        # --------------------------------------------------------------

        if not self._form_visible:
            self.form_frame.pack(
                fill="x",
                padx=32,
                pady=(16, 24),
            )

            self._form_visible = True

            # Llevar el foco al primer campo.
            self.after(
                50,
                self._focus_first_form_field,
            )

        self.update_idletasks()

    # ------------------------------------------------------------------
    def _focus_first_form_field(self) -> None:
        """
        Intenta enfocar el primer Entry del formulario.
        No dependemos de guardar referencias adicionales al widget:
        buscamos los hijos directos del formulario.
        """

        for widget in self.form_frame.winfo_children():
            if isinstance(widget, ttk.Entry):
                widget.focus_set()
                return

    # ------------------------------------------------------------------
    @staticmethod
    def _angle_id_before(
        next_angle_id: str,
    ) -> str | None:
        ids = [
            angle["id"]
            for angle in config.CAPTURE_ANGLES
        ]

        idx = ids.index(
            next_angle_id
        )

        if idx <= 0:
            return None

        return ids[idx - 1]

    # ------------------------------------------------------------------
    def _mark_done(
        self,
        angle_id: str,
    ) -> None:
        var = self.angle_rows.get(
            angle_id
        )

        if var is not None:
            label = (
                var.get()
                .split("  ", 1)[-1]
            )

            # Evita convertir:
            # ✓  ✓  Frontal
            # en llamadas posteriores.
            if not var.get().startswith("✓"):
                var.set(
                    f"✓  {label}"
                )

    # ------------------------------------------------------------------
    def _submit_form(self) -> None:
        self.form_error_var.set("")

        self.submit_button.state(
            ["disabled"]
        )

        self.submit_button.configure(
            text=(
                "Creando cuenta y entrenando "
                "el modelo…"
            )
        )

        self.update_idletasks()

        try:
            usuario_id = (
                self.controller.finalize(
                    self.nombre_var.get(),
                    self.correo_var.get(),
                    self.password_var.get(),
                )
            )

        except RegistrationError as exc:
            code = (
                exc.args[0]
                if exc.args
                else ""
            )

            self.form_error_var.set(
                ERROR_MESSAGES.get(
                    code,
                    "No se pudo completar "
                    "el registro.",
                )
            )

            self.submit_button.state(
                ["!disabled"]
            )

            self.submit_button.configure(
                text="Crear mi cuenta"
            )

            return

        auth.login_user(
            usuario_id
        )

        from .dashboard_view import DashboardView

        self.app.show_view(
            DashboardView
        )

    # ------------------------------------------------------------------
    def _cancelar(self) -> None:
        from .home_view import HomeView

        self.app.show_view(
            HomeView
        )

    # ------------------------------------------------------------------
    def on_leave(self) -> None:
        self.camera_view.stop()