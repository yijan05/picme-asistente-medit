"""Publica el historial entregado en un repositorio GitHub vacío creado por ti."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description="Publicar PicMe en tu repositorio GitHub")
    parser.add_argument("--repo", help="URL HTTPS del repositorio vacío que creaste")
    parser.add_argument("--destino", type=Path, help="Carpeta nueva para el clon")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    git = shutil.which("git")
    if not git:
        print("Instala Git para Windows desde https://git-scm.com/downloads/win y vuelve a intentar.")
        return 1
    repo = (args.repo or input("URL HTTPS de tu repositorio GitHub público: ")).strip()
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?", repo):
        print("Usa una URL HTTPS de GitHub con propietario y repositorio, sin credenciales.")
        return 1
    bundle = root / "historial.bundle"
    if not bundle.exists():
        print("No se encontró historial.bundle. Sigue los comandos manuales de la documentación.")
        return 1
    destination = (args.destino or root.parent / "PicMe_GitHub").resolve()
    if destination.exists():
        result = subprocess.run([git, "-C", str(destination), "remote", "get-url", "origin"], capture_output=True, text=True)
        if result.returncode or result.stdout.strip() != repo:
            print("La carpeta de destino ya existe y no corresponde a ese repositorio. Usa --destino con una carpeta nueva.")
            return 1
    else:
        subprocess.run([git, "clone", str(bundle), str(destination)], check=True)
        subprocess.run([git, "-C", str(destination), "remote", "set-url", "origin", repo], check=True)
    branch = subprocess.check_output([git, "-C", str(destination), "branch", "--show-current"], text=True).strip()
    subprocess.run([git, "-C", str(destination), "push", "-u", "origin", branch], check=True)
    print("Fuente publicada. Verifica en GitHub que el repositorio sea público.")
    print("Clon de trabajo:", destination)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError:
        print("Git no terminó la publicación. Revisa la autenticación y que el repositorio esté vacío. No se hizo un push forzado.")
        raise SystemExit(1)
