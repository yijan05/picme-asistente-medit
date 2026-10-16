"""
Lógica de geometría para el visor 3D, separada deliberadamente de
`mesh_viewer.py` (que sí depende de Tkinter/matplotlib) para poder
probarla sin necesitar una interfaz gráfica.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def parse_obj(obj_path: Path) -> tuple[np.ndarray, np.ndarray, list[tuple[int, int, int]]]:
    """Lee un .obj en el mismo formato exacto que escribe
    `app.vision.mesh_builder._write_obj` (v / vt / f con índices
    1-indexados tipo 'a/a b/b c/c')."""
    vertices: list[list[float]] = []
    uvs: list[list[float]] = []
    faces: list[tuple[int, int, int]] = []

    for line in Path(obj_path).read_text().splitlines():
        if line.startswith("v "):
            vertices.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("vt "):
            uvs.append([float(x) for x in line.split()[1:3]])
        elif line.startswith("f "):
            idx = [int(tok.split("/")[0]) - 1 for tok in line.split()[1:4]]
            faces.append((idx[0], idx[1], idx[2]))

    return np.array(vertices, dtype=float), np.array(uvs, dtype=float), faces


def face_colors_from_texture(
    uvs: np.ndarray, faces: list[tuple[int, int, int]], texture_path: Optional[Path]
) -> Optional[list[tuple[float, float, float, float]]]:
    """
    Para cada triángulo, calcula su UV promedio y toma el color de la
    textura en ese punto. Es una aproximación (no un mapeo de textura
    fotográfico real), pero da un modelo con los colores reales de la
    persona sin necesitar un motor de renderizado 3D completo.
    """
    if texture_path is None or not Path(texture_path).exists():
        return None
    image_bgr = cv2.imread(str(texture_path))
    if image_bgr is None:
        return None

    h, w = image_bgr.shape[:2]
    colors = []
    for a, b, c in faces:
        u, v = uvs[[a, b, c]].mean(axis=0)
        # La V se guardó invertida respecto a la fila de píxel (ver
        # mesh_builder._write_obj: vs = 1 - y/h); se deshace igual acá.
        px = int(np.clip(u * (w - 1), 0, w - 1))
        py = int(np.clip((1.0 - v) * (h - 1), 0, h - 1))
        b_, g_, r_ = image_bgr[py, px]
        colors.append((r_ / 255.0, g_ / 255.0, b_ / 255.0, 1.0))
    return colors


def bounding_sphere(vertices: np.ndarray) -> tuple[np.ndarray, float]:
    """Centro y radio de una esfera que envuelve todos los vértices (con
    un pequeño margen), útil para encuadrar la cámara del visor."""
    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    center = (mins + maxs) / 2
    radius = max((maxs - mins).max() / 2, 1e-6) * 1.15
    return center, radius


def build_poly3dcollection(ax, vertices: np.ndarray, faces, colors=None, default_color: str = "#C9A98C"):
    """
    Construye y añade a `ax` (un Axes3D de matplotlib) la malla como un
    Poly3DCollection coloreado por triángulo. No depende de Tkinter: solo
    de matplotlib, así que se puede probar con el backend 'Agg' (sin
    display) — es la parte de `mesh_viewer.MeshViewer.load()` que
    realmente construye la geometría 3D.
    """
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    triangles = [vertices[list(f)] for f in faces]
    poly = Poly3DCollection(triangles)
    poly.set_facecolor(colors if colors is not None else default_color)
    poly.set_edgecolor((0.0, 0.0, 0.0, 0.08))
    ax.add_collection3d(poly)
    return poly


def fit_view(ax, vertices: np.ndarray, elev: float = 10, azim: float = -80) -> None:
    """Encuadra la cámara del Axes3D para que se vea toda la malla, y fija
    un ángulo de vista inicial razonable."""
    center, radius = bounding_sphere(vertices)
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)
    try:
        ax.set_box_aspect([1, 1, 1])
    except AttributeError:
        pass  # versiones muy antiguas de matplotlib no tienen set_box_aspect
    ax.view_init(elev=elev, azim=azim)
