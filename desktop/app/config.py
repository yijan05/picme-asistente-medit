from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MESH_DIR = DATA_DIR / "meshes"
DB_PATH = DATA_DIR / "picme.db"


BACKEND_URL = os.getenv(
    "PICME_BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


FACE_LANDMARKER_MODEL_PATH = (
    MODELS_DIR / "face_landmarker.task"
)


CAMERA_INDEX = int(os.getenv("PICME_CAMERA_INDEX", "0"))
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS_TARGET = 24


CAPTURE_ANGLES = [
    {
        "id": "frontal",
        "label": "Mira al frente",
        "yaw_range": (-10, 10),
    },
    {
        "id": "izq_45",
        "label": "Gira levemente a tu izquierda",
        "yaw_range": (15, 45),
    },
    {
        "id": "der_45",
        "label": "Gira levemente a tu derecha",
        "yaw_range": (-45, -15),
    },
    {
        "id": "izq_90",
        "label": "Perfil izquierdo completo",
        "yaw_range": (45, 90),
    },
    {
        "id": "der_90",
        "label": "Perfil derecho completo",
        "yaw_range": (-90, -45),
    },
]

FRAMES_PER_ANGLE = 8

CAPTURE_YAW_TOLERANCE = 5.0


EAR_BLINK_THRESHOLD = 0.21
EAR_CONSEC_FRAMES = 2
BLINKS_REQUIRED_LOGIN = 1
LOGIN_MAX_FRAMES = 150


LANDMARK_COUNT = 468
FEATURE_DIM = LANDMARK_COUNT * 3

SVM_DECISION_MARGIN = 0.05
SVM_NU = 0.1
SVM_GAMMA = "scale"


PCA_MAX_COMPONENTS = 30
MIN_TRAINING_SAMPLES = 8


ENCRYPTION_KEY_ENV_VAR = "PICME_ENCRYPTION_KEY"


def ensure_directories() -> None:
    """
    Crea los directorios de datos si todavía no existen.
    """
    for directory in (
        DATA_DIR,
        MODELS_DIR,
        MESH_DIR,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )
