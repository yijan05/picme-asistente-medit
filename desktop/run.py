"""Entrada de PicMe. Uso: python run.py [--chatbot]."""
from __future__ import annotations

import argparse
import logging
import sys

from app import config, db


def main() -> None:
    parser = argparse.ArgumentParser(description="PicMe para escritorio")
    parser.add_argument("--chatbot", action="store_true", help="Abrir solo el chatbot (sin cámara)")
    args = parser.parse_args()
    config.ensure_directories()
    logging.basicConfig(
        filename=config.DATA_DIR / "picme.log", level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8",
    )
    try:
        from app.gui.app_window import AppWindow
        db.init_db()
        from app.chatbot.repository import KnowledgeRepository
        KnowledgeRepository()
        window = AppWindow(chatbot_only=args.chatbot)

        def report_callback_exception(exc_type, exc_value, exc_tb):
            logging.error("Error en la interfaz", exc_info=(exc_type, exc_value, exc_tb))
            window._show_error_dialog(exc_value)

        window.report_callback_exception = report_callback_exception
        window.mainloop()
    except Exception as exc:
        logging.exception("No se pudo iniciar PicMe")
        print(f"No se pudo iniciar PicMe: {exc}\nEjecuta DIAGNOSTICAR_WINDOWS.bat para revisar el entorno.", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
