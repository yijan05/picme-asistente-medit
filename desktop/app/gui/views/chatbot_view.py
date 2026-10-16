"""Interfaz del asistente local. Solo requiere Tkinter y SQLite."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import webbrowser
import queue
import threading

from ... import auth
from ...chatbot.rag import RagAssistant
from .. import theme


class ChatbotView(tk.Frame):
    def __init__(self, master: tk.Misc, app, **kwargs):
        super().__init__(master, bg=theme.COLOR_BG, **kwargs)
        self.app = app
        self.bot = RagAssistant()
        self._links: list[str] = []
        self._active = True
        self._busy = False
        self._after_id = None
        self._results = queue.SimpleQueue()

        header = tk.Frame(self, bg=theme.COLOR_BG)
        header.pack(fill="x", padx=24, pady=(20, 8))
        ttk.Label(header, text="Asistente UCundinamarca", style="Heading.TLabel").pack(side="left")
        self.new_button = ttk.Button(header, text="Nueva conversación", style="Secondary.TButton",
                                     command=self._clear)
        self.new_button.pack(side="right")
        if not getattr(app, "chatbot_only", False):
            ttk.Button(header, text="Volver", style="Secondary.TButton",
                       command=self._back).pack(side="right", padx=8)
        ttk.Label(self, text="MEDIT · Declaración Persona Transhumana · Seccional Ubaté",
                  style="Subheading.TLabel").pack(anchor="w", padx=24)
        mode = ("Gemini activado: se envían la pregunta y fragmentos de conocimiento al proveedor."
                if self.bot.mode == "gemini" else "Consulta local. Para usar el LLM, configura GEMINI_API_KEY en .env.")
        self.mode_var = tk.StringVar(value=mode)
        ttk.Label(self, textvariable=self.mode_var,
                  style="Muted.TLabel").pack(anchor="w", padx=24, pady=(4, 12))

        self.transcript = ScrolledText(
            self, wrap="word", font=theme.FONT_NORMAL, bg=theme.COLOR_BG_ALT,
            fg=theme.COLOR_TEXT, relief="flat", padx=18, pady=14, height=14, state="disabled",
        )
        self.transcript.pack(fill="both", expand=True, padx=24)
        self.transcript.tag_configure("speaker", foreground=theme.COLOR_ACCENT_DARK, font=theme.FONT_BUTTON)
        self.transcript.tag_configure("source", foreground=theme.COLOR_ACCENT_DARK, underline=True)

        quick = tk.Frame(self, bg=theme.COLOR_BG)
        quick.pack(fill="x", padx=24, pady=(10, 8))
        for label, question in [
            ("¿Qué es MEDIT?", "¿Qué es el MEDIT?"),
            ("Los 12 principios", "Muéstrame los 12 principios"),
            ("Ejemplo: principio 6", "Explícame el principio 6"),
        ]:
            ttk.Button(quick, text=label, style="Secondary.TButton",
                       command=lambda q=question: self.send(q)).pack(side="left", padx=(0, 8))

        composer = tk.Frame(self, bg=theme.COLOR_BG)
        composer.pack(fill="x", padx=24, pady=(0, 18))
        self.question_var = tk.StringVar()
        self.entry = ttk.Entry(composer, textvariable=self.question_var)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self._enter)
        self.send_button = ttk.Button(composer, text="Enviar", style="Accent.TButton", command=self.send)
        self.send_button.pack(side="right")
        self._welcome()
        self.after_idle(self.entry.focus_set)

    def _append(self, speaker: str, text: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", speaker + "\n", "speaker")
        self.transcript.insert("end", text + "\n\n")
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def _welcome(self) -> None:
        self._append("PicMe", "Hola. Puedo explicarte el MEDIT y los doce principios de la declaración. "
                     "Prueba: «¿Qué significa me valoro y cuido?» o «Explícame el principio 9».")

    def _enter(self, event=None) -> str:
        self.send()
        return "break"

    def send(self, question: str | None = None) -> None:
        if self._busy or not self._active:
            return
        question = self.question_var.get() if question is None else question
        if not question.strip():
            return
        if len(question) > self.bot.MAX_QUESTION_LENGTH:
            self._append("PicMe", "Usa una pregunta de hasta 2000 caracteres.")
            return
        self.question_var.set("")
        self._append("Tú", question)
        if self.bot.mode == "local":
            self._display_answer(self.bot.ask(question))
            return
        self._busy = True
        self.send_button.configure(state="disabled")
        self.new_button.configure(state="disabled")
        self.mode_var.set("Consultando el conocimiento y Gemini…")
        def work():
            try:
                self._results.put(self.bot.ask(question))
            except Exception:
                self._results.put(None)
        threading.Thread(target=work, daemon=True).start()
        self._after_id = self.after(60, self._poll_result)

    def _poll_result(self) -> None:
        self._after_id = None
        if not self._active:
            return
        try:
            answer = self._results.get_nowait()
        except queue.Empty:
            self._after_id = self.after(60, self._poll_result)
            return
        self._busy = False
        self.send_button.configure(state="normal")
        self.new_button.configure(state="normal")
        if answer is None:
            self._append("PicMe", "No se pudo procesar la consulta. Intenta de nuevo.")
            self.mode_var.set("Consulta interrumpida")
        else:
            self._display_answer(answer)

    def _display_answer(self, answer) -> None:
        label = f"Gemini · {answer.modelo}" if answer.llm_usado else "Consulta local"
        if answer.modo == "local_respaldo":
            label = "Consulta local · respaldo de la API"
        self.mode_var.set(label)
        self._append("PicMe · " + label, answer.texto)
        if answer.fuentes:
            self.transcript.configure(state="normal")
            for source in answer.fuentes:
                url = source.get("url") or source.get("fuente_url")
                tag = f"link_{len(self._links)}"
                self._links.append(url)
                self.transcript.tag_configure(tag, foreground=theme.COLOR_ACCENT_DARK, underline=True)
                self.transcript.tag_bind(tag, "<Button-1>", lambda event, u=url: webbrowser.open(u))
                self.transcript.tag_bind(tag, "<Enter>", lambda event: self.transcript.configure(cursor="hand2"))
                self.transcript.tag_bind(tag, "<Leave>", lambda event: self.transcript.configure(cursor="xterm"))
                self.transcript.insert("end", f"Fuente: {source['titulo']}\n{url}\n\n", tag)
            self.transcript.configure(state="disabled")
        if answer.sugerencias:
            self._append("Puedes preguntar", "\n".join("• " + q for q in answer.sugerencias))
        self.transcript.see("end")

    def _clear(self) -> None:
        if self._busy:
            return
        self.bot.reset()
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        for i in range(len(self._links)):
            self.transcript.tag_delete(f"link_{i}")
        self._links.clear()
        self.transcript.configure(state="disabled")
        self._welcome()

    def _back(self) -> None:
        if auth.current_user() is not None:
            from .dashboard_view import DashboardView
            self.app.show_view(DashboardView)
        else:
            from .home_view import HomeView
            self.app.show_view(HomeView)

    def on_leave(self) -> None:
        self._active = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
