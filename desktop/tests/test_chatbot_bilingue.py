"""Comprueba el idioma y la reflexión con la integración de las dos versiones."""
import json
from pathlib import Path
import tempfile
import unittest

from app.chatbot.engine import Chatbot
from app.chatbot.rag import RagAssistant
from app.chatbot.repository import SEED_PATH, TRANSLATIONS_PATH


class BilingualChatbotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'chatbot.db'
        self.bot = Chatbot(self.path, SEED_PATH)

    def tearDown(self):
        self.temp.cleanup()

    def test_all_principles_in_both_languages(self):
        for number in range(1, 13):
            article_id = f'principio_{number:02d}'
            for question, field in [(f'Explícame el principio {number}', 'contenido'),
                                    (f'Explain principle {number}', 'contenido_en')]:
                with self.subTest(question=question):
                    answer = self.bot.ask(question)
                    self.assertEqual(answer.articulo_id, article_id)
                    self.assertEqual(answer.texto, self.bot.by_id[article_id][field])

    def test_medit_question_in_english(self):
        answer = self.bot.ask('What is MEDIT?')
        self.assertEqual(answer.articulo_id, 'medit_definicion')
        self.assertEqual(answer.texto, self.bot.by_id[answer.articulo_id]['contenido_en'])

    def test_translations_cover_the_entire_seed(self):
        seed = json.loads(SEED_PATH.read_text(encoding='utf-8'))
        translations = json.loads(TRANSLATIONS_PATH.read_text(encoding='utf-8'))
        self.assertTrue(all(translations.get(article['id']) for article in seed['articulos']))

    def test_english_reflection_is_educational(self):
        for question in ['How do I know if I am a transhuman person?', 'Am I a transhuman person?']:
            with self.subTest(question=question):
                answer = self.bot.ask(question)
                self.assertEqual(answer.articulo_id, 'declaracion_reflexion')
                self.assertIn('not an evaluation', answer.texto)

    def test_english_reflection_retrieves_the_complete_declaration(self):
        class Provider:
            model = 'simulated'
            documents = None
            def generate(self, question, documents, history):
                self.documents = documents
                return 'An educational reflection.', [d['id'] for d in documents]
        provider = Provider()
        bot = RagAssistant(self.path, SEED_PATH, provider=provider, mode='gemini')
        answer = bot.ask('How do I know if I am a transhuman person?')
        self.assertTrue(answer.llm_usado)
        self.assertEqual([d['id'] for d in provider.documents],
                         ['declaracion_reflexion', 'declaracion_completa'])


if __name__ == '__main__':
    unittest.main()
