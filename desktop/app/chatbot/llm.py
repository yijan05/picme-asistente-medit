"""Gemini REST con contexto recuperado; sin dependencias externas ni claves en código."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

from .. import config

DEFAULT_MODEL = "gemini-3.8-flash"
PROMPT_PATH = config.BASE_DIR / "conocimiento" / "system_prompt.txt"


class LLMError(RuntimeError):
    """Error seguro para mostrar al usuario, sin cuerpo ni credenciales del proveedor."""


def load_environment(path: Path | None = None) -> None:
    """Lee solo las variables del chat desde .env; el entorno del proceso tiene prioridad."""
    path = path or config.BASE_DIR / ".env"
    if not path.exists():
        return
    allowed = {"GEMINI_API_KEY", "GEMINI_MODEL", "PICME_CHAT_MODE"}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() in allowed:
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def build_payload(question: str, documents: list[dict], history: list[dict]) -> dict:
    evidence = [{"id": d["id"], "titulo": d["titulo"], "contenido": d["contenido"],
                 "fuente": d["fuente_titulo"]} for d in documents]
    # Los antecedentes se acotan y se consideran datos de baja confianza.
    past = [{"pregunta": t["pregunta"][:2000], "respuesta": t["respuesta"][:3000]}
            for t in history[-4:]]
    data = {"documentos_recuperados": evidence, "historial_reciente": past, "pregunta": question}
    return {
        "systemInstruction": {"parts": [{"text": PROMPT_PATH.read_text(encoding="utf-8")}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(data, ensure_ascii=False)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "respuesta": {"type": "STRING"},
                    "articulos_usados": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["respuesta", "articulos_usados"],
            },
        },
    }


def parse_generation(body: dict, allowed_ids: set[str]) -> tuple[str, list[str]]:
    if not isinstance(body, dict):
        raise LLMError("El proveedor no entregó un objeto de respuesta válido.")
    candidates = body.get("candidates") or []
    if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
        raise LLMError("El proveedor no entregó una respuesta utilizable.")
    candidate = candidates[0]
    if candidate.get("finishReason") not in (None, "STOP"):
        raise LLMError("El proveedor interrumpió la generación. Intenta una pregunta más breve.")
    content = candidate.get("content")
    parts = content.get("parts", []) if isinstance(content, dict) else []
    if not isinstance(parts, list):
        raise LLMError("La respuesta del proveedor no contiene partes válidas.")
    text = "".join(p["text"] for p in parts if isinstance(p, dict)
                   and isinstance(p.get("text"), str) and not p.get("thought"))
    try:
        result = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise LLMError("La respuesta del LLM no cumplió el formato esperado.") from exc
    if not isinstance(result, dict):
        raise LLMError("La respuesta del LLM no es un objeto JSON.")
    answer, ids = result.get("respuesta"), result.get("articulos_usados")
    if not isinstance(answer, str) or not answer.strip() or len(answer) > 12000:
        raise LLMError("La respuesta del LLM está vacía o excede el límite.")
    if not isinstance(ids, list) or any(not isinstance(i, str) or i not in allowed_ids for i in ids):
        raise LLMError("El LLM devolvió referencias ajenas a los documentos recuperados.")
    return answer.strip(), list(dict.fromkeys(ids))


class GeminiClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, opener=None):
        if not api_key:
            raise LLMError("Configura GEMINI_API_KEY para activar el LLM.")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
            raise LLMError("GEMINI_MODEL no tiene un formato válido.")
        self.api_key = api_key
        self.model = model
        self.opener = opener or urllib.request.urlopen

    def generate(self, question: str, documents: list[dict], history: list[dict]) -> tuple[str, list[str]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        request = urllib.request.Request(
            url, data=json.dumps(build_payload(question, documents, history), ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key}, method="POST",
        )
        try:
            with self.opener(request, timeout=45) as response:
                body = json.loads(response.read(1024 * 1024).decode("utf-8"))
        except urllib.error.HTTPError as exc:
            messages = {400: "Revisa el modelo y la configuración de Gemini.",
                        401: "La credencial de Gemini fue rechazada.",
                        403: "La clave de Gemini no tiene acceso al modelo.",
                        404: "El modelo no está disponible para esta clave.",
                        429: "Se alcanzó el límite de consultas del proveedor."}
            raise LLMError(messages.get(exc.code, "Gemini no está disponible en este momento.")) from None
        except (OSError, ValueError) as exc:
            raise LLMError("No se pudo completar la conexión con Gemini.") from None
        return parse_generation(body, {d["id"] for d in documents})
