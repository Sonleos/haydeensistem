#!/usr/bin/env python
"""Prueba rápida de Haydeén Sistema.

Verifica base de datos, API, login, endpoints principales y RBAC sin pytest
ni configuraciones adicionales:

    api\\.venv\\Scripts\\python.exe scripts\\test_sistema.py

Si la API no está levantada, este script la inicia en un puerto libre y la
detiene al terminar. Crea usuarios temporales y los elimina al final.
"""

from __future__ import annotations

import argparse
import json
import secrets
import socket
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "api"

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from config import settings  # noqa: E402
from db import db  # noqa: E402
from security import hash_password  # noqa: E402

ENDPOINTS = [
    "/api/dashboard/stats",
    "/api/pacientes",
    "/api/personal",
    "/api/inventario",
    "/api/tratamientos",
    "/api/control-diario",
]


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        if ok:
            self.passed += 1
            print(f"PASS  {name}")
        else:
            self.failed += 1
            suffix = f" -> {detail}" if detail else ""
            print(f"FAIL  {name}{suffix}")

    def summary(self) -> int:
        total = self.passed + self.failed
        print()
        print("=" * 68)
        print(f" Resultado: {self.passed}/{total} pruebas OK")
        print("=" * 68)
        return 0 if self.failed == 0 else 1


