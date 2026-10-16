"""Ejecuta las pruebas locales; --backend incluye las del servidor opcional."""
import argparse
from pathlib import Path
import unittest


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificar PicMe sin cámara")
    parser.add_argument("--backend", action="store_true", help="Incluir pruebas FastAPI/MySQL simuladas")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    for test_file in sorted((root / "tests").glob("test_*.py")):
        if not args.backend and test_file.name.startswith("test_backend"):
            continue
        suite.addTests(loader.loadTestsFromName("tests." + test_file.stem))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
