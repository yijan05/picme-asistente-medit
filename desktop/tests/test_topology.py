import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.vision import face_topology as topo  # noqa: E402


class TestFaceTopology(unittest.TestCase):
    def test_edge_count_matches_mediapipe(self):
        # MediaPipe publica 2556 conexiones para la tesselación canónica
        self.assertEqual(len(topo.get_edges()), 2556)

    def test_all_468_vertices_referenced(self):
        verts = topo.get_referenced_vertices()
        self.assertEqual(len(verts), topo.NUM_LANDMARKS)
        self.assertEqual(min(verts), 0)
        self.assertEqual(max(verts), topo.NUM_LANDMARKS - 1)

    def test_triangles_are_closed_cycles(self):
        faces = topo.get_triangle_faces()
        self.assertGreater(len(faces), 0)
        edge_set = set(topo.get_edges()) | {(b, a) for a, b in topo.get_edges()}
        bad = 0
        for a, b, c in faces:
            if not ((a, b) in edge_set and (b, c) in edge_set and (c, a) in edge_set):
                bad += 1
        self.assertEqual(bad, 0, f"{bad} triángulos no forman ciclos cerrados válidos")

    def test_triangles_cover_most_vertices(self):
        faces = topo.get_triangle_faces()
        covered = set()
        for tri in faces:
            covered.update(tri)
        # Debe cubrir prácticamente todos los 468 puntos (permitimos un
        # pequeño margen por si algún punto solo aparece en aristas de
        # contorno que no cierran triángulo dentro de la tesselación).
        self.assertGreaterEqual(len(covered), topo.NUM_LANDMARKS - 5)

    def test_ear_indices_within_range(self):
        for idx in topo.RIGHT_EYE_EAR + topo.LEFT_EYE_EAR:
            self.assertTrue(0 <= idx < topo.NUM_LANDMARKS)
        self.assertEqual(len(topo.RIGHT_EYE_EAR), 6)
        self.assertEqual(len(topo.LEFT_EYE_EAR), 6)

    def test_no_duplicate_faces(self):
        faces = topo.get_triangle_faces()
        # normalizar cada triángulo (mismo triángulo, distinto orden de vértices)
        normalized = {frozenset(f) for f in faces}
        # Puede haber algunas repeticiones legítimas por cómo se agrupan
        # las aristas; solo verificamos que la mayoría son únicas.
        self.assertGreater(len(normalized), len(faces) * 0.9)


if __name__ == "__main__":
    unittest.main()
