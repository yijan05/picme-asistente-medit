"""
Configuración básica del backend de PicMe.
"""

import os


HOST = os.getenv("PICME_HOST", "0.0.0.0")
PORT = int(os.getenv("PICME_PORT", "8000"))

JWT_SECRET = os.getenv(
    "PICME_JWT_SECRET",
    "picme-development-secret-change-me",
)

JWT_ALGORITHM = os.getenv(
    "PICME_JWT_ALGORITHM",
    "HS256",
)

JWT_EXPIRATION_MINUTES = int(
    os.getenv(
        "PICME_JWT_EXPIRATION_MINUTES",
        "60",
    )
)