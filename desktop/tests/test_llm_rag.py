import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from app.chatbot.llm import GeminiClient, LLMError, build_payload, parse_generation
from app.chatbot.rag import RagAssistant


class FakeProvider:
    model = "modelo-de-prueba"

    def __init__(self):
        self.calls = []

    def generate(self, question, documents, history):
        self.calls.append((question, documents, list(history)))
        return "Explicación de prueba con una referencia recuperada.", [documents[0]["id"]]


class RagIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.load = patch("app.chatbot.rag.load_environment")
        self.load.start()
        self.provider = FakeProvider()
        self.bot = RagAssistant(Path(self.temp.name) / "chat.db", provider=self.provider)

    def tearDown(self):
        self.load.stop()
        self.env.stop()
        self.temp.cleanup()

    def test_llm_recibe_fragmentos_y_devuelve_fuentes(self):
        answer = self.bot.ask("Explícame el principio 6")
        self.assertTrue(answer.llm_usado)
        self.assertEqual(answer.modo, "gemini")
        self.assertEqual(answer.articulo_id, "principio_06")
        self.assertEqual(self.provider.calls[0][1][0]["id"], "principio_06")
        self.assertTrue(answer.fuentes)

    def test_comparacion_recupera_dos_principios(self):
        self.bot.ask("Compara los principios 5 y 9")
        ids = [d["id"] for d in self.provider.calls[-1][1]]
        self.assertEqual(ids[:2], ["principio_05", "principio_09"])

    def test_historial_contextual_acotado(self):
        for number in range(1, 7):
            self.bot.ask(f"Explícame el principio {number}")
        self.assertEqual(len(self.bot.history), 4)
        self.assertTrue(self.provider.calls[-1][2])
        self.assertLessEqual(len(self.provider.calls[-1][2]), 4)

    def test_sin_evidencia_no_invoca_llm(self):
        answer = self.bot.ask("¿Cuál es la capital de Colombia?")
        self.assertFalse(answer.llm_usado)
        self.assertFalse(self.provider.calls)

    def test_modo_local_explicito_no_invoca_llm(self):
        self.bot.mode = "local"
        self.assertFalse(self.bot.ask("qué es el medit").llm_usado)
        self.assertFalse(self.provider.calls)

    def test_error_api_se_identifica_como_respaldo(self):
        with patch.object(self.provider, "generate", side_effect=LLMError("Se alcanzó el límite.")):
            answer = self.bot.ask("Qué es el MEDIT")
        self.assertFalse(answer.llm_usado)
        self.assertEqual(answer.modo, "local_respaldo")
        self.assertIn("límite", answer.texto)

    def test_limite_de_pregunta_antes_del_proveedor(self):
        self.bot.ask("x" * 2001)
        self.assertFalse(self.provider.calls)

    def test_reinicio_elimina_contexto(self):
        self.bot.ask("principio 3")
        self.bot.reset()
        self.assertEqual(self.bot.history, [])
        self.assertEqual(self.bot.previous_ids, [])

    def test_payload_incluye_system_prompt_y_contexto_serializado(self):
        d = self.bot.local.by_id["principio_05"]
        payload = build_payload("Qué significa cuidarme", [d], [])
        self.assertIn("FEW-SHOT", payload["systemInstruction"]["parts"][0]["text"])
        content = json.loads(payload["contents"][0]["parts"][0]["text"])
        self.assertEqual(len(content["documentos_recuperados"]), 1)
        self.assertEqual(payload["generationConfig"]["responseMimeType"], "application/json")

    def test_transporte_resta_clave_de_url_y_solo_la_envia_en_header(self):
        def opener(request, timeout):
            self.assertNotIn("clave-de-prueba", request.full_url)
            self.assertEqual(request.get_header("X-goog-api-key"), "clave-de-prueba")
            self.assertEqual(timeout, 45)
            body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps({"respuesta": "Respuesta de prueba", "articulos_usados": ["principio_05"]})}]}}]}
            return io.BytesIO(json.dumps(body).encode())
        client = GeminiClient("clave-de-prueba", opener=opener)
        answer, ids = client.generate("principio 5", [self.bot.local.by_id["principio_05"]], [])
        self.assertEqual(ids, ["principio_05"])

    def test_referencia_inventada_se_rechaza(self):
        body = {"candidates": [{"content": {"parts": [{"text": '{"respuesta":"Algo", "articulos_usados":["fuente_inventada"]}'}]}}]}
        with self.assertRaises(LLMError):
            parse_generation(body, {"principio_05"})

    def test_json_con_formato_incorrecto_se_rechaza(self):
        for text in ["No es JSON", "[]", '{"respuesta":"", "articulos_usados":[]}']:
            with self.subTest(text=text):
                body = {"candidates": [{"content": {"parts": [{"text": text}]}}]}
                with self.assertRaises(LLMError):
                    parse_generation(body, set())

    def test_http_429_no_revela_cuerpo_del_proveedor(self):
        def opener(*args, **kwargs):
            raise HTTPError("https://example.invalid", 429, "cuerpo-privado", {}, None)
        client = GeminiClient("clave-de-prueba", opener=opener)
        with self.assertRaisesRegex(LLMError, "límite"):
            client.generate("principio 5", [self.bot.local.by_id["principio_05"]], [])


if __name__ == "__main__":
    unittest.main()
