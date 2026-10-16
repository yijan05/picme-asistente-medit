import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.vision.face_topology import NUM_LANDMARKS, get_triangle_faces  # noqa: E402
from app.vision.mesh_builder import build_face_mesh  # noqa: E402


def _synthetic_frontal_capture(width=480, height=640):

    rng = np.random.default_rng(42)
    image = rng.integers(0, 255, size=(height, width, 3), dtype=np.uint8)

    t = np.linspace(0, 2 * np.pi, NUM_LANDMARKS)
    cx, cy = width / 2, height / 2
    x = cx + 0.35 * width * np.cos(t)
    y = cy + 0.35 * height * np.sin(t)
    z = 0.05 * width * np.sin(2 * t)
    landmarks = np.stack([x, y, z], axis=1)
    return landmarks, image


class TestMeshBuilder(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_creates_all_expected_files(self):
        landmarks, image = _synthetic_frontal_capture()
        asset = build_face_mesh(landmarks, image, self.tmpdir, name="test_user")
        self.assertTrue(asset.obj_path.exists())
        self.assertTrue(asset.mtl_path.exists())
        self.assertTrue(asset.texture_path.exists())

    def test_obj_has_correct_vertex_and_face_counts(self):
        landmarks, image = _synthetic_frontal_capture()
        asset = build_face_mesh(landmarks, image, self.tmpdir, name="test_user")
        content = asset.obj_path.read_text()

        v_lines = [l for l in content.splitlines() if l.startswith("v ")]
        vt_lines = [l for l in content.splitlines() if l.startswith("vt ")]
        f_lines = [l for l in content.splitlines() if l.startswith("f ")]

        self.assertEqual(len(v_lines), NUM_LANDMARKS)
        self.assertEqual(len(vt_lines), NUM_LANDMARKS)
        self.assertEqual(len(f_lines), len(get_triangle_faces()))

    def test_obj_face_indices_are_valid_and_1_indexed(self):
        landmarks, image = _synthetic_frontal_capture()
        asset = build_face_mesh(landmarks, image, self.tmpdir, name="test_user")
        content = asset.obj_path.read_text()

        max_idx = 0
        min_idx = 10**9
        for line in content.splitlines():
            if line.startswith("f "):
                for token in line.split()[1:]:
                    vidx = int(token.split("/")[0])
                    max_idx = max(max_idx, vidx)
                    min_idx = min(min_idx, vidx)
        self.assertGreaterEqual(min_idx, 1)  # OBJ es 1-indexado
        self.assertLessEqual(max_idx, NUM_LANDMARKS)

    def test_vertices_are_finite_numbers(self):
        landmarks, image = _synthetic_frontal_capture()
        asset = build_face_mesh(landmarks, image, self.tmpdir, name="test_user")
        content = asset.obj_path.read_text()
        for line in content.splitlines():
            if line.startswith("v "):
                coords = [float(x) for x in line.split()[1:]]
                self.assertTrue(all(np.isfinite(c) for c in coords))

    def test_mtl_references_texture_file(self):
        landmarks, image = _synthetic_frontal_capture()
        asset = build_face_mesh(landmarks, image, self.tmpdir, name="test_user")
        mtl_content = asset.mtl_path.read_text()
        self.assertIn(asset.texture_path.name, mtl_content)

    def test_texture_matches_input_image_dimensions(self):
        import cv2

        landmarks, image = _synthetic_frontal_capture(width=320, height=400)
        asset = build_face_mesh(landmarks, image, self.tmpdir, name="test_user")
        saved = cv2.imread(str(asset.texture_path))
        self.assertEqual(saved.shape[:2], (400, 320))

    def test_uv_coordinates_within_unit_range(self):
        landmarks, image = _synthetic_frontal_capture()
        asset = build_face_mesh(landmarks, image, self.tmpdir, name="test_user")
        content = asset.obj_path.read_text()
        for line in content.splitlines():
            if line.startswith("vt "):
                u, v = [float(x) for x in line.split()[1:]]
                self.assertGreaterEqual(u, -0.01)
                self.assertLessEqual(u, 1.01)
                self.assertGreaterEqual(v, -0.01)
                self.assertLessEqual(v, 1.01)


if __name__ == "__main__":
    unittest.main()
