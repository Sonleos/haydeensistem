from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


class Settings:
    APP_NAME = "Haydeén Sistema API"
    APP_VERSION = "0.1.0"

    APP_ENV = os.getenv("APP_ENV", "development").strip().lower()

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = _get_int("DB_PORT", 3306)
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "haydeensistem")
    DB_POOL_SIZE = _get_int("DB_POOL_SIZE", 5)
    DB_POOL_TIMEOUT = _get_int("DB_POOL_TIMEOUT", 10)

    SESSION_HOURS = _get_int("SESSION_HOURS", 12)
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    # Clave usada como "pepper" al hashear tokens de sesión en reposo.
    # Si cambia, todas las sesiones activas quedan invalidadas.
    SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

    API_HOST = os.getenv("API_HOST", "0.0.0.0").strip() or "0.0.0.0"
    API_PORT = _get_int("API_PORT", 8000)

    IS_PRODUCTION = APP_ENV in {"production", "prod"}

    if IS_PRODUCTION and not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY es obligatoria cuando APP_ENV=production. "
            "Genera una con: python -c \"import secrets; print(secrets.token_hex(32))\""
        )


settings = Settings()
