"""Instalador local reproducible; crea .venv sin modificar el Python global."""
from __future__ import annotations

import argparse
from pathlib import Path
import struct
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preparar PicMe para Windows")
    parser.add_argument("--solo-chatbot", action="store_true", help="No descargar paquetes biométricos")
    args = parser.parse_args()
    if sys.platform != "win32":
        print("En Linux/macOS usa un entorno virtual e instala requirements.txt. Este instalador es para Windows.")
        return 1
    if not ((3, 10) <= sys.version_info[:2] <= (3, 12)) or struct.calcsize("P") != 8:
        print("PicMe necesita Python 3.10, 3.11 o 3.12 de 64 bits. Se recomienda Python 3.10.")
        print("Instálalo desde https://www.python.org/downloads/windows/ incluyendo Tcl/Tk y el lanzador py.")
        return 1
    try:
        import tkinter
    except ImportError:
        print("Falta Tcl/Tk. Modifica la instalación de Python y marca Tcl/Tk and IDLE.")
        return 1
    environment = ROOT / ".venv"
    python = environment / "Scripts" / "python.exe"
    if not python.exists():
        print("Creando un entorno propio en .venv...", flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    else:
        # Reutilizar solo un entorno que realmente pueda ejecutar este proyecto.
        probe = subprocess.run([str(python), "-c",
            "import sys,struct;sys.exit(0 if (3,10)<=sys.version_info[:2]<=(3,12) and struct.calcsize('P')==8 else 1)"],
            capture_output=True)
        if probe.returncode:
            print("El entorno .venv no es compatible. Renombra esa carpeta a .venv_anterior y vuelve a instalar.")
            return 1
    if not args.solo_chatbot:
        print("Instalando las dependencias de reconocimiento facial. Requiere Internet...", flush=True)
        run(str(python), "-m", "pip", "install", "--upgrade", "pip")
        run(str(python), "-m", "pip", "install", "-r", "requirements.txt")
        run(str(python), "-m", "pip", "check")
        if not (ROOT / "models" / "face_landmarker.task").exists():
            run(str(python), "download_model.py")
    run(str(python), "actualizar_conocimiento.py")
    print("\nListo. Abre INICIAR_PICME.bat o SOLO_CHATBOT.bat.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"\nNo se terminó la instalación: {exc}")
        print("Verifica tu conexión y vuelve a ejecutar INSTALAR_WINDOWS.bat.")
        raise SystemExit(1)
