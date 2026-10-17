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
    text = " ".join(re.findall(r"[a-z0-9]+", text))
    return re.sub(r"\b(?:trans|tras)\s+(human[ao]s?)\b", r"trans\1", text)


STOP = set("a al algo ante aqui asi cual cuales como con conoce conocer de del dime el ella ellas ellos en es esa esas ese eso esta estan este estos explicame explicar explicacion favor fue ha hay la las le lo los me mi mis nos o para pero por porque puedes puede que quiero se si sobre son su sus te tengo tiene toda todo tu un una unas unos y yo".split())
STOP.update("ser puedo podria podrias saber quisiera explicas explica explique explicarme explicarlo cuentame hablame hablar favor importante importancia what is are was were does did do can could would should please tell explain describe define mean means does how why who where which the this that these those my your me about give list show next and for of to in on from with by it its as at be have has had i we they he she them their our your am an if then than also into than much many".split())
ALIASES = {"medit": "medit", "meditacion": "meditacion", "ucundinamarca": "universidad",
           "unicundi": "universidad", "udec": "universidad", "u": "universidad",
           "principios": "principio", "puntos": "principio", "punto": "principio",
           "numeral": "principio", "declaracion": "declaracion", "transhumanas": "transhumana",
           "transhumano": "transhumana", "transhumanos": "transhumana",
           "trashumana": "transhumana", "trashumano": "transhumana",
           "trashumanas": "transhumana", "trashumanos": "transhumana",
           "transumana": "transhumana", "transumano": "transhumana",
           "dimensiones": "dimension", "ejes": "eje", "campos": "campo",
           "significa": "significado", "significar": "significado", "responsable": "responsabilidad",
           "university": "universidad", "universitys": "universidad", "people": "persona", "person": "persona",
           "users": "usuario", "user": "usuario", "registered": "registrado", "registration": "registro",
           "registrations": "registro", "dimension": "dimension", "dimensions": "dimension",
           "pillar": "eje", "pillars": "eje", "axes": "eje", "axis": "eje", "ethics": "etica",
           "ethical": "etica", "learning": "aprendizaje", "knowledge": "conocimiento", "technology": "tecnologia",
           "technologies": "tecnologia", "declaration": "declaracion", "transhuman": "transhumana",
           "principle": "principio", "principles": "principio", "meaning": "significado", "care": "cuidado",
           "health": "salud", "freedom": "libertad", "responsibility": "responsabilidad", "family": "familia",
           "society": "sociedad", "classroom": "aula", "nature": "naturaleza", "culture": "cultura"}
