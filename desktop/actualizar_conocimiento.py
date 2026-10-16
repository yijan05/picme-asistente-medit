"""Importa el JSON editable a SQLite, validándolo antes de modificar la BD."""
from __future__ import annotations

import argparse
from pathlib import Path

from app.chatbot.repository import KnowledgeRepository, SEED_PATH


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualizar la base local del chatbot")
    parser.add_argument("--archivo", type=Path, default=SEED_PATH, help="JSON de conocimiento")
    parser.add_argument("--bd", type=Path, help="Base SQLite de destino (opcional)")
    args = parser.parse_args()
    repository = KnowledgeRepository(db_path=args.bd, seed_path=args.archivo)
    repository.initialize(force=True)
    print(f"Base lista: {repository.db_path}")
    print(f"Artículos: {len(repository.articles())}; fuentes: {len(repository.sources())}")


if __name__ == "__main__":
    main()
