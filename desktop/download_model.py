from __future__ import annotations

import sys

from app import model_downloader


def _print_progress(downloaded: int, total: int) -> None:
    if total > 0:
        pct = downloaded * 100 // total
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        print(f"\rDescargando... {pct}%  ({mb_downloaded:.1f} / {mb_total:.1f} MB)", end="", flush=True)
    else:
        mb_downloaded = downloaded / (1024 * 1024)
        print(f"\rDescargando... {mb_downloaded:.1f} MB", end="", flush=True)


def main() -> int:
    if model_downloader.is_model_downloaded():
        print(f"El modelo ya existe en {model_downloader.config.FACE_LANDMARKER_MODEL_PATH} — no se vuelve a descargar.")
        print("(Si quieres forzar la descarga de nuevo, borra ese archivo y vuelve a correr este script.)")
        return 0

    print("Descargando modelo de MediaPipe FaceLandmarker...")
    try:
        path = model_downloader.download_model(progress_callback=_print_progress)
    except model_downloader.ModelDownloadError as exc:
        print()
        print(f"ERROR: {exc}")
        print()
        print("Si el problema persiste, descarga el archivo manualmente desde:")
        print(f"  {model_downloader.MODEL_URL}")
        print(f"y guárdalo en: {model_downloader.config.FACE_LANDMARKER_MODEL_PATH}")
        return 1

    print()
    print(f"Listo: modelo guardado en {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