ORDINALS = {"primero": 1, "primer": 1, "segundo": 2, "tercero": 3, "tercer": 3,
            "cuarto": 4, "quinto": 5, "sexto": 6, "septimo": 7, "octavo": 8,
            "noveno": 9, "decimo": 10, "undecimo": 11, "duodecimo": 12,
            "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
            "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
            "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
            "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12}


def tokens(text: str) -> set[str]:
    return {ALIASES.get(t, t) for t in normalize(text).split() if t not in STOP}


def is_declaration_reflection(question: str) -> bool:
    """Reconoce una reflexión sobre la declaración, sin clasificar identidades."""
    words = set(normalize(question).split())
    topic = tokens(question)
    if "transhumana" in topic and words & {
        "soy", "somos", "eres", "cumplo", "cumplimos", "considerarme",
        "considero", "identificarme", "convertirme", "ser", "reconocerme",
        "am", "are", "be", "become", "identify", "consider",
    }:
        return True
    return bool(
        topic & {"principio", "declaracion"}
        and words & {"aplico", "aplicar", "aplicarlos", "practico", "practicar", "vivir",
                     "apply", "practice", "practise"}
        and words & {"mi", "mis", "vida", "cotidiana", "diaria", "my", "life", "daily", "everyday"}
    )


def question_is_english(question: str) -> bool:
    markers = {"hello", "hi", "good", "what", "how", "why", "when", "where", "who", "which", "explain", "tell", "show",
               "please", "the", "this", "that", "my", "your", "people", "users", "registered",
               "principle", "principles", "learning", "knowledge", "technology", "university", "care", "am"}
    return bool(set(normalize(question).split()) & markers)


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
        self._english = False
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
        content = document.get("contenido_en", document["contenido"]) if self._english else document["contenido"]
        return Respuesta(
            content, True, document["id"],
            [{"titulo": document["fuente_titulo"], "url": document["fuente_url"],
              "consultada_el": document["consultada_el"]}],
        )

    def _unknown(self) -> Respuesta:
        if self._english:
            return Respuesta(
                "I could not find enough information to answer that from the local knowledge base. "
                "I can help with PicMe, the University of Cundinamarca, MEDIT, and the twelve principles "
                "of the Declaration of the Transhuman Person. For personal records, ask a specific PicMe data question.",
                sugerencias=["What is MEDIT?", "Explain principle 6", "How many people are registered in PicMe?"],
            )
        return Respuesta(
            "No encontré información suficiente para responder esa pregunta en mi base local. "
            "Puedo ayudarte con PicMe, la Universidad de Cundinamarca, el MEDIT y los doce principios "
            "de la Declaración Persona Transhumana. Para datos operativos, haz una pregunta concreta sobre PicMe.",
            sugerencias=["¿Qué es el MEDIT?", "Explícame el principio 6", "¿Cuántas personas están registradas en PicMe?"],
        )

    def ask(self, question: str) -> Respuesta:
        self._english = question_is_english(question) if isinstance(question, str) else False
        if not isinstance(question, str) or not question.strip():
            return Respuesta("Ask a question about PicMe, MEDIT, or the declaration." if self._english else "Escribe una pregunta sobre PicMe, el MEDIT o la declaración.")
        if len(question) > self.MAX_QUESTION_LENGTH:
            return Respuesta("Your question is too long. Use no more than 2000 characters." if self._english else "La pregunta es muy larga. Usa un máximo de 2000 caracteres.")
        q = normalize(question)
        if q in {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "hola picme", "hello", "hi", "hello picme", "good morning", "good afternoon"}:
            return Respuesta("Hello. I am PicMe's assistant. Ask me about PicMe records, the University of Cundinamarca, MEDIT, or the Declaration of the Transhuman Person." if self._english else "Hola. Soy el asistente de PicMe. Pregúntame sobre registros de PicMe, la Universidad de Cundinamarca, el MEDIT o la Declaración Persona Transhumana.")
        if q in {"gracias", "muchas gracias", "ok", "listo", "thanks", "thank you", "thank you very much"}:
            return Respuesta("You're welcome. You can ask another question." if self._english else "Con gusto. Puedes hacer otra pregunta.")
        if q in {"que es picme", "que hace picme", "what is picme", "what does picme do", "how does picme work"}:
            return Respuesta(
                "PicMe is an academic desktop prototype that uses facial recognition to support access-control workflows. It stores registered accounts and records access attempts, such as permitted and unknown attempts. Its assistant can answer operational questions from the local database and explain MEDIT. It does not send the biometric database to Gemini.",
                True,
            ) if self._english else Respuesta(
                "PicMe es un prototipo académico de escritorio que usa reconocimiento facial para apoyar el control de ingreso. Guarda cuentas registradas y registra intentos de acceso, incluidos los permitidos y los desconocidos. Su asistente puede consultar datos operativos de la base local y explicar el MEDIT. La base biométrica no se envía a Gemini.",
                True,
            )
        if q in {"ayuda", "menu", "que sabes", "que puedo preguntar", "que puedes hacer", "help", "menu", "what can you do", "what do you know"}:
            return Respuesta("I can answer PicMe questions about registered users and entry events, and explain MEDIT, its pillars and dimensions, and the twelve principles of the declaration." if self._english else "Puedo responder preguntas de PicMe sobre usuarios registrados y eventos de ingreso, además de explicar el MEDIT, sus ejes y dimensiones, y los doce principios de la declaración.",
                             sugerencias=["How many people are registered in PicMe?", "What is MEDIT?", "Explain principle 6"] if self._english else ["¿Cuántas personas están registradas en PicMe?", "¿Qué es el MEDIT?", "Explícame el principio 6"])
        if q in {"fuentes", "referencias", "cuales son tus fuentes", "de donde sacas la informacion", "sources", "references", "what are your sources"}:
            return Respuesta("These are the sources in the local knowledge base. This answer does not search the live web." if self._english else "Estas son las fuentes de la base local. Las respuestas no consultan Internet en tiempo real.", True, fuentes=self.repository.sources())
        # Seguimiento al principio anterior, sin interpretar un número arbitrario como principio.
        if q in {"siguiente", "el siguiente", "y el siguiente", "otro principio", "next", "the next", "next principle"}:
            if self.last_document and self.last_document["principio"]:
                number = self.last_document["principio"] + 1
                if number in self.by_number:
                    return self._answer(self.by_number[number])
                return Respuesta("Principle 12 is the last one. You can return to principle 1." if self._english else "El principio 12 es el último. Puedes volver al principio 1.")
            return Respuesta("Tell me a principle number from 1 to 12 to begin." if self._english else "Indica un principio del 1 al 12 para comenzar.")
        if q in {"explicalo", "un ejemplo", "dame un ejemplo", "mas sencillo", "explicamelo mas sencillo", "explain it", "an example", "give me an example", "simpler"}:
            if self.last_document:
                return self._answer(self.last_document)
            return Respuesta("Tell me which principle or topic you want me to explain." if self._english else "Dime qué principio o tema quieres que explique.")
        words = q.split()
        numbers = [int(w) if w.isdigit() else ORDINALS[w]
                   for w in words if w.isdigit() or w in ORDINALS]
        is_principle = any(w in {"principio", "principios", "punto", "puntos", "numeral", "principle", "principles"} for w in words)
        ordinal_principle = any(w in ORDINALS for w in words) and len(words) <= 4
        follows_number = bool(re.fullmatch(r"(?:y )?(?:el )?(?:\d+|" + "|".join(ORDINALS) + r")", q))
        if numbers and (is_principle or ordinal_principle or follows_number):
            plural_list = any(w in {"principios", "puntos", "principles", "todos", "all", "list"} for w in words)
            if numbers == [12] and (plural_list or "todos" in words or "cuales" in words or "muestrame" in words or "show" in words):
                return self._answer(self.by_id["declaracion_completa"])
            if len(set(numbers)) > 1:
                return Respuesta("Puedo explicar un principio a la vez. Indica un número del 1 al 12.")
            if numbers[0] not in self.by_number:
                return Respuesta("La declaración contiene doce principios. Elige un número del 1 al 12.")
            return self._answer(self.by_number[numbers[0]])
        if any(p in q for p in ("identidad de genero", "transgenero", "persona trans ", "personas trans ", "gender identity", "transgender")):
            return self._answer(self.by_id["declaracion_contexto"]) 
        if is_declaration_reflection(question):
            document = self.by_id.get("declaracion_reflexion", self.by_id["declaracion_resumen"])
            return self._answer(document)
        query_tokens = tokens(question)
        if "transhumana" in query_tokens and query_tokens <= {
            "persona", "transhumana", "significado", "declaracion", "universidad", "cundinamarca", "medit",
        }:
            return self._answer(self.by_id["declaracion_resumen"])
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
