"""Consultas operativas de PicMe en modo SQLite de solo lectura.

Solo devuelve estadísticas y eventos de acceso. Nunca lee hashes de contraseña,
plantillas biométricas, rutas de modelos ni puntuaciones de reconocimiento.
"""
from __future__ import annotations

import os
import re
import sqlite3
import unicodedata
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from .. import config


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9@._-]+", text))


ENGLISH_MARKERS = {
    "how", "many", "people", "users", "registered", "registration", "registrations",
    "when", "did", "enter", "entered", "entry", "entries", "access", "last", "today",
    "month", "this", "show", "my", "who", "was", "what", "time", "count",
    "number", "successful", "active", "is", "are", "there", "have", "has",
    "please", "registered", "user", "person", "people",
}


def is_english(question: str) -> bool:
    words = set(normalize(question).split())
    return len(words & ENGLISH_MARKERS) >= 1


def _local_day_bounds(day: date | None = None) -> tuple[str, str]:
    """Rango del día local convertido a UTC, compatible con timestamps de app.db."""
    day = day or datetime.now().astimezone().date()
    tz = datetime.now().astimezone().tzinfo
    start_local = datetime.combine(day, time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return (start_local.astimezone(timezone.utc).isoformat(),
            end_local.astimezone(timezone.utc).isoformat())


def _format_timestamp(value: str | None) -> str:
    if not value:
        return "fecha no disponible"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(value)


class PicMeDataAssistant:
    """Clasifica preguntas operativas y ejecuta SELECT parametrizados en picme.db."""

    def __init__(self, db_path: Path | None = None, admin_emails: set[str] | None = None):
        self.db_path = Path(db_path or config.DB_PATH)
        configured = os.getenv("PICME_CHATBOT_ADMIN_EMAILS", "")
        self.admin_emails = {e.strip().casefold() for e in (admin_emails or set()) if e.strip()}
        self.admin_emails.update(e.strip().casefold() for e in configured.split(",") if e.strip())

    def _connect(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise FileNotFoundError("La base de datos de PicMe aún no existe.")
        # URI mode=ro impide que una pregunta cree o modifique la base.
        uri = self.db_path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=3)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        return conn

    def _authorized_for_people(self, user: Any) -> bool:
        email = getattr(user, "correo", "") if user is not None else ""
        return bool(email and email.casefold() in self.admin_emails)

    @staticmethod
    def _answer(es: str, en: str, english: bool) -> str:
        return en if english else es

    def ask(self, question: str, user: Any = None) -> str | None:
        q = normalize(question)
        words = set(q.split())
        english = is_english(question)

        # Detección de preguntas sobre usuarios registrados.
        asks_registered = (
            ("registrad" in q or "registered" in q or "registro" in q or "registrations" in q)
            and any(w in words for w in {"persona", "personas", "usuario", "usuarios", "user", "users", "people", "person", "cuantas", "cuantos", "how", "many", "count", "number", "total"})
        ) or any(phrase in q for phrase in (
            "cuantas personas hay", "cuantos usuarios hay", "total de usuarios", "total de personas",
            "how many users", "how many people", "number of registered", "total users", "total people",
        ))
        asks_active = any(phrase in q for phrase in ("usuarios activos", "personas activas", "active users", "active people"))
        asks_today_registration = any(phrase in q for phrase in (
            "registrados hoy", "registradas hoy", "se registraron hoy", "registro de hoy",
            "registered today", "registrations today", "signed up today",
        ))
        asks_month_registration = any(phrase in q for phrase in (
            "registrados este mes", "registradas este mes", "registro este mes", "registraron este mes",
            "registered this month", "registrations this month", "signed up this month",
        ))

        # Preguntas sobre ingresos/accesos, tanto en español como en inglés.
        asks_entries = any(term in words for term in {
            "ingreso", "ingresos", "ingreso", "acceso", "accesos", "entradas", "entrada",
            "enter", "entered", "entry", "entries", "access", "login", "logins",
        }) or any(phrase in q for phrase in ("a que hora ingreso", "cuando ingreso", "ultimo ingreso", "last entry", "last access", "when did"))
        asks_entry_count = asks_entries and any(term in words for term in {
            "cuantos", "cuantas", "total", "many", "count", "number", "successful",
        })
        asks_latest = any(phrase in q for phrase in (
            "ultimos ingresos", "ultimos accesos", "ingresos recientes", "accesos recientes",
            "ultimo ingreso", "ultimo acceso", "last entry", "last access", "recent entries", "recent access",
            "latest entries", "latest access", "quien ingreso hoy", "quienes ingresaron hoy",
            "who entered today", "who accessed today", "who came in today",
        ))
        asks_person_entry = asks_entries and any(phrase in q for phrase in (
            "a que hora", "cuando ingreso", "cuando entro", "cuando accedio", "when did", "what time", "when was", "last entry for", "last access for",
        ))
        asks_my_entry = any(phrase in q for phrase in (
            "mi ultimo ingreso", "cuando ingrese", "mi ultimo acceso", "my last entry", "my last access",
            "when did i enter", "when did i last enter", "when did i log in",
        ))
        asks_my_registration = any(phrase in q for phrase in (
            "cuando me registre", "cuando me registre en", "mi fecha de registro", "when did i register",
            "when did i sign up", "my registration date",
        ))
        asks_registration_date = any(phrase in q for phrase in (
            "cuando se registro", "cuando se registro", "fecha de registro de", "when did", "registration date of",
        )) and any(w in words for w in {"registró", "registro", "registered", "register", "registration"})

        if not any((asks_registered, asks_active, asks_today_registration, asks_month_registration,
                    asks_entries, asks_my_entry, asks_my_registration, asks_registration_date)):
            return None

        try:
            conn = self._connect()
        except (FileNotFoundError, sqlite3.Error):
            return self._answer(
                "No pude leer la base de datos local de PicMe. Comprueba que PicMe se haya iniciado al menos una vez.",
                "I could not read PicMe's local database. Check that PicMe has been started at least once.", english,
            )

        try:
            if asks_active:
                return self._answer(
                    "La base actual no tiene un campo de estado activo/inactivo para usuarios, así que no puedo calcular ese dato con fiabilidad. Sí puedo contar las cuentas registradas.",
                    "The current database has no active/inactive user-status field, so I cannot calculate that reliably. I can count registered accounts.", english,
                )

            if asks_my_registration:
                if user is None:
                    return self._answer("Para consultar tu fecha de registro, inicia sesión en PicMe.",
                                         "Sign in to PicMe to check your registration date.", english)
                row = conn.execute("SELECT nombre, creado_en FROM usuario WHERE id = ?", (user.id,)).fetchone()
                if not row:
                    return self._answer("No encontré tu cuenta en la base de datos de PicMe.",
                                         "I could not find your account in PicMe's database.", english)
                return self._answer(f"Tu cuenta, {row['nombre']}, fue registrada el {_format_timestamp(row['creado_en'])}.",
                                     f"Your account, {row['nombre']}, was registered on {_format_timestamp(row['creado_en'])}.", english)

            if asks_my_entry:
                if user is None:
                    return self._answer("Para consultar tu historial de ingresos, inicia sesión en PicMe.",
                                         "Sign in to PicMe to check your entry history.", english)
                row = conn.execute("SELECT creado_en, resultado FROM ingreso WHERE usuario_id = ? ORDER BY id DESC LIMIT 1", (user.id,)).fetchone()
                if not row:
                    return self._answer("No hay ingresos registrados para tu cuenta.",
                                         "There are no entry events recorded for your account.", english)
                return self._answer(f"Tu último ingreso registrado fue el {_format_timestamp(row['creado_en'])}. Resultado: {row['resultado']}.",
                                     f"Your latest recorded entry was on {_format_timestamp(row['creado_en'])}. Result: {row['resultado']}.", english)

            if asks_today_registration:
                start, end = _local_day_bounds()
                row = conn.execute("SELECT COUNT(*) AS n FROM usuario WHERE creado_en >= ? AND creado_en < ?", (start, end)).fetchone()
                return self._answer(f"Hoy se registraron {row['n']} cuentas nuevas en PicMe.",
                                     f"{row['n']} new accounts were registered in PicMe today.", english)

            if asks_month_registration:
                now = datetime.now().astimezone()
                start_local = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
                if now.month == 12:
                    next_local = datetime(now.year + 1, 1, 1, tzinfo=now.tzinfo)
                else:
                    next_local = datetime(now.year, now.month + 1, 1, tzinfo=now.tzinfo)
                start, end = start_local.astimezone(timezone.utc).isoformat(), next_local.astimezone(timezone.utc).isoformat()
                row = conn.execute("SELECT COUNT(*) AS n FROM usuario WHERE creado_en >= ? AND creado_en < ?", (start, end)).fetchone()
                return self._answer(f"Este mes se registraron {row['n']} cuentas nuevas en PicMe.",
                                     f"{row['n']} new accounts were registered in PicMe this month.", english)

            if asks_registered:
                row = conn.execute("SELECT COUNT(*) AS n FROM usuario").fetchone()
                return self._answer(f"Hay {row['n']} personas registradas en PicMe.",
                                     f"There are {row['n']} people registered in PicMe.", english)

            if asks_entry_count:
                conditions = []
                parameters = []
                if "hoy" in words or "today" in words:
                    start, end = _local_day_bounds()
                    conditions.append("creado_en >= ? AND creado_en < ?")
                    parameters.extend((start, end))
                successful = bool(words & {"successful", "permitidos", "permitido", "permitted", "exitosos"})
                if successful:
                    conditions.append("resultado = ?")
                    parameters.append("permitido")
                where = " WHERE " + " AND ".join(conditions) if conditions else ""
                row = conn.execute("SELECT COUNT(*) AS n FROM ingreso" + where, parameters).fetchone()
                if successful and ("hoy" in words or "today" in words):
                    return self._answer(f"Hoy hay {row['n']} ingresos con resultado 'permitido' en PicMe.",
                                         f"There are {row['n']} successful entry events recorded in PicMe today.", english)
                if "hoy" in words or "today" in words:
                    return self._answer(f"Hoy hay {row['n']} eventos de ingreso registrados en PicMe.",
                                         f"There are {row['n']} entry events recorded in PicMe today.", english)
                if successful:
                    return self._answer(f"Hay {row['n']} ingresos con resultado 'permitido' en el historial.",
                                         f"There are {row['n']} entries with a 'permitted' result in the history.", english)
                return self._answer(f"El historial contiene {row['n']} eventos de ingreso, incluidos intentos desconocidos.",
                                     f"The history contains {row['n']} entry events, including unknown attempts.", english)

            if asks_latest or asks_person_entry or asks_registration_date:
                if not self._authorized_for_people(user):
                    return self._answer(
                        "Para consultar el historial o la fecha de registro de otra persona, inicia sesión con una cuenta autorizada. Configura PICME_CHATBOT_ADMIN_EMAILS en el archivo .env con el correo de esa cuenta. Las estadísticas agregadas sí están disponibles.",
                        "To check another person's entry history or registration date, sign in with an authorized account. Set PICME_CHATBOT_ADMIN_EMAILS in .env to that account's email. Aggregate statistics are still available.", english,
                    )
                people = conn.execute("SELECT id, nombre, creado_en FROM usuario ORDER BY id").fetchall()
                matching = [p for p in people if normalize(p["nombre"]) and normalize(p["nombre"]) in q]
                if asks_registration_date:
                    if not matching:
                        return self._answer("Indica el nombre completo de la persona cuya fecha de registro quieres consultar.",
                                             "Provide the full name of the person whose registration date you want to check.", english)
                    if len(matching) > 1:
                        return self._answer("Encontré varias coincidencias. Escribe el nombre completo.",
                                             "I found multiple matches. Please provide the full name.", english)
                    p = matching[0]
                    return self._answer(f"{p['nombre']} se registró el {_format_timestamp(p['creado_en'])}.",
                                         f"{p['nombre']} registered on {_format_timestamp(p['creado_en'])}.", english)
                if asks_person_entry and not matching:
                    return self._answer("Indica el nombre completo de la persona cuyo ingreso quieres consultar.",
                                         "Provide the full name of the person whose entry you want to check.", english)
                if asks_person_entry and len(matching) > 1:
                    return self._answer("Encontré varias coincidencias. Escribe el nombre completo.",
                                         "I found multiple matches. Please provide the full name.", english)
                if asks_person_entry:
                    p = matching[0]
                    row = conn.execute("SELECT creado_en, resultado FROM ingreso WHERE usuario_id = ? ORDER BY id DESC LIMIT 1", (p["id"],)).fetchone()
                    if not row:
                        return self._answer(f"No hay ingresos registrados para {p['nombre']}.",
                                             f"There are no entry events recorded for {p['nombre']}.", english)
                    return self._answer(f"El último ingreso registrado de {p['nombre']} fue el {_format_timestamp(row['creado_en'])}. Resultado: {row['resultado']}.",
                                         f"{p['nombre']}'s latest recorded entry was on {_format_timestamp(row['creado_en'])}. Result: {row['resultado']}.", english)
                if "hoy" in words or "today" in words:
                    start, end = _local_day_bounds()
                    rows = conn.execute("SELECT u.nombre, i.creado_en, i.resultado FROM ingreso i LEFT JOIN usuario u ON u.id = i.usuario_id WHERE i.creado_en >= ? AND i.creado_en < ? ORDER BY i.id DESC LIMIT 50", (start, end)).fetchall()
                else:
                    rows = conn.execute("SELECT u.nombre, i.creado_en, i.resultado FROM ingreso i LEFT JOIN usuario u ON u.id = i.usuario_id ORDER BY i.id DESC LIMIT 10").fetchall()
                if not rows:
                    return self._answer("Todavía no hay eventos de ingreso registrados.",
                                         "There are no entry events recorded yet.", english)
                if english:
                    lines = [f"{r['nombre'] or 'Unknown user'} — {_format_timestamp(r['creado_en'])} — {r['resultado']}" for r in rows]
                    return "Latest PicMe entry events:\n" + "\n".join(lines)
                lines = [f"{r['nombre'] or 'Usuario desconocido'} — {_format_timestamp(r['creado_en'])} — {r['resultado']}" for r in rows]
                return "Últimos eventos de ingreso en PicMe:\n" + "\n".join(lines)

            return None
        except sqlite3.Error:
            return self._answer("No pude consultar la base de datos de PicMe. Ejecuta el diagnóstico para revisar el archivo data/picme.db.",
                                 "I could not query PicMe's database. Run the diagnostic tool to check data/picme.db.", english)
        finally:
            conn.close()
