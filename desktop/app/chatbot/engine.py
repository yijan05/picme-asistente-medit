"""Recupera respuestas verificables de SQLite; no genera datos institucionales."""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from difflib import get_close_matches
from pathlib import Path

from .repository import KnowledgeRepository


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", text))


STOP = set("a al algo ante aqui asi cual cuales como con conoce conocer de del dime el ella ellas ellos en es esa esas ese eso esta estan este estos explicame explicar explicacion favor fue ha hay la las le lo los me mi mis nos o para pero por porque puedes puede que quiero se si sobre son su sus te tengo tiene toda todo tu un una unas unos y yo".split())
STOP.update("ser puedo podria podrias saber quisiera explicas explica explique explicarme explicarlo cuentame hablame hablar favor importante importancia".split())
ALIASES = {"medit": "medit", "meditacion": "meditacion", "ucundinamarca": "universidad",
           "unicundi": "universidad", "udec": "universidad", "u": "universidad",
           "principios": "principio", "puntos": "principio", "punto": "principio",
           "numeral": "principio", "declaracion": "declaracion", "transhumanas": "transhumana",
           "transhumano": "transhumana", "transhumanos": "transhumana",
           "dimensiones": "dimension", "ejes": "eje", "campos": "campo",
           "significa": "significado", "significar": "significado", "responsable": "responsabilidad"}
