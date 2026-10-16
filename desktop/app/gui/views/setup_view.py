from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from ... import model_downloader
from .. import theme


class SetupRequiredView(tk.Frame):
    """
    Pantalla que aparece cuando falta `face_landmarker.task`. Permite
    descargarlo con un botón (barra de progreso incluida) en vez de tener
    que abrir una terminal.

    La descarga corre en un hilo aparte para no congelar la ventana; ese
    hilo NUNCA toca widgets de Tkinter directamente (Tkinter no es
    thread-safe) — solo actualiza un diccionario compartido, que esta
    vista revisa periódicamente desde el hilo principal con `after()`.
    """

    def __init__(self, master: tk.Misc, app, next_view_class=None, **kwargs):
        super().__init__(master, bg=theme.COLOR_BG, **kwargs)
        self.app = app
        self.next_view_class = next_view_class
        self._progress_state: dict = {}
        self._build_layout()

    def _build_layout(self) -> None:
        wrapper = tk.Frame(self, bg=theme.COLOR_BG)
        wrapper.place(relx=0.5, rely=0.42, anchor="center")

        ttk.Label(wrapper, text="Falta un archivo necesario", style="Heading.TLabel", anchor="center").pack(
            pady=(0, 10)
        )
        ttk.Label(
            wrapper,
            text=(
                "PicMe necesita el modelo de reconocimiento facial de MediaPipe\n"
                "(un archivo de unos pocos MB) que se descarga una sola vez.\n"
                "Necesitas conexión a internet para este paso."
            ),
            style="Muted.TLabel",
            justify="center",
        ).pack(pady=(0, 20))

        self.status_var = tk.StringVar(value="")
        ttk.Label(wrapper, textvariable=self.status_var, style="Muted.TLabel").pack(pady=(0, 6))

        self.progress = ttk.Progressbar(
            wrapper, style="Horizontal.TProgressbar", length=340, maximum=100, value=0
        )
        self.progress.pack(pady=(0, 18))

        self.download_button = ttk.Button(
            wrapper, text="Descargar modelo ahora", style="Accent.TButton", command=self._start_download
        )
        self.download_button.pack()

        self.error_var = tk.StringVar(value="")
        ttk.Label(wrapper, textvariable=self.error_var, style="Error.TLabel", justify="center").pack(pady=(14, 0))

        ttk.Button(wrapper, text="Volver al inicio", style="Secondary.TButton", command=self._volver).pack(
            pady=(18, 0)
        )

    # ------------------------------------------------------------------
    def _start_download(self) -> None:
        self.download_button.state(["disabled"])
        self.error_var.set("")
        self.status_var.set("Conectando…")
        self.progress["value"] = 0

        self._progress_state = {"downloaded": 0, "total": 0, "done": False, "error": None}
        thread = threading.Thread(target=self._download_worker, daemon=True)
        thread.start()
        self.after(150, self._poll_progress)

    def _download_worker(self) -> None:
        def on_progress(downloaded: int, total: int) -> None:
            self._progress_state["downloaded"] = downloaded
            self._progress_state["total"] = total

        try:
            model_downloader.download_model(progress_callback=on_progress)
            self._progress_state["done"] = True
        except model_downloader.ModelDownloadError as exc:
            self._progress_state["error"] = str(exc)
        except Exception as exc:  # cualquier otro fallo inesperado, igual se muestra en vez de tumbar el hilo en silencio
            self._progress_state["error"] = str(exc)

    def _poll_progress(self) -> None:
        state = self._progress_state

        if state.get("error"):
            self.error_var.set(f"No se pudo descargar: {state['error']}")
            self.status_var.set("")
            self.download_button.state(["!disabled"])
            return

        total = state.get("total", 0)
        downloaded = state.get("downloaded", 0)
        if total > 0:
            pct = int(100 * downloaded / total)
            self.progress["value"] = pct
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_var.set(f"Descargando… {pct}% ({mb_downloaded:.1f} / {mb_total:.1f} MB)")
        else:
            self.status_var.set("Descargando…")

        if state.get("done"):
            self.status_var.set("¡Listo!")
            self.progress["value"] = 100
            self.after(500, self._continuar)
            return

        self.after(150, self._poll_progress)

    def _continuar(self) -> None:
        target = self.next_view_class
        if target is None:
            from .home_view import HomeView

            target = HomeView
        self.app.show_view(target)

    def _volver(self) -> None:
        from .home_view import HomeView

        self.app.show_view(HomeView)
