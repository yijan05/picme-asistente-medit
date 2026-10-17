"""Pruebas de consultas operativas bilingües y de solo lectura."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
import sqlite3
from unittest.mock import patch

from app import db
from app.chatbot.picme_queries import PicMeDataAssistant
from app.chatbot.rag import RagAssistant
from app.chatbot.repository import SEED_PATH


class User:
    def __init__(self, user_id, email):
        self.id = user_id
        self.correo = email


class PicMeQueriesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "picme.db"
        db.init_db(self.path)
        self.uid = db.crear_usuario("Alice Example", "alice@example.com", "hash", db_path=self.path)
        db.crear_usuario("Bob Example", "bob@example.com", "hash", db_path=self.path)
        db.registrar_ingreso(self.uid, "permitido", 0.91, db_path=self.path)
        db.registrar_ingreso(None, "desconocido", None, db_path=self.path)
        self.service = PicMeDataAssistant(self.path, admin_emails={"admin@example.com"})

    def tearDown(self):
        self.temp.cleanup()

    def test_count_registered_in_spanish_and_english(self):
        es = self.service.ask("¿Cuántas personas están registradas en PicMe?")
        en = self.service.ask("How many people are registered in PicMe?")
        self.assertIn("Hay 2 personas", es)
        self.assertIn("There are 2 people", en)

    def test_count_entry_events(self):
        es = self.service.ask("¿Cuántos ingresos hay en total?")
        en = self.service.ask("How many entry events are recorded?")
        self.assertIn("2 eventos", es)
        self.assertIn("2 entry events", en)

    def test_spanish_own_registration_keeps_spanish(self):
        answer = self.service.ask("¿Cuándo me registré?", User(self.uid, "alice@example.com"))
        self.assertIn("Tu cuenta", answer)

    def test_today_names_require_authorization(self):
        for question in ["¿Quién ingresó hoy?", "Who entered today?"]:
            with self.subTest(question=question):
                denied = self.service.ask(question)
                allowed = self.service.ask(question, User(self.uid, "admin@example.com"))
                self.assertTrue("autorizada" in denied or "authorized" in denied)
                self.assertIn("Alice Example", allowed)

    def test_successful_today_excludes_unknown_attempts(self):
        es = self.service.ask("¿Cuántos ingresos permitidos hay hoy?")
        en = self.service.ask("How many successful entries are recorded today?")
        self.assertIn("1 ingresos", es)
        self.assertIn("1 successful entry", en)

    def test_named_time_today_does_not_return_global_count(self):
        answer = self.service.ask("What time did Alice Example enter today?", User(self.uid, "admin@example.com"))
        self.assertIn("Alice Example's latest recorded entry", answer)

    def test_sqlite_rejects_a_write(self):
        connection = self.service._connect()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM usuario")
        finally:
            connection.close()

    def test_personal_last_entry_requires_login(self):
        no_session = self.service.ask("When did I last enter PicMe?")
        with_session = self.service.ask("When did I last enter PicMe?", User(self.uid, "alice@example.com"))
        self.assertIn("Sign in", no_session)
        self.assertIn("Your latest recorded entry", with_session)

    def test_named_person_entry_requires_authorized_account(self):
        denied = self.service.ask("When did Alice Example enter PicMe?", User(2, "bob@example.com"))
        allowed = self.service.ask("When did Alice Example enter PicMe?", User(2, "admin@example.com"))
        self.assertIn("authorized account", denied)
        self.assertIn("Alice Example's latest recorded entry", allowed)

    def test_active_users_not_invented(self):
        answer = self.service.ask("How many active users are there?")
        self.assertIn("no active/inactive user-status field", answer)

    def test_unrelated_question_is_not_handled(self):
        self.assertIsNone(self.service.ask("What is MEDIT?"))

    def test_database_is_read_only(self):
        before = len(db.listar_usuarios(db_path=self.path))
        self.service.ask("How many people are registered in PicMe?")
        after = len(db.listar_usuarios(db_path=self.path))
        self.assertEqual(before, after)

    def test_rag_handles_operational_questions_before_llm(self):
        class Provider:
            model = "fake-model"
            def generate(self, *args, **kwargs):
                raise AssertionError("Operational records must never be sent to the LLM")

        knowledge_db = Path(self.temp.name) / "chatbot.db"
        with patch("app.config.DB_PATH", self.path):
            bot = RagAssistant(knowledge_db, SEED_PATH, provider=Provider(), mode="gemini")
            answer = bot.ask("How many people are registered in PicMe?")
        self.assertEqual(answer.modo, "picme_datos")
        self.assertIn("There are 2 people", answer.texto)


if __name__ == "__main__":
    unittest.main()
