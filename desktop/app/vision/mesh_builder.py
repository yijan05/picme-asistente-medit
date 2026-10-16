"""
Construcción del modelo 3D del rostro a partir de los puntos escaneados.

Idea central (la que se discutió para esta funcionalidad): los 468 puntos
que MediaPipe ya extrae en el registro no son solo para comparar rostros;
también son directamente los VÉRTICES de una malla 3D, porque MediaPipe
publica la conectividad canónica de esa malla (ver `face_topology.py`).
Así que construir el modelo 3D no requiere un reconstructor 3D externo
(DECA, 3DDFA, etc.): se arma con lo que el sistema ya captura.

Pipeline:
  1. Vértices: los 468 puntos (x, y, z) de la foto FRONTAL del registro
     (es la que mejor cubre la cara de frente; los ángulos laterales se
     usan para el dataset de reconocimiento, no para este modelo base).
  2. Caras: la triangulación real de MediaPipe (`face_topology`).
  3. Textura (UV): dado que los propios landmarks (x, y) YA son las
     coordenadas de píxel sobre la foto frontal, se normalizan a [0, 1]
     y se usan directamente como coordenadas UV. Es decir, la textura es
     la foto original completa, y cada vértice "sabe" qué píxel de esa
     foto le corresponde porque ese píxel es, literalmente, donde
     MediaPipe lo detectó.
  4. Exportación: formato OBJ + MTL + una copia de la textura en JPEG,
     el trío de archivos estándar que cualquier visor 3D (Blender,
     three.js, MeshLab) puede abrir sin plugins.

Limitación conocida (documentar en el informe, no ocultarla): al usar
solo la foto frontal, las zonas que esa foto no ve bien (bordes muy
laterales de la cara) heredan textura estirada/poco fiel. Si se quisiera
mejorar, el siguiente paso sería fusionar texturas de más de un ángulo,
lo cual queda fuera del alcance de esta primera versión.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .face_topology import get_triangle_faces


@dataclass
class FaceMeshAsset:
    obj_path: Path
    mtl_path: Path
    texture_path: Path


def _smooth_z(landmarks: np.ndarray, faces: tuple[tuple[int, int, int], ...], iterations: int = 2) -> np.ndarray:
    """
    Suaviza la coordenada Z (la más ruidosa; MediaPipe la entrega como
    profundidad relativa, no una medición métrica real) promediando cada
    punto con sus vecinos directos en la malla. Reduce los 'bultos' que
    aparecen si se usa la z cruda tal cual.
    """
    adjacency: dict[int, set[int]] = {i: set() for i in range(len(landmarks))}
    for a, b, c in faces:
        adjacency[a].update((b, c))
        adjacency[b].update((a, c))
        adjacency[c].update((a, b))

    z = landmarks[:, 2].copy()
    for _ in range(iterations):
        new_z = z.copy()
        for idx, neighbors in adjacency.items():
            if neighbors:
                new_z[idx] = 0.5 * z[idx] + 0.5 * np.mean([z[n] for n in neighbors])
        z = new_z
    return z


def build_face_mesh(
    landmarks: np.ndarray,
    frontal_image_bgr: np.ndarray,
    output_dir: Path,
    name: str = "rostro",
) -> FaceMeshAsset:
    """
    landmarks: array (468, 3) de la captura FRONTAL (coordenadas x,y en
               píxeles de `frontal_image_bgr`, z relativa de MediaPipe).
    frontal_image_bgr: imagen (H, W, 3) en formato BGR (como la entrega OpenCV).
    output_dir: carpeta donde se escriben el .obj, .mtl y la textura.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    h, w = frontal_image_bgr.shape[:2]

    faces = get_triangle_faces()
    z_smooth = _smooth_z(landmarks, faces)

    # --- Vértices: recentrar en el origen y usar un sistema de coordenadas
    # 3D "amigable" (Y hacia arriba, como espera la mayoría de visores),
    # aunque la imagen tiene Y hacia abajo.
    xs = landmarks[:, 0]
    ys = landmarks[:, 1]
    cx, cy = xs.mean(), ys.mean()
    scale = 1.0 / max(w, h)

    vertices = np.stack(
        [
            (xs - cx) * scale,
            -(ys - cy) * scale,  # invertir Y: en imagen crece hacia abajo, en 3D queremos que crezca hacia arriba
            -z_smooth * scale,  # z de MediaPipe: negativo es "hacia la cámara"; invertimos para que la nariz sobresalga
        ],
        axis=1,
    )

    # --- UV: los mismos landmarks (x, y) en píxeles, normalizados a [0,1].
    # La V de OBJ crece hacia arriba, así que se invierte respecto a la
    # fila de píxel (que crece hacia abajo).
    us = xs / w
    vs = 1.0 - (ys / h)
    uvs = np.stack([us, vs], axis=1)

    texture_filename = f"{name}_textura.jpg"
    mtl_filename = f"{name}.mtl"
    obj_path = output_dir / f"{name}.obj"
    mtl_path = output_dir / mtl_filename
    texture_path = output_dir / texture_filename

    cv2.imwrite(str(texture_path), frontal_image_bgr)
    _write_mtl(mtl_path, texture_filename)
    _write_obj(obj_path, vertices, uvs, faces, mtl_filename)

    return FaceMeshAsset(obj_path=obj_path, mtl_path=mtl_path, texture_path=texture_path)


def _write_mtl(path: Path, texture_filename: str) -> None:
    path.write_text(
        "newmtl rostro_material\n"
        "Ka 1.000 1.000 1.000\n"
        "Kd 1.000 1.000 1.000\n"
        "Ks 0.100 0.100 0.100\n"
        "d 1.0\n"
        "illum 2\n"
        f"map_Kd {texture_filename}\n"
    )


def _write_obj(
    path: Path,
    vertices: np.ndarray,
    uvs: np.ndarray,
    faces: tuple[tuple[int, int, int], ...],
    mtl_filename: str,
) -> None:
    lines = [
        "# Modelo 3D generado por PicMe a partir de 468 puntos faciales",
        f"mtllib {mtl_filename}",
        "usemtl rostro_material",
    ]
    for v in vertices:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    for uv in uvs:
        lines.append(f"vt {uv[0]:.6f} {uv[1]:.6f}")
    # OBJ es 1-indexado, y el índice de vértice y de UV coinciden porque
    # cada punto MediaPipe tiene una única coordenada de textura asociada.
    for a, b, c in faces:
        lines.append(f"f {a + 1}/{a + 1} {b + 1}/{b + 1} {c + 1}/{c + 1}")
    path.write_text("\n".join(lines) + "\n")
