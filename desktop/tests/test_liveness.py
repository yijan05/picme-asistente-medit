import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.vision import face_topology as topo  # noqa: E402
from app.vision.liveness import BlinkDetector, compute_ear  # noqa: E402


def _make_landmarks(eye_state: str) -> np.ndarray:
    """
    Construye un array (468,3) de landmarks sintéticos donde ambos ojos
    (usando los índices reales RIGHT_EYE_EAR / LEFT_EYE_EAR) tienen una
    geometría de "ojo abierto" o "ojo cerrado" conocida, para poder
    predecir el EAR exacto sin depender de una cámara real.

    Orden P1..P6 esperado por compute_ear: (corner1, top1, top2, corner2, bottom2, bottom1)
    """
    lm = np.zeros((topo.NUM_LANDMARKS, 3), dtype=np.float64)

    if eye_state == "open":
        # horizontal = 3 (P1 a P4), vertical (P2-P6)=(P3-P5)=2 -> EAR = 4/6 ≈ 0.667
        offsets = np.array(
            [[0, 0, 0], [1, 1, 0], [2, 1, 0], [3, 0, 0], [2, -1, 0], [1, -1, 0]], dtype=np.float64
        )
    elif eye_state == "closed":
        # misma horizontal=3, vertical casi nula -> EAR ≈ 0.1/6 ≈ 0.033 (< umbral 0.21)
        offsets = np.array(
            [[0, 0, 0], [1, 0.05, 0], [2, 0.05, 0], [3, 0, 0], [2, -0.05, 0], [1, -0.05, 0]],
            dtype=np.float64,
        )
    else:
        raise ValueError(eye_state)

    for idx_group in (topo.RIGHT_EYE_EAR, topo.LEFT_EYE_EAR):
        for i, idx in enumerate(idx_group):
            lm[idx] = offsets[i]

    return lm


class TestLiveness(unittest.TestCase):
    def test_ear_open_eye_is_high(self):
        lm = _make_landmarks("open")
        ear = compute_ear(lm)
        self.assertAlmostEqual(ear, 4 / 6, places=3)

    def test_ear_closed_eye_is_low(self):
        lm = _make_landmarks("closed")
        ear = compute_ear(lm)
        self.assertLess(ear, 0.21)
        self.assertAlmostEqual(ear, 0.2 / 6, places=3)

    def test_blink_detector_counts_one_blink(self):
        detector = BlinkDetector()
        sequence = ["open", "open", "closed", "closed", "open", "open"]
        for state in sequence:
            detector.update(_make_landmarks(state))
        self.assertEqual(detector.blink_count, 1)

    def test_sustained_closure_not_counted_until_recovery(self):
        detector = BlinkDetector()
        for _ in range(10):
            detector.update(_make_landmarks("closed"))
        # Los ojos siguen cerrados: todavía no debe contarse ningún parpadeo
        self.assertEqual(detector.blink_count, 0)
        # Al recuperarse, ahí sí se cuenta el parpadeo (una sola vez)
        detector.update(_make_landmarks("open"))
        self.assertEqual(detector.blink_count, 1)

    def test_single_frame_dip_below_consec_frames_not_counted(self):
        # consec_frames por defecto = 2; un solo frame cerrado no debe bastar
        detector = BlinkDetector(consec_frames=2)
        detector.update(_make_landmarks("open"))
        detector.update(_make_landmarks("closed"))  # solo 1 frame por debajo
        detector.update(_make_landmarks("open"))
        self.assertEqual(detector.blink_count, 0)

    def test_multiple_blinks_counted(self):
        detector = BlinkDetector()
        sequence = ["open"] * 2 + ["closed"] * 2 + ["open"] * 3 + ["closed"] * 2 + ["open"] * 2
        for state in sequence:
            detector.update(_make_landmarks(state))
        self.assertEqual(detector.blink_count, 2)

    def test_reset(self):
        detector = BlinkDetector()
        for state in ["open", "closed", "closed", "open"]:
            detector.update(_make_landmarks(state))
        self.assertEqual(detector.blink_count, 1)
        detector.reset()
        self.assertEqual(detector.blink_count, 0)
        self.assertIsNone(detector.last_ear)


if __name__ == "__main__":
    unittest.main()
