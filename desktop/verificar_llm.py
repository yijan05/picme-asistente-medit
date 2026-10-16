"""Prueba real de Gemini. Falla si solo respondió el modo local."""
from app.chatbot.rag import RagAssistant


def main() -> int:
    bot = RagAssistant()
    if bot.mode != "gemini":
        print("PENDIENTE: configura GEMINI_API_KEY en .env para verificar el LLM real.")
        return 1
    answer = bot.ask("¿Cuáles son los cuatro ejes del MEDIT? Explica en una frase.")
    print("Modo de la respuesta:", answer.modo)
    print("Modelo:", answer.modelo or "No usado")
    print(answer.texto)
    for source in answer.fuentes:
        print("Fuente:", source["url"])
    if not answer.llm_usado:
        print("NO VERIFICADO: la respuesta anterior no fue generada por el LLM.")
        return 1
    print("VERIFICADO: hubo una respuesta del proveedor LLM. Revisa su exactitud con la fuente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
