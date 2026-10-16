"""RAG léxico sobre SQLite + LLM opcional. El modo real siempre se identifica."""
from __future__ import annotations

import os
from pathlib import Path

from .engine import Chatbot, Respuesta, ORDINALS, normalize, tokens
from .llm import DEFAULT_MODEL, GeminiClient, LLMError, load_environment


class RagAssistant:
    MAX_QUESTION_LENGTH = Chatbot.MAX_QUESTION_LENGTH

    def __init__(self, db_path: Path | None = None, seed_path: Path | None = None,
                 *, provider=None, mode: str | None = None):
        load_environment()
        self.local = Chatbot(db_path, seed_path)
        self.repository = self.local.repository
        self.documents = self.local.documents
        self.history: list[dict] = []
        self.previous_ids: list[str] = []
        selected_mode = mode or os.getenv("PICME_CHAT_MODE", "auto")
        key = os.getenv("GEMINI_API_KEY", "")
        self.provider = provider
        if self.provider is None and key and selected_mode != "local":
            self.provider = GeminiClient(key, os.getenv("GEMINI_MODEL", DEFAULT_MODEL))
        self.mode = "gemini" if self.provider is not None and selected_mode != "local" else "local"

    def reset(self) -> None:
        self.local.reset()
        self.history.clear()
        self.previous_ids.clear()

    def retrieve(self, question: str, direct: Respuesta) -> list[dict]:
        normalized = normalize(question)
        words = normalized.split()
        selected = []
        # Admite comparaciones entre varios principios; no confunde una fecha con un número.
        if any(w in {"principio", "principios", "punto", "puntos", "principle", "principles"} for w in words):
            numbers = [int(w) if w.isdigit() else ORDINALS[w] for w in words if w.isdigit() or w in ORDINALS]
            if len(numbers) > 1:
                selected.extend(f"principio_{n:02d}" for n in numbers if 1 <= n <= 12)
        if direct.articulo_id:
            selected.append(direct.articulo_id)
        if direct.articulo_id == "declaracion_reflexion":
            # Las preguntas personales necesitan los compromisos completos,
            # no una coincidencia genérica con el título de un libro del MEDIT.
            selected.append("declaracion_completa")
            return [self.local.by_id[id] for id in selected if id in self.local.by_id]
        if normalized in {"un ejemplo", "dame un ejemplo", "mas sencillo", "explicalo", "compare them", "an example"}:
            selected.extend(self.previous_ids)
        query = tokens(question)
        weighted = []
        for document in self.documents:
            dt = tokens(document["titulo"] + " " + document["palabras_clave"] + " " + " ".join(document["preguntas"]))
            shared = query & dt
            score = sum(self.local.weights.get(t, 1) for t in shared) / max(
                sum(self.local.weights.get(t, 2) for t in query), 1)
            if score >= 0.45:
                weighted.append((score, document["id"]))
        selected.extend(id for score, id in sorted(weighted, reverse=True))
        selected = list(dict.fromkeys(selected))[:4]
        return [self.local.by_id[id] for id in selected if id in self.local.by_id]

    def ask(self, question: str) -> Respuesta:
        direct = self.local.ask(question)
        if self.mode != "gemini" or not isinstance(question, str) or not question.strip() or len(question) > self.MAX_QUESTION_LENGTH:
            return direct
        documents = self.retrieve(question, direct)
        if not documents:
            return direct
        try:
            answer, ids = self.provider.generate(question, documents, self.history)
        except LLMError as exc:
            direct.texto = f"{exc} Te muestro la consulta local disponible:\n\n{direct.texto}"
            direct.modo = "local_respaldo"
            return direct
        by_id = {d["id"]: d for d in documents}
        sources = []
        for id in ids:
            document = by_id[id]
            if document["fuente_url"] not in {s["url"] for s in sources}:
                sources.append({"titulo": document["fuente_titulo"], "url": document["fuente_url"],
                                "consultada_el": document["consultada_el"]})
        self.history.append({"pregunta": question, "respuesta": answer})
        self.history = self.history[-4:]
        self.previous_ids = ids
        return Respuesta(answer, bool(ids), ids[0] if ids else None, sources,
                         modo="gemini", modelo=getattr(self.provider, "model", "gemini"), llm_usado=True)
