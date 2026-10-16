"""Consulta la misma base del chatbot desde el terminal, sin dependencias."""
from __future__ import annotations

import argparse
import json
import sys

from app.chatbot.rag import RagAssistant


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Chatbot local UCundinamarca y MEDIT")
    parser.add_argument("pregunta", nargs="?", help="Pregunta; sin argumento inicia conversación")
    parser.add_argument("--json", action="store_true", help="Respuesta como JSON")
    args = parser.parse_args()
    bot = RagAssistant()

    def respond(question: str) -> None:
        answer = bot.ask(question)
        if args.json:
            from dataclasses import asdict
            print(json.dumps(asdict(answer), ensure_ascii=False, indent=2))
        else:
            print("\nPicMe: " + answer.texto)
            for source in answer.fuentes:
                print(f"Fuente: {source['titulo']}\n{source['url']}")

    if args.pregunta is not None:
        respond(args.pregunta)
        return
    print(f"Asistente UCundinamarca — modo {bot.mode}; escribe salir para terminar.")
    while True:
        try:
            question = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.casefold() in {"salir", "exit", "quit"}:
            break
        respond(question)


if __name__ == "__main__":
    main()
