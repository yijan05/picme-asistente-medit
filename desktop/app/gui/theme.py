"""
Paleta y estilos de la interfaz: fondo blanco, acentos en verde (los
mismos tonos del logo de PicMe), sin bordes ni sombras innecesarias.

Se usan únicamente opciones de `ttk.Style` que son estables entre
versiones de Tk (background, foreground, font, padding, relief,
borderwidth) para evitar depender de detalles específicos de un tema que
puedan no existir en la instalación de Tk de cada máquina.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

COLOR_BG = "#FFFFFF"
COLOR_BG_ALT = "#F2F8F3"        # verde muy claro, para tarjetas/paneles
COLOR_ACCENT = "#43A047"         # verde principal (marca PicMe)
COLOR_ACCENT_DARK = "#2E7D32"
COLOR_ACCENT_LIGHT = "#DCEEDD"
COLOR_TEXT = "#1B1F1C"
COLOR_TEXT_MUTED = "#66766B"
COLOR_BORDER = "#DCE5DE"
COLOR_DANGER = "#C0392B"
COLOR_ON_ACCENT = "#FFFFFF"

FONT_FAMILY = "Segoe UI"
FONT_NORMAL = (FONT_FAMILY, 10)
FONT_MUTED = (FONT_FAMILY, 9)
FONT_HEADING = (FONT_FAMILY, 18, "bold")
FONT_SUBHEADING = (FONT_FAMILY, 12, "bold")
FONT_BUTTON = (FONT_FAMILY, 10, "bold")


def apply(root: tk.Misc) -> None:
    """Configura los estilos globales. Llamar una sola vez, al crear la
    ventana principal."""
    style = ttk.Style(root)
    # 'clam' es el tema ttk más flexible para recolorear a fondo sin
    # depender del tema nativo del sistema operativo.
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass  # si 'clam' no está disponible, se sigue con el tema por defecto

    style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_NORMAL)

    style.configure("TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_BG_ALT)

    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_NORMAL)
    style.configure("Card.TLabel", background=COLOR_BG_ALT, foreground=COLOR_TEXT, font=FONT_NORMAL)
    style.configure("Muted.TLabel", background=COLOR_BG, foreground=COLOR_TEXT_MUTED, font=FONT_MUTED)
    style.configure("CardMuted.TLabel", background=COLOR_BG_ALT, foreground=COLOR_TEXT_MUTED, font=FONT_MUTED)
    style.configure("Heading.TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_HEADING)
    style.configure("Subheading.TLabel", background=COLOR_BG, foreground=COLOR_ACCENT_DARK, font=FONT_SUBHEADING)
    style.configure("Error.TLabel", background=COLOR_BG, foreground=COLOR_DANGER, font=FONT_MUTED)
    style.configure("Accent.TLabel", background=COLOR_BG, foreground=COLOR_ACCENT_DARK, font=FONT_BUTTON)

    style.configure(
        "Accent.TButton",
        background=COLOR_ACCENT,
        foreground=COLOR_ON_ACCENT,
        font=FONT_BUTTON,
        borderwidth=0,
        padding=(18, 10),
    )
    style.map(
        "Accent.TButton",
        background=[("active", COLOR_ACCENT_DARK), ("disabled", COLOR_ACCENT_LIGHT)],
        foreground=[("disabled", COLOR_TEXT_MUTED)],
    )

    style.configure(
        "Secondary.TButton",
        background=COLOR_BG,
        foreground=COLOR_ACCENT_DARK,
        font=FONT_NORMAL,
        borderwidth=1,
        relief="solid",
        padding=(16, 9),
    )
    style.map("Secondary.TButton", background=[("active", COLOR_BG_ALT)])

    style.configure("TEntry", fieldbackground=COLOR_BG, foreground=COLOR_TEXT, padding=8)

    style.configure(
        "Horizontal.TProgressbar",
        troughcolor=COLOR_BG_ALT,
        background=COLOR_ACCENT,
    )

    style.configure(
        "Treeview",
        background=COLOR_BG,
        fieldbackground=COLOR_BG,
        foreground=COLOR_TEXT,
        rowheight=28,
        font=FONT_NORMAL,
    )
    style.configure("Treeview.Heading", background=COLOR_BG_ALT, foreground=COLOR_TEXT, font=FONT_SUBHEADING)
    style.map("Treeview", background=[("selected", COLOR_ACCENT_LIGHT)], foreground=[("selected", COLOR_TEXT)])

    root.configure(background=COLOR_BG)