def http_request(
    method: str,
    url: str,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> tuple[int, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else None
            return response.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        return exc.code, payload
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        return 0, str(exc)


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _pick_port(preferred: int = 8000) -> int:
    for port in range(preferred, preferred + 50):
        if _port_free(port):
            return port
    raise RuntimeError("No hay puertos libres entre 8000 y 8049")


def _api_running(base_url: str) -> bool:
    status, _ = http_request("GET", f"{base_url}/api/ping", timeout=1.5)
    return status == 200


def _start_api(port: int) -> subprocess.Popen:
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    return subprocess.Popen(
        command,
        cwd=str(API_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _wait_api(base_url: str, process: subprocess.Popen | None, timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _api_running(base_url):
            return True
        if process is not None and process.poll() is not None:
            return False
        time.sleep(0.3)
    return False


def _stop_api(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _create_temp_user(rol_name: str) -> dict[str, Any]:
    role = db.fetch_one("SELECT id FROM roles WHERE nombre = %s", (rol_name,))
    if not role:
        raise RuntimeError(f"No existe el rol '{rol_name}'. Ejecuta init_db.py.")

    suffix = secrets.token_hex(4).upper()
    username = f"__test_{rol_name}_{suffix.lower()}"
    document = f"TEST-{suffix}"
    password = secrets.token_urlsafe(18)

    personal_id, _ = db.execute(
        """
        INSERT INTO personal
          (nombre, apellidos, documento, email, rol_id, estado, fecha_ingreso, notas)
        VALUES ('Prueba', %s, %s, %s, %s, 'activo', CURDATE(), 'Temporal de test_sistema.py')
        """,
        (rol_name.title(), document, f"{username}@example.local", role["id"]),
    )
    user_id, _ = db.execute(
        """
        INSERT INTO usuarios (personal_id, rol_id, username, password_hash, activo)
        VALUES (%s, %s, %s, %s, 1)
        """,
        (personal_id, role["id"], username, hash_password(password)),
    )
    return {
        "id": user_id,
        "personal_id": personal_id,
        "username": username,
        "password": password,
    }


def _delete_temp_user(user: dict[str, Any]) -> None:
    db.execute("DELETE FROM sesiones WHERE usuario_id = %s", (user["id"],))
    db.execute("DELETE FROM usuarios WHERE id = %s", (user["id"],))
    db.execute("DELETE FROM personal WHERE id = %s", (user["personal_id"],))


def _login(base_url: str, username: str, password: str) -> tuple[int, Any]:
    return http_request(
        "POST",
        f"{base_url}/api/auth/login",
        body={"username": username, "password": password},
    )


def run(args: argparse.Namespace) -> int:
    checks = Checks()
    process: subprocess.Popen | None = None
    temp_users: list[dict[str, Any]] = []
    base_url = (args.base_url or "").rstrip("/")

    if not (API_DIR / ".env").exists():
        print("[ERROR] No existe api\\.env. Ejecuta primero:")
        print("  api\\.venv\\Scripts\\python.exe scripts\\init_db.py")
        return 1

    try:
        # 1. Base de datos
        try:
            ping = db.ping()
            checks.check("MySQL conectado", ping.get("ok") == 1, str(ping))
        except Exception as exc:  # noqa: BLE001
            checks.check("MySQL conectado", False, f"{type(exc).__name__}: {exc}")
            print("\nRevisa Laragon y api\\.env. Detalle técnico:")
            traceback.print_exc()
            return checks.summary()

        # 2. API
        if base_url:
            checks.check("API disponible", _api_running(base_url), base_url)
            if not _api_running(base_url):
                return checks.summary()
        else:
            if _api_running("http://127.0.0.1:8000"):
                base_url = "http://127.0.0.1:8000"
                checks.check("API disponible", True, f"{base_url} (ya estaba activa)")
            else:
                port = _pick_port(args.port)
                process = _start_api(port)
                base_url = f"http://127.0.0.1:{port}"
                ready = _wait_api(base_url, process)
                checks.check("API disponible", ready, base_url)
                if not ready:
                    if process.stdout is not None:
                        output = process.stdout.read()
                        if output:
                            print("\nSalida de Uvicorn:")
                            print(output)
                    return checks.summary()

        # 3. Endpoints públicos
        status, payload = http_request("GET", f"{base_url}/api/ping")
        checks.check("GET /api/ping", status == 200, f"status={status}")

        status, payload = http_request("GET", f"{base_url}/api/health")
        checks.check(
            "GET /api/health",
            status == 200 and payload.get("status") == "ok",
            f"status={status} payload={payload}",
        )

        status, _ = http_request("GET", f"{base_url}/api/pacientes")
        checks.check("GET /api/pacientes sin token -> 401", status == 401, f"status={status}")

        # 4. Usuario admin temporal
        admin = _create_temp_user("admin")
        temp_users.append(admin)

        status, payload = _login(base_url, admin["username"], admin["password"])
        checks.check("Login admin", status == 200 and bool(payload.get("token")), f"status={status}")
        admin_token = payload.get("token") if isinstance(payload, dict) else None

        if admin_token:
            status, me = http_request("GET", f"{base_url}/api/auth/me", token=admin_token)
            permisos = me.get("permisos", []) if isinstance(me, dict) else []
            checks.check(
                "GET /api/auth/me (admin)",
                status == 200 and "*" in permisos,
                f"status={status} permisos={permisos}",
            )

            for endpoint in ENDPOINTS:
                status, _ = http_request("GET", f"{base_url}{endpoint}", token=admin_token)
                checks.check(f"GET {endpoint}", status == 200, f"status={status}")

        # 5. RBAC con usuario administrativo temporal
        adminis = _create_temp_user("administrativo")
        temp_users.append(adminis)

        status, payload = _login(base_url, adminis["username"], adminis["password"])
        checks.check(
            "Login administrativo",
            status == 200 and bool(payload.get("token")),
            f"status={status}",
        )
        adminis_token = payload.get("token") if isinstance(payload, dict) else None

        if adminis_token:
            status, _ = http_request("GET", f"{base_url}/api/tratamientos", token=adminis_token)
            checks.check("RBAC: tratamientos -> 403", status == 403, f"status={status}")

            status, _ = http_request("GET", f"{base_url}/api/personal", token=adminis_token)
            checks.check("RBAC: personal -> 200", status == 200, f"status={status}")

        return checks.summary()

    finally:
        for user in temp_users:
            try:
                _delete_temp_user(user)
            except Exception as exc:  # noqa: BLE001
                print(f"[aviso] No se pudo limpiar {user['username']}: {exc}")
        if process is not None:
            _stop_api(process)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prueba rápida de BD, API, login, endpoints y RBAC."
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Usa una API ya levantada, por ejemplo http://127.0.0.1:8000.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Puerto preferido si hay que iniciar la API (por defecto 8000).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run(args)
    except KeyboardInterrupt:
        print("\nCancelado.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"\n[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
