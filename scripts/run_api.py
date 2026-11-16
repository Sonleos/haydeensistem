#!/usr/bin/env python
"""Arranca la API de Haydeén Sistema leyendo api/.env.

Uso normal (desde la raíz):
    api\\.venv\\Scripts\\python.exe scripts\\run_api.py

También lo usa iniciar_api.bat. No requiere PowerShell ni activar .venv.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "api"

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

os.chdir(API_DIR)

from config import settings  # noqa: E402
from db import db  # noqa: E402


def main() -> int:
    if not (API_DIR / ".env").exists():
        print("[ERROR] No existe api\\.env.")
        print("Ejecuta primero:")
        print("  api\\.venv\\Scripts\\python.exe scripts\\init_db.py")
        return 1

    try:
        db.ping()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR MySQL] {type(exc).__name__}: {exc}")
        print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
        print(f"Usuario: {settings.DB_USER}")
        print(f"Base: {settings.DB_NAME}")
        print("Revisa que Laragon esté encendido y que api\\.env sea correcto.")
        return 1

    try:
        import uvicorn  # noqa: PLC0415
    except ImportError:
        print("[ERROR] Falta Uvicorn. Instala las dependencias:")
        print("  api\\.venv\\Scripts\\python.exe -m pip install -r api\\requirements.txt")
        return 1

    host = settings.API_HOST
    port = settings.API_PORT
    display = "127.0.0.1" if host in {"0.0.0.0", "::"} else host

    print()
    print("=" * 68)
    print(" Haydeén Sistema · API")
    print("=" * 68)
    print(f" API:      http://{display}:{port}")
    print(f" Docs:     http://{display}:{port}/docs")
    print(f" Web móvil: http://{display}:{port}/app/")
    print(" Ctrl+C para detener.")
    print()

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info",
        app_dir=str(API_DIR),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
