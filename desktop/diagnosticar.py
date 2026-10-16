"""Diagnóstico ejecutable en el PC: paquetes, SQLite, modelo y cámara opcional."""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import struct
import sys
import tempfile

from app import config, db


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico local de PicMe")
    parser.add_argument("--camara", action="store_true", help="Abrir la cámara y leer un frame")
    parser.add_argument("--modelo", action="store_true", help="Cargar el modelo real de MediaPipe")
    parser.add_argument("--solo-chatbot", action="store_true", help="Verificar solo los requisitos del chat")
    args = parser.parse_args()
    issues = []
    print("PICME - DIAGNÓSTICO\n")
    print("Python:", sys.version.split()[0], "|", struct.calcsize("P") * 8, "bits")
    print("Intérprete:", sys.executable)
    print("Proyecto:", config.BASE_DIR)
    if not ((3, 10) <= sys.version_info[:2] <= (3, 12)):
        issues.append("Usa Python 3.10, 3.11 o 3.12.")
    if struct.calcsize("P") != 8:
        issues.append("Usa Python de 64 bits para el motor biométrico.")
    modules = ["tkinter", "sqlite3"]
    if not args.solo_chatbot:
        modules += ["numpy", "PIL", "matplotlib", "cv2", "mediapipe", "sklearn", "cryptography", "werkzeug"]
    loaded = {}
    for name in modules:
        try:
            module = loaded[name] = importlib.import_module(name)
            print("OK", name, getattr(module, "__version__", ""))
        except Exception as exc:
            print("FALLÓ", name, str(exc))
            issues.append(f"Revisar {name}: ejecuta INSTALAR_WINDOWS.bat.")
    try:
        from app.chatbot import Chatbot
        bot = Chatbot()
        answer = bot.ask("Explícame el principio 6")
        assert answer.articulo_id == "principio_06"
        print("OK chatbot:", len(bot.documents), "artículos;", len(bot.repository.sources()), "fuentes")
        print("BD del chatbot:", bot.repository.db_path)
    except Exception as exc:
        issues.append(f"Base del chatbot: {exc}")
    try:
        config.ensure_directories()
        with tempfile.NamedTemporaryFile(dir=config.DATA_DIR):
            pass
        db.init_db()
        print("OK base biométrica y permisos de escritura")
        for row in db.obtener_plantillas_activas():
            for key in ("ruta_svm", "ruta_mesh_obj"):
                if row[key] and not db.resolve_data_path(row[key]).exists():
                    issues.append(f"No se encuentra un archivo biométrico del usuario {row['usuario_id']}.")
    except Exception as exc:
        issues.append(f"Datos locales: {exc}")
    if not args.solo_chatbot:
        if config.FACE_LANDMARKER_MODEL_PATH.exists():
            print("OK modelo de MediaPipe presente")
        else:
            issues.append("Falta el modelo: ejecuta python download_model.py.")
    if args.modelo:
        try:
            import numpy as np
            from app.vision.landmark_extractor import FaceLandmarkExtractor
            extractor = FaceLandmarkExtractor()
            try:
                result = extractor.extract(np.zeros((480, 640, 3), dtype=np.uint8))
                print("OK modelo real cargado y ejecutado; imagen vacía:", result)
            finally:
                extractor.close()
        except Exception as exc:
            issues.append(f"Carga del modelo: {exc}")
    if args.camara:
        cap = None
        try:
            import cv2
            cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(config.CAMERA_INDEX)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(config.CAMERA_INDEX)
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("No se pudo leer la cámara. Cierra Teams/Zoom y revisa los permisos de Windows.")
            print("OK cámara:", frame.shape[1], "x", frame.shape[0])
        except Exception as exc:
            issues.append(str(exc))
        finally:
            if cap is not None:
                cap.release()
    print()
    if issues:
        for issue in issues:
            print("REVISAR:", issue)
        return 1
    print("Diagnóstico correcto. La prueba de cámara solo se ejecuta con --camara.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
