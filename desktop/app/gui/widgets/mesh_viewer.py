"""
Visor 3D del modelo .obj generado en el registro, embebido directamente
en la ventana (sin depender de un navegador ni de OpenGL).

La lógica de geometría (parseo del .obj y muestreo de color de la
textura) vive en `mesh_geometry.py`, que no depende de Tkinter/matplotlib
y por eso se puede probar de forma aislada; este archivo solo se encarga
de dibujar esos datos y de la interacción de arrastrar-para-rotar.
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .. import theme
from . import mesh_geometry


class MeshViewer(tk.Frame):
    """Widget embebido con arrastrar-para-rotar (botón izquierdo)."""

    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, bg=theme.COLOR_BG, **kwargs)

        self.figure = Figure(figsize=(4, 4), dpi=100, facecolor=theme.COLOR_BG)
        self.ax = self.figure.add_subplot(111, projection="3d")
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self._drag_last: Optional[tuple[float, float]] = None
        self.canvas.mpl_connect("button_press_event", self._on_press)
        self.canvas.mpl_connect("button_release_event", self._on_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_drag)

    def _style_axes(self) -> None:
        self.ax.set_facecolor(theme.COLOR_BG)
        self.ax.set_axis_off()

    def show_error(self, message: str) -> None:
        self.ax.clear()
        self._style_axes()
        self.ax.text2D(0.5, 0.5, message, ha="center", va="center", transform=self.ax.transAxes)
        self.canvas.draw()

    def load(self, obj_path: Path, texture_path: Optional[Path] = None) -> None:
        vertices, uvs, faces = mesh_geometry.parse_obj(obj_path)
        if len(vertices) == 0 or len(faces) == 0:
            self.show_error("No se pudo leer el modelo 3D")
            return

        colors = mesh_geometry.face_colors_from_texture(uvs, faces, texture_path)

        self.ax.clear()
        self._style_axes()
        mesh_geometry.build_poly3dcollection(self.ax, vertices, faces, colors)
        mesh_geometry.fit_view(self.ax, vertices)
        self.canvas.draw()

    # --- interacción: arrastrar para rotar --------------------------------
    def _on_press(self, event) -> None:
        if event.button == 1 and event.xdata is not None:
            self._drag_last = (event.x, event.y)

    def _on_release(self, event) -> None:
        self._drag_last = None

    def _on_drag(self, event) -> None:
        if self._drag_last is None or event.x is None:
            return
        dx = event.x - self._drag_last[0]
        dy = event.y - self._drag_last[1]
        self._drag_last = (event.x, event.y)
        self.ax.view_init(elev=self.ax.elev - dy * 0.4, azim=self.ax.azim + dx * 0.4)
        self.canvas.draw_idle()