ORDINALS = {"primero": 1, "primer": 1, "segundo": 2, "tercero": 3, "tercer": 3,
            "cuarto": 4, "quinto": 5, "sexto": 6, "septimo": 7, "octavo": 8,
            "noveno": 9, "decimo": 10, "undecimo": 11, "duodecimo": 12,
            "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
            "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}


def tokens(text: str) -> set[str]:
    return {ALIASES.get(t, t) for t in normalize(text).split() if t not in STOP}


@dataclass
class Respuesta:
    texto: str
    encontrado: bool = False
    articulo_id: str | None = None
    fuentes: list[dict] = field(default_factory=list)
    sugerencias: list[str] = field(default_factory=list)
    modo: str = "local"
    modelo: str | None = None
    llm_usado: bool = False


class Chatbot:
    MAX_QUESTION_LENGTH = 2000

    def __init__(self, db_path: Path | None = None, seed_path: Path | None = None):
        self.repository = KnowledgeRepository(db_path, seed_path)
        self.documents = self.repository.articles()
        self.by_id = {d["id"]: d for d in self.documents}
        self.by_number = {d["principio"]: d for d in self.documents if d["principio"]}
        self.last_document: dict | None = None
        self.vocabulary = set()
        counts = Counter()
        for d in self.documents:
            d["_tokens"] = tokens(" ".join([d["titulo"], d["palabras_clave"], *d["preguntas"]]))
            self.vocabulary.update(d["_tokens"])
            counts.update(d["_tokens"])
        self.weights = {t: math.log(1 + len(self.documents) / (1 + n)) for t, n in counts.items()}

    def reset(self) -> None:
        self.last_document = None

    def _answer(self, document: dict) -> Respuesta:
        self.last_document = document
        return Respuesta(
            document["contenido"], True, document["id"],
            [{"titulo": document["fuente_titulo"], "url": document["fuente_url"],
              "consultada_el": document["consultada_el"]}],
        )

    def _unknown(self) -> Respuesta:
        return Respuesta(
            "No encontré información suficiente para responder esa pregunta en mi base local. "
            "Puedo ayudarte con la Universidad de Cundinamarca, el MEDIT y los doce principios "
            "de la Declaración Persona Transhumana. Para fechas, pagos, trámites o información "
            "personal, consulta los canales oficiales de la Universidad.",
            sugerencias=["¿Qué es el MEDIT?", "Muéstrame los 12 principios", "¿Dónde está la seccional Ubaté?"],
        )

    def ask(self, question: str) -> Respuesta:
        if not isinstance(question, str) or not question.strip():
            return Respuesta("Escribe una pregunta sobre la Universidad, el MEDIT o la declaración.")
        if len(question) > self.MAX_QUESTION_LENGTH:
            return Respuesta("La pregunta es muy larga. Usa un máximo de 2000 caracteres.")
        q = normalize(question)
        if q in {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "hola picme"}:
            return Respuesta("Hola. Soy el asistente de PicMe. Pregúntame sobre la Universidad de "
                             "Cundinamarca, el MEDIT o la Declaración Persona Transhumana.")
        if q in {"gracias", "muchas gracias", "ok", "listo"}:
            return Respuesta("Con gusto. Puedes hacer otra pregunta.")
        if q in {"ayuda", "menu", "que sabes", "que puedo preguntar", "que puedes hacer"}:
            return Respuesta("Puedo consultar el MEDIT, sus ejes, dimensiones y campos; los doce "
                             "principios de la declaración; y datos generales de la Universidad y Ubaté.",
                             sugerencias=["¿Qué significa persona transhumana?", "Explícame el principio 6",
                                          "¿Cuáles son las dimensiones del MEDIT?"])
        if q in {"fuentes", "referencias", "cuales son tus fuentes", "de donde sacas la informacion"}:
            return Respuesta("Estas son las fuentes de la base local. Las respuestas no consultan "
                             "Internet en tiempo real.", True, fuentes=self.repository.sources())
        # Seguimiento al principio anterior, sin interpretar un número arbitrario como principio.
        if q in {"siguiente", "el siguiente", "y el siguiente", "otro principio"}:
            if self.last_document and self.last_document["principio"]:
                number = self.last_document["principio"] + 1
                if number in self.by_number:
                    return self._answer(self.by_number[number])
                return Respuesta("El principio 12 es el último. Puedes volver al principio 1.")
            return Respuesta("Indica un principio del 1 al 12 para comenzar.")
        if q in {"explicalo", "un ejemplo", "dame un ejemplo", "mas sencillo", "explicamelo mas sencillo"}:
            if self.last_document:
                return self._answer(self.last_document)
            return Respuesta("Dime qué principio o tema quieres que explique.")
        words = q.split()
        numbers = [int(w) if w.isdigit() else ORDINALS[w]
                   for w in words if w.isdigit() or w in ORDINALS]
        is_principle = any(w in {"principio", "principios", "punto", "puntos", "numeral"} for w in words)
        ordinal_principle = any(w in ORDINALS for w in words) and len(words) <= 4
        follows_number = bool(re.fullmatch(r"(?:y )?(?:el )?(?:\d+|" + "|".join(ORDINALS) + r")", q))
        if numbers and (is_principle or ordinal_principle or follows_number):
            plural_list = "principios" in words or "puntos" in words
            if numbers == [12] and (plural_list or "todos" in words or "cuales" in words or "muestrame" in words):
                return self._answer(self.by_id["declaracion_completa"])
            if len(set(numbers)) > 1:
                return Respuesta("Puedo explicar un principio a la vez. Indica un número del 1 al 12.")
            if numbers[0] not in self.by_number:
                return Respuesta("La declaración contiene doce principios. Elige un número del 1 al 12.")
            return self._answer(self.by_number[numbers[0]])
        if any(p in q for p in ("identidad de genero", "transgenero", "persona trans ", "personas trans ")):
            return self._answer(self.by_id["declaracion_contexto"]) 
        query_tokens = tokens(question)
        # La mención institucional acompaña muchas preguntas sin cambiar
        # su tema principal: 'qué significa MEDIT en la Universidad...'.
        if "medit" in query_tokens or {"persona", "transhumana"} <= query_tokens:
            query_tokens -= {"universidad", "cundinamarca"}
        if not query_tokens:
            return self._unknown()
        corrected = set()
        for token in query_tokens:
            match = get_close_matches(token, self.vocabulary, n=1, cutoff=0.82) if len(token) >= 5 else []
            corrected.add(token if token in self.vocabulary or not match else match[0])
        # Un dato no almacenado (p. ej. fechas de matrícula) no se responde por coincidir
        # únicamente con 'universidad' o 'medit'. Los artículos de orientación tienen sus
        # propias preguntas y son seleccionados por la búsqueda normal.
        best = None
        best_score = 0.0
        generic = {"universidad", "cundinamarca", "medit", "declaracion", "persona", "transhumana", "principio"}
        for document in self.documents:
            shared = corrected & document["_tokens"]
            if not shared:
                continue
            examples = [document["titulo"], *document["preguntas"], document["palabras_clave"]]
            score = 0.0
            for example in examples:
                et = tokens(example)
                denom = sum(self.weights.get(t, 2.0) for t in corrected)
                coverage = sum(self.weights.get(t, 2.0) for t in corrected & et) / max(denom, 1)
                precision = len(corrected & et) / max(len(et), 1)
                score = max(score, coverage * 0.85 + precision * 0.15)
            if normalize(question) in {normalize(e) for e in examples}:
                score = 1.0
            elif corrected - generic and not (shared - generic):
                score = 0.0
            if score > best_score:
                best, best_score = document, score
        if best is not None and best_score >= 0.56:
            return self._answer(best)
        return self._unknown()
