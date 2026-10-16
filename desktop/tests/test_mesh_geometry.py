import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.gui.widgets import mesh_geometry  # noqa: E402
from app.vision.face_topology import NUM_LANDMARKS, get_triangle_faces  # noqa: E402
from app.vision.mesh_builder import build_face_mesh  # noqa: E402


def _synthetic_frontal_capture(width=200, height=240):
    rng = np.random.default_rng(3)
    image = rng.integers(0, 255, size=(height, width, 3), dtype=np.uint8)
    t = np.linspace(0, 2 * np.pi, NUM_LANDMARKS)
    cx, cy = width / 2, height / 2
    x = cx + 0.35 * width * np.cos(t)
    y = cy + 0.35 * height * np.sin(t)
    z = 0.05 * width * np.sin(2 * t)
    landmarks = np.stack([x, y, z], axis=1)
    return landmarks, image


class TestMeshGeometry(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        landmarks, image = _synthetic_frontal_capture()
        self.asset = build_face_mesh(landmarks, image, self.tmpdir, name="visor_test")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_parse_obj_roundtrip_matches_original_counts(self):
        vertices, uvs, faces = mesh_geometry.parse_obj(self.asset.obj_path)
        self.assertEqual(vertices.shape, (NUM_LANDMARKS, 3))
        self.assertEqual(uvs.shape, (NUM_LANDMARKS, 2))
        self.assertEqual(len(faces), len(get_triangle_faces()))

    def test_parsed_face_indices_are_valid(self):
        vertices, uvs, faces = mesh_geometry.parse_obj(self.asset.obj_path)
        for a, b, c in faces:
            self.assertTrue(0 <= a < NUM_LANDMARKS)
            self.assertTrue(0 <= b < NUM_LANDMARKS)
            self.assertTrue(0 <= c < NUM_LANDMARKS)

    def test_face_colors_have_one_entry_per_face(self):
        vertices, uvs, faces = mesh_geometry.parse_obj(self.asset.obj_path)
        colors = mesh_geometry.face_colors_from_texture(uvs, faces, self.asset.texture_path)
        self.assertIsNotNone(colors)
        self.assertEqual(len(colors), len(faces))
        for r, g, b, a in colors:
            for channel in (r, g, b, a):
                self.assertGreaterEqual(channel, 0.0)
                self.assertLessEqual(channel, 1.0)

    def test_face_colors_none_when_texture_missing(self):
        vertices, uvs, faces = mesh_geometry.parse_obj(self.asset.obj_path)
        colors = mesh_geometry.face_colors_from_texture(uvs, faces, Path("/no/existe/textura.jpg"))
        self.assertIsNone(colors)

    def test_face_colors_none_when_texture_path_is_none(self):
        vertices, uvs, faces = mesh_geometry.parse_obj(self.asset.obj_path)
        colors = mesh_geometry.face_colors_from_texture(uvs, faces, None)
        self.assertIsNone(colors)

    def test_bounding_sphere_contains_all_vertices(self):
        vertices, _, _ = mesh_geometry.parse_obj(self.asset.obj_path)
        center, radius = mesh_geometry.bounding_sphere(vertices)
        distances = np.linalg.norm(vertices - center, axis=1)
        self.assertLessEqual(distances.max(), radius * 1.01)  # pequeño margen numérico

    def test_build_poly3dcollection_with_real_matplotlib(self):
        """Ejercita la construcción real del Poly3DCollection (con
        matplotlib de verdad, backend 'Agg' sin necesidad de Tkinter) tal
        como la usa mesh_viewer.MeshViewer.load(), para detectar cualquier
        uso incorrecto de la API de matplotlib sin depender de una
        pantalla."""
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib.figure import Figure

        vertices, uvs, faces = mesh_geometry.parse_obj(self.asset.obj_path)
        colors = mesh_geometry.face_colors_from_texture(uvs, faces, self.asset.texture_path)

        fig = Figure(figsize=(2, 2))
        ax = fig.add_subplot(111, projection="3d")
        poly = mesh_geometry.build_poly3dcollection(ax, vertices, faces, colors)

        self.assertEqual(len(ax.collections), 1)
        face_colors = poly.get_facecolor()
        self.assertEqual(face_colors.shape[0], len(faces))

        mesh_geometry.fit_view(ax, vertices)
        # Si algo en fit_view fallara (p. ej. un método inexistente en la
        # versión de matplotlib instalada), esta línea lanzaría antes de
        # llegar aquí.
        fig.canvas.draw()

    def test_build_poly3dcollection_default_color_when_no_texture(self):
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib.figure import Figure

        vertices, uvs, faces = mesh_geometry.parse_obj(self.asset.obj_path)
        fig = Figure(figsize=(2, 2))
        ax = fig.add_subplot(111, projection="3d")
        poly = mesh_geometry.build_poly3dcollection(ax, vertices, faces, colors=None)
        face_colors = poly.get_facecolor()
        self.assertEqual(face_colors.shape[0], len(faces))

    def test_sampled_color_matches_known_pixel(self):
        """Verifica el mapeo UV->píxel con un caso exacto y controlado
        (no solo que 'no truene'): coloca una textura de un solo color
        sólido y confirma que el color muestreado es ese color."""
        solid_color_bgr = np.zeros((50, 50, 3), dtype=np.uint8)
        solid_color_bgr[:, :] = (10, 20, 200)  # B, G, R
        texture_path = self.tmpdir / "solida.png"
        import cv2

        cv2.imwrite(str(texture_path), solid_color_bgr)

        uvs = np.array([[0.5, 0.5], [0.2, 0.8], [0.9, 0.1]])
        faces = [(0, 1, 2)]
        colors = mesh_geometry.face_colors_from_texture(uvs, faces, texture_path)
        r, g, b, a = colors[0]
        self.assertAlmostEqual(r, 200 / 255, places=2)
        self.assertAlmostEqual(g, 20 / 255, places=2)
        self.assertAlmostEqual(b, 10 / 255, places=2)


if __name__ == "__main__":
    unittest.main()
