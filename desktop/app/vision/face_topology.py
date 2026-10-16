"""
Topología facial canónica de MediaPipe (468 puntos).

MediaPipe expone la conectividad de su "malla canónica" (la misma que se
usa en el proyecto original, ver Figura 1 del PGC: "Malla facial utilizada
en el sistema de detección") como datos puros de Python, sin necesidad de
descargar el modelo `.task`. Esto nos permite:

  1. Triangular la malla 3D con la topología REAL de MediaPipe (en vez de
     improvisar una triangulación genérica tipo Delaunay), lo que da un
     modelo 3D fiel a la estructura anatómica que MediaPipe reconoce.
  2. Obtener los índices exactos de los puntos de cada ojo para calcular
     el Eye Aspect Ratio (EAR) de forma consistente con la malla.

`FaceLandmarksConnections` vive en `mediapipe.tasks.python.vision` y es
pura metadata (listas de conexiones), separada del modelo de inferencia.
"""
from __future__ import annotations

from functools import lru_cache

from mediapipe.tasks.python.vision import FaceLandmarksConnections

NUM_LANDMARKS = 468

# --- Puntos EAR (Eye Aspect Ratio) ------------------------------------
# Orden P1..P6 según la formula clásica:
#   EAR = (||P2-P6|| + ||P3-P5||) / (2 * ||P1-P4||)
# (misma fórmula y misma disposición P1-P6 documentadas en el PGC, Figura 2/3)
RIGHT_EYE_EAR = (33, 160, 158, 133, 153, 144)   # ojo derecho de la persona
LEFT_EYE_EAR = (362, 385, 387, 263, 373, 380)   # ojo izquierdo de la persona


@lru_cache(maxsize=1)
def get_edges() -> tuple[tuple[int, int], ...]:
    """Todas las aristas (start, end) de la malla canónica (2556 conexiones)."""
    return tuple((c.start, c.end) for c in FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION)


@lru_cache(maxsize=1)
def _adjacency() -> tuple[frozenset[int], ...]:
    """Lista de adyacencia (por índice de vértice) construida a partir de
    todas las aristas de la tesselación."""
    adj: list[set[int]] = [set() for _ in range(NUM_LANDMARKS)]
    for a, b in get_edges():
        adj[a].add(b)
        adj[b].add(a)
    return tuple(frozenset(s) for s in adj)


@lru_cache(maxsize=1)
def get_triangle_faces() -> tuple[tuple[int, int, int], ...]:
    """
    Reconstruye la lista de triángulos (caras) de la malla a partir de las
    aristas de la tesselación.

    MediaPipe publica la tesselación como una lista plana de ARISTAS, no
    de caras. Cada arista interna es compartida por dos triángulos, así
    que el mismo par (u, v) aparece más de una vez en la lista cruda; por
    eso el primer paso es des-duplicar a aristas únicas no dirigidas. La
    forma correcta y general de recuperar los triángulos de una malla a
    partir de su grafo de aristas es la enumeración clásica de triángulos:
    para cada arista única (u, v) con u < v, cualquier vértice w > v que
    sea vecino de ambos cierra un triángulo (u, v, w). Con aristas ya
    únicas, cada triángulo real de la malla se cuenta exactamente una vez.
    """
    adj = _adjacency()
    unique_edges = {(min(a, b), max(a, b)) for a, b in get_edges() if a != b}
    faces: list[tuple[int, int, int]] = []
    for u, v in unique_edges:
        common = adj[u] & adj[v]
        for w in common:
            if w > v:
                faces.append((u, v, w))
    return tuple(faces)


@lru_cache(maxsize=1)
def get_referenced_vertices() -> frozenset[int]:
    verts: set[int] = set()
    for a, b in get_edges():
        verts.add(a)
        verts.add(b)
    return frozenset(verts)
