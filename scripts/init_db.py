#!/usr/bin/env python
"""Inicialización completa de Haydeén Sistema.

Un solo comando crea el entorno, la base de datos, el esquema, las
migraciones, los datos demo y los usuarios base:

    api\\.venv\\Scripts\\python.exe scripts\\init_db.py

Es idempotente: si la base ya existe no vuelve a ejecutar `schema.sql`
(destructivo). Para recrear todo desde cero usa `--reset`.

Otros usos:

    api\\.venv\\Scripts\\python.exe scripts\\init_db.py --check
    api\\.venv\\Scripts\\python.exe scripts\\init_db.py --list
    api\\.venv\\Scripts\\python.exe scripts\\init_db.py --reset
    api\\.venv\\Scripts\\python.exe scripts\\init_db.py --no-demo
    api\\.venv\\Scripts\\python.exe scripts\\init_db.py --reset-passwords
    api\\.venv\\Scripts\\python.exe scripts\\init_db.py --export-seed
    api\\.venv\\Scripts\\python.exe scripts\\init_db.py --import-seed

No requiere PowerShell, mysql.exe ni activar el entorno virtual.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import string
import sys
import time
import traceback
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "api"
ENV_PATH = API_DIR / ".env"
ENV_EXAMPLE = API_DIR / ".env.example"

SCHEMA_PATH = ROOT / "database" / "schema.sql"
DEMO_PATH = ROOT / "database" / "demo_data.sql"
MIGRATIONS_DIR = ROOT / "database" / "migrations"
DEFAULT_EXPORT = ROOT / "database" / "seeds" / "initial_data.json"

SEED_VERSION = 1
MIN_PASSWORD_LENGTH = 12

# Tablas mínimas para considerar que el esquema ya está creado.
CORE_TABLES = {
    "roles",
    "personal",
    "usuarios",
    "pacientes",
    "medicamentos",
    "inventario_lotes",
    "tratamientos",
    "signos_vitales",
}

ROLES: dict[str, str] = {
    "admin": "Administración general del sistema",
    "medico": "Valoración y prescripción médica",
    "enfermeria": "Cuidados y registro de signos vitales",
    "administrativo": "Inventario, personal y gestión administrativa",
    "farmacia": "Gestión de inventario y surtido",
    "recepcion": "Atención a familiares y admisión",
}

PERMISSIONS: dict[str, list[str]] = {
    "admin": ["*"],
    "medico": [
        "dashboard:leer",
        "pacientes:leer",
        "personal:leer",
        "inventario:leer",
        "tratamientos:leer",
        "tratamientos:escribir",
        "control:leer",
        "administracion:escribir",
    ],
    "enfermeria": [
        "dashboard:leer",
        "pacientes:leer",
        "inventario:leer",
        "tratamientos:leer",
        "control:leer",
        "control:escribir",
        "administracion:escribir",
    ],
    "administrativo": [
        "dashboard:leer",
        "pacientes:leer",
        "personal:leer",
        "personal:escribir",
        "inventario:leer",
        "inventario:escribir",
    ],
    "farmacia": [
        "dashboard:leer",
        "pacientes:leer",
        "inventario:leer",
        "inventario:escribir",
        "tratamientos:leer",
    ],
    "recepcion": [
        "dashboard:leer",
        "pacientes:leer",
        "personal:leer",
    ],
}

USERS: list[dict[str, str]] = [
    {
        "username": "admin",
        "rol": "admin",
        "nombre": "Administrador",
        "apellidos": "del Sistema",
        "documento": "SEED-ADMIN",
        "email": "admin@example.local",
        "arg": "admin",
        "env": "SEED_ADMIN_PASSWORD",
    },
    {
        "username": "medico",
        "rol": "medico",
        "nombre": "Médico",
        "apellidos": "Demo",
        "documento": "SEED-MED",
        "email": "medico@example.local",
        "arg": "medico",
        "env": "SEED_MEDICO_PASSWORD",
    },
    {
        "username": "enfermero",
        "rol": "enfermeria",
        "nombre": "Enfermero",
        "apellidos": "Demo",
        "documento": "SEED-ENF",
        "email": "enfermero@example.local",
        "arg": "enfermero",
        "env": "SEED_ENFERMERO_PASSWORD",
    },
    {
        "username": "administrativo",
        "rol": "administrativo",
        "nombre": "Administrativo",
        "apellidos": "Demo",
        "documento": "SEED-ADM",
        "email": "administrativo@example.local",
        "arg": "administrativo",
        "env": "SEED_ADMINISTRATIVO_PASSWORD",
    },
]

settings = None
db = None
hash_password = None


# ---------------------------------------------------------------------------
# Entorno
# ---------------------------------------------------------------------------

def _write_env(text: str) -> None:
    with ENV_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def ensure_env_file() -> None:
    """Crea api/.env si no existe y genera SECRET_KEY si está vacía."""
    if not ENV_PATH.exists():
        if not ENV_EXAMPLE.exists():
            raise SystemExit(
                f"No existe {ENV_EXAMPLE}. Restaura la plantilla del repositorio."
            )
        text = ENV_EXAMPLE.read_text(encoding="utf-8")
        _write_env(text)
        print(f"[env] Creado {ENV_PATH.relative_to(ROOT)} desde .env.example")

    text = ENV_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    changed = False
    found = False

    for index, line in enumerate(lines):
        if line.strip().startswith("SECRET_KEY="):
            found = True
            value = line.split("=", 1)[1].strip()
            if not value:
                lines[index] = f"SECRET_KEY={secrets.token_hex(32)}"
                changed = True
            break

    if not found:
        lines.append(f"SECRET_KEY={secrets.token_hex(32)}")
        changed = True

    if changed:
        _write_env("\n".join(lines) + "\n")
        print("[env] SECRET_KEY generada automáticamente")


def bootstrap() -> None:
    """Carga configuración y utilidades reales del proyecto."""
    global settings, db, hash_password

    ensure_env_file()

    if str(API_DIR) not in sys.path:
        sys.path.insert(0, str(API_DIR))

    from config import settings as _settings  # noqa: PLC0415
    from db import db as _db  # noqa: PLC0415
    from security import hash_password as _hash_password  # noqa: PLC0415

    settings = _settings
    db = _db
    hash_password = _hash_password
    _validate_db_name()


# ---------------------------------------------------------------------------
# Conexión y SQL
# ---------------------------------------------------------------------------

def _pymysql():
    try:
        import pymysql  # noqa: PLC0415
    except ImportError as exc:
        raise SystemExit(
            "Falta PyMySQL. Instala las dependencias con:\n"
            "  api\\.venv\\Scripts\\python.exe -m pip install -r api\\requirements.txt"
        ) from exc
    return pymysql


def _connection(with_database: bool):
    pymysql = _pymysql()
    from pymysql.constants import CLIENT  # noqa: PLC0415
    from pymysql.cursors import DictCursor  # noqa: PLC0415

    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME if with_database else None,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=5,
        read_timeout=60,
        write_timeout=60,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )


def _validate_db_name() -> None:
    if not re.fullmatch(r"[A-Za-z0-9_]+", settings.DB_NAME):
        raise SystemExit(
            f"DB_NAME inválido: {settings.DB_NAME!r}. Usa solo letras, números y guion bajo."
        )


def _database_exists() -> bool:
    connection = _connection(with_database=False)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
                (settings.DB_NAME,),
            )
            return cursor.fetchone() is not None
    finally:
        connection.close()


def _create_database() -> bool:
    _validate_db_name()
    connection = _connection(with_database=False)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()
    return True


def _adapt_sql(script: str) -> str:
    """Ajusta el nombre de la base para respetar DB_NAME de api/.env."""
    script = re.sub(
        r"CREATE\s+DATABASE\s+IF\s+NOT\s+EXISTS\s+`[^`]+`",
        f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}`",
        script,
        count=1,
        flags=re.IGNORECASE,
    )
    script = re.sub(
        r"\bUSE\s+`[^`]+`\s*;",
        f"USE `{settings.DB_NAME}`;",
        script,
        count=0,
        flags=re.IGNORECASE,
    )
    return script


def _run_sql_file(connection, path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"No existe el archivo SQL: {path}")

    script = _adapt_sql(path.read_text(encoding="utf-8-sig"))
    started = time.perf_counter()
    print(f"[sql] {path.relative_to(ROOT)} ...", end="", flush=True)

    with connection.cursor() as cursor:
        cursor.execute(script)
        while cursor.nextset():
            pass

    connection.commit()
    elapsed = time.perf_counter() - started
    print(f" OK ({elapsed:.2f}s)")


def _apply_migrations(connection) -> None:
    if not MIGRATIONS_DIR.exists():
        return

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        return

    print(f"[sql] Aplicando {len(files)} migración(es) idempotente(s)")
    for path in files:
        _run_sql_file(connection, path)


# ---------------------------------------------------------------------------
# Utilidades del seed
# ---------------------------------------------------------------------------

def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Tipo no serializable: {type(value).__name__}")


def _generate_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(16))


def _resolve_password(user: dict[str, str], args: argparse.Namespace) -> tuple[str, str]:
    cli_value = getattr(args, f"password_{user['arg']}", None)
    if cli_value:
        return cli_value, "CLI"

    env_value = os.getenv(user["env"])
    if env_value:
        return env_value, "entorno"

    return _generate_password(), "generado"


def _validate_password(user: dict[str, str], password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(
            f"La contraseña de '{user['username']}' debe tener al menos "
            f"{MIN_PASSWORD_LENGTH} caracteres."
        )


def _print_header(title: str) -> None:
    print()
    print("=" * 68)
    print(f" {title}")
    print("=" * 68)


# ---------------------------------------------------------------------------
# Roles, permisos y usuarios
# ---------------------------------------------------------------------------

def _ensure_roles(cursor) -> None:
    for nombre, descripcion in ROLES.items():
        cursor.execute(
            """
            INSERT INTO roles (nombre, descripcion)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion)
            """,
            (nombre, descripcion),
        )


def _role_id(cursor, nombre: str) -> int:
    cursor.execute("SELECT id FROM roles WHERE nombre = %s", (nombre,))
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"No existe el rol '{nombre}'")
    return int(row["id"])


def _ensure_permissions(cursor) -> None:
    for rol, permisos in PERMISSIONS.items():
        rol_id = _role_id(cursor, rol)
        cursor.execute("DELETE FROM rol_permisos WHERE rol_id = %s", (rol_id,))
        for permiso in permisos:
            cursor.execute(
                "INSERT INTO rol_permisos (rol_id, permiso) VALUES (%s, %s)",
                (rol_id, permiso),
            )


def _ensure_personal(cursor, user: dict[str, str], rol_id: int) -> int:
    cursor.execute(
        "SELECT id FROM personal WHERE documento = %s LIMIT 1",
        (user["documento"],),
    )
    row = cursor.fetchone()
    if row:
        return int(row["id"])

    cursor.execute(
        """
        INSERT INTO personal
          (nombre, apellidos, documento, email, rol_id, estado, fecha_ingreso, notas)
        VALUES (%s, %s, %s, %s, %s, 'activo', CURDATE(), %s)
        """,
        (
            user["nombre"],
            user["apellidos"],
            user["documento"],
            user["email"],
            rol_id,
            "Registro creado por init_db.py",
        ),
    )
    return int(cursor.lastrowid)


def _ensure_user(
    cursor,
    user: dict[str, str],
    rol_id: int,
    personal_id: int,
    password: str,
    reset: bool,
) -> tuple[str, str | None]:
    cursor.execute(
        "SELECT id FROM usuarios WHERE username = %s LIMIT 1",
        (user["username"],),
    )
    row = cursor.fetchone()

    if row:
        if not reset:
            return "sin cambios", None
        cursor.execute(
            """
            UPDATE usuarios
               SET password_hash = %s, rol_id = %s, personal_id = %s, activo = 1
             WHERE id = %s
            """,
            (hash_password(password), rol_id, personal_id, row["id"]),
        )
        return "contraseña rotada", password

    cursor.execute(
        """
        INSERT INTO usuarios (personal_id, rol_id, username, password_hash, activo)
        VALUES (%s, %s, %s, %s, 1)
        """,
        (personal_id, rol_id, user["username"], hash_password(password)),
    )
    return "creado", password


def apply_seed(reset_passwords: bool, args: argparse.Namespace) -> int:
    _print_header("USUARIOS · Roles, permisos y usuarios base")

    resolved: list[tuple[dict[str, str], str]] = []
    for user in USERS:
        password, _origin = _resolve_password(user, args)
        _validate_password(user, password)
        resolved.append((user, password))

    results: list[tuple[str, str, str, str | None]] = []

    with db.cursor(commit=True) as cursor:
        _ensure_roles(cursor)
        _ensure_permissions(cursor)

        for user, password in resolved:
            rol_id = _role_id(cursor, user["rol"])
            personal_id = _ensure_personal(cursor, user, rol_id)
            estado, shown = _ensure_user(
                cursor, user, rol_id, personal_id, password, reset_passwords
            )
            results.append((user["username"], user["rol"], estado, shown))

    print(f"{'USUARIO':<16} {'ROL':<16} {'ESTADO':<18} CONTRASEÑA")
    print("-" * 68)
    for username, rol, estado, shown in results:
        print(f"{username:<16} {rol:<16} {estado:<18} {shown or '(sin cambios)'}")

    generated = [r for r in results if r[3] and r[2] in {"creado", "contraseña rotada"}]
    if generated:
        print()
        print("Guarda estas contraseñas ahora. No se vuelven a mostrar ni se")
        print("almacenan en texto plano. Cámbialas tras el primer acceso.")

    if any(r[2] == "sin cambios" for r in results):
        print()
        print("Los usuarios existentes conservaron su contraseña.")
        print("Usa --reset-passwords para rotarlas.")

    print()
    print(f"Roles: {len(ROLES)} · Usuarios: {len(USERS)} · BD: {settings.DB_NAME}")
    return 0


# ---------------------------------------------------------------------------
# Exportar / importar seed
# ---------------------------------------------------------------------------

def export_seed(path: Path) -> int:
    _print_header("EXPORT · Seed JSON anonimizado")

    roles = db.fetch_all("SELECT nombre, descripcion FROM roles ORDER BY id")

    permisos: dict[str, list[str]] = {}
    for row in db.fetch_all(
        """
        SELECT r.nombre AS rol, rp.permiso
          FROM rol_permisos rp
          JOIN roles r ON r.id = rp.rol_id
         ORDER BY r.nombre, rp.permiso
        """
    ):
        permisos.setdefault(row["rol"], []).append(row["permiso"])

    usuarios = db.fetch_all(
        """
        SELECT u.username,
               r.nombre AS rol,
               u.password_hash,
               u.activo,
               p.nombre,
               p.apellidos,
               p.documento,
               p.email
          FROM usuarios u
          JOIN roles r ON r.id = u.rol_id
          LEFT JOIN personal p ON p.id = u.personal_id
         ORDER BY u.username
        """
    )

    medicamentos = db.fetch_all(
        """
        SELECT nombre, principio_activo, presentacion, concentracion, unidad,
               stock_minimo, requiere_refrigeracion, activo
          FROM medicamentos
         ORDER BY nombre, concentracion
        """
    )

    lotes = db.fetch_all(
        """
        SELECT m.nombre AS medicamento,
               m.concentracion,
               l.codigo_lote,
               l.cantidad_inicial,
               l.cantidad_disponible,
               l.fecha_caducidad,
               l.fecha_ingreso,
               l.proveedor,
               l.costo_unitario
          FROM inventario_lotes l
          JOIN medicamentos m ON m.id = l.medicamento_id
         ORDER BY m.nombre, l.codigo_lote
        """
    )

    # Solo pacientes con documento de demostración. El seed nunca arrastra
    # identificadores de personas reales y sigue siendo idempotente.
    pacientes_rows = db.fetch_all(
        """
        SELECT documento, fecha_nacimiento, sexo, tipo_residencia, habitacion,
               cama, alergias, diagnostico, peso_kg, talla_m, estado,
               fecha_ingreso
          FROM pacientes
         WHERE documento LIKE 'PAC-%' OR documento LIKE 'DEMO-%'
         ORDER BY documento
        """
    )

    pacientes = []
    for index, row in enumerate(pacientes_rows, start=1):
        pacientes.append(
            {
                "documento": row["documento"],
                "nombre": "Paciente",
                "apellidos": f"Demo {index:03d}",
                "fecha_nacimiento": row["fecha_nacimiento"],
                "sexo": row["sexo"],
                "tipo_residencia": row["tipo_residencia"],
                "habitacion": row["habitacion"],
                "cama": row["cama"],
                "contacto_familiar": None,
                "telefono_contacto": None,
                "alergias": row["alergias"],
                "diagnostico": row["diagnostico"],
                "peso_kg": row["peso_kg"],
                "talla_m": row["talla_m"],
                "estado": row["estado"],
                "fecha_ingreso": row["fecha_ingreso"],
            }
        )

    payload = {
        "meta": {
            "sistema": "Haydeén Sistema",
            "version": SEED_VERSION,
            "exportado_en": datetime.now().isoformat(timespec="seconds"),
            "anonimizado": True,
            "advertencia": (
                "Contiene hashes PBKDF2 de usuarios. No lo publiques ni lo "
                "compartas fuera del equipo autorizado."
            ),
        },
        "roles": roles,
        "permisos": permisos,
        "usuarios": usuarios,
        "medicamentos": medicamentos,
        "lotes": lotes,
        "pacientes": pacientes,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=_json_default)
        handle.write("\n")

    print(f"Archivo: {path}")
    print(
        f"Roles: {len(roles)} · Usuarios: {len(usuarios)} · "
        f"Medicamentos: {len(medicamentos)} · Lotes: {len(lotes)} · "
        f"Pacientes anonimizados: {len(pacientes)}"
    )
    print()
    print("El JSON incluye hashes de contraseñas y datos clínicos anonimizados.")
    print("Está excluido de Git por .gitignore; trátalo como material sensible.")
    return 0


def _load_seed(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"No existe el archivo de seed: {path}")

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    meta = payload.get("meta") or {}
    if meta.get("version") != SEED_VERSION:
        raise SystemExit(
            f"Versión de seed incompatible: {meta.get('version')} "
            f"(se esperaba {SEED_VERSION})."
        )
    return payload


def import_seed(path: Path) -> int:
    _print_header("IMPORT · Seed JSON")
    payload = _load_seed(path)

    counters = {
        "roles": 0,
        "permisos": 0,
        "usuarios": 0,
        "medicamentos": 0,
        "lotes": 0,
        "pacientes": 0,
    }

    with db.cursor(commit=True) as cursor:
        for role in payload.get("roles", []):
            cursor.execute(
                """
                INSERT INTO roles (nombre, descripcion)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion)
                """,
                (role["nombre"], role.get("descripcion")),
            )
            counters["roles"] += 1

        for rol, permisos in (payload.get("permisos") or {}).items():
            rol_id = _role_id(cursor, rol)
            cursor.execute("DELETE FROM rol_permisos WHERE rol_id = %s", (rol_id,))
            for permiso in permisos:
                cursor.execute(
                    "INSERT INTO rol_permisos (rol_id, permiso) VALUES (%s, %s)",
                    (rol_id, permiso),
                )
                counters["permisos"] += 1

        for user in payload.get("usuarios", []):
            rol_id = _role_id(cursor, user["rol"])
            documento = user.get("documento") or f"SEED-{user['username'].upper()}"

            cursor.execute(
                "SELECT id FROM personal WHERE documento = %s LIMIT 1",
                (documento,),
            )
            row = cursor.fetchone()
            if row:
                personal_id = int(row["id"])
            else:
                cursor.execute(
                    """
                    INSERT INTO personal
                      (nombre, apellidos, documento, email, rol_id, estado,
                       fecha_ingreso, notas)
                    VALUES (%s, %s, %s, %s, %s, 'activo', CURDATE(),
                            'Importado desde seed JSON')
                    """,
                    (
                        user.get("nombre") or "Usuario",
                        user.get("apellidos") or user["username"],
                        documento,
                        user.get("email"),
                        rol_id,
                    ),
                )
                personal_id = int(cursor.lastrowid)

            cursor.execute(
                "SELECT id FROM usuarios WHERE username = %s LIMIT 1",
                (user["username"],),
            )
            if cursor.fetchone():
                cursor.execute(
                    """
                    UPDATE usuarios
                       SET rol_id = %s, personal_id = %s, activo = %s
                     WHERE username = %s
                    """,
                    (rol_id, personal_id, int(user.get("activo", 1)), user["username"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO usuarios
                      (personal_id, rol_id, username, password_hash, activo)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        personal_id,
                        rol_id,
                        user["username"],
                        user["password_hash"],
                        int(user.get("activo", 1)),
                    ),
                )
            counters["usuarios"] += 1

        for med in payload.get("medicamentos", []):
            cursor.execute(
                """
                SELECT id FROM medicamentos
                 WHERE nombre = %s AND concentracion = %s
                 LIMIT 1
                """,
                (med["nombre"], med["concentracion"]),
            )
            if cursor.fetchone():
                continue
            cursor.execute(
                """
                INSERT INTO medicamentos
                  (nombre, principio_activo, presentacion, concentracion, unidad,
                   stock_minimo, requiere_refrigeracion, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    med["nombre"],
                    med.get("principio_activo"),
                    med.get("presentacion"),
                    med["concentracion"],
                    med.get("unidad"),
                    med.get("stock_minimo", 0),
                    int(med.get("requiere_refrigeracion", 0)),
                    int(med.get("activo", 1)),
                ),
            )
            counters["medicamentos"] += 1

        for lote in payload.get("lotes", []):
            cursor.execute(
                """
                SELECT id FROM medicamentos
                 WHERE nombre = %s AND concentracion = %s
                 LIMIT 1
                """,
                (lote["medicamento"], lote["concentracion"]),
            )
            med = cursor.fetchone()
            if not med:
                continue
            cursor.execute(
                """
                SELECT id FROM inventario_lotes
                 WHERE medicamento_id = %s AND codigo_lote = %s
                 LIMIT 1
                """,
                (med["id"], lote["codigo_lote"]),
            )
            if cursor.fetchone():
                continue
            cursor.execute(
                """
                INSERT INTO inventario_lotes
                  (medicamento_id, codigo_lote, cantidad_inicial,
                   cantidad_disponible, fecha_caducidad, fecha_ingreso,
                   proveedor, costo_unitario)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    med["id"],
                    lote["codigo_lote"],
                    lote.get("cantidad_inicial", 0),
                    lote.get("cantidad_disponible", 0),
                    lote.get("fecha_caducidad"),
                    lote.get("fecha_ingreso"),
                    lote.get("proveedor"),
                    lote.get("costo_unitario"),
                ),
            )
            counters["lotes"] += 1

        for pac in payload.get("pacientes", []):
            cursor.execute(
                "SELECT id FROM pacientes WHERE documento = %s LIMIT 1",
                (pac["documento"],),
            )
            if cursor.fetchone():
                continue
            cursor.execute(
                """
                INSERT INTO pacientes
                  (nombre, apellidos, documento, fecha_nacimiento, sexo,
                   tipo_residencia, habitacion, cama, contacto_familiar,
                   telefono_contacto, alergias, diagnostico, peso_kg, talla_m,
                   estado, fecha_ingreso)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    pac.get("nombre") or "Paciente",
                    pac.get("apellidos") or "Demo",
                    pac["documento"],
                    pac.get("fecha_nacimiento"),
                    pac.get("sexo"),
                    pac.get("tipo_residencia"),
                    pac.get("habitacion"),
                    pac.get("cama"),
                    pac.get("contacto_familiar"),
                    pac.get("telefono_contacto"),
                    pac.get("alergias"),
                    pac.get("diagnostico"),
                    pac.get("peso_kg"),
                    pac.get("talla_m"),
                    pac.get("estado", "activo"),
                    pac.get("fecha_ingreso"),
                ),
            )
            counters["pacientes"] += 1

    print(f"Archivo: {path}")
    for key, value in counters.items():
        print(f"  {key:<13} {value}")
    print()
    print("Los usuarios importados conservan el hash original del JSON.")
    return 0


# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------

def initialize(reset: bool, no_demo: bool, reset_passwords: bool, args: argparse.Namespace) -> int:
    _print_header("INIT · Haydeén Sistema")

    if reset:
        print("ATENCIÓN: --reset elimina y recrea todas las tablas.")
        print("No lo uses sobre una base con datos reales.")

    print(f"MySQL: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"Base:  {settings.DB_NAME}")
    print(f"Usuario: {settings.DB_USER}")

    if _database_exists():
        print(f"[db] La base '{settings.DB_NAME}' ya existe")
    else:
        _create_database()
        print(f"[db] Base '{settings.DB_NAME}' creada")

    connection = _connection(with_database=True)
    try:
        tables = _table_names_from(connection)
        has_schema = "roles" in tables

        if reset or not has_schema:
            _run_sql_file(connection, SCHEMA_PATH)
        else:
            missing = CORE_TABLES - tables
            if missing:
                raise SystemExit(
                    "La base existe pero faltan tablas: "
                    + ", ".join(sorted(missing))
                    + "\nUsa --reset para recrear el esquema (destructivo)."
                )
            print("[sql] Esquema existente: no se ejecuta schema.sql")

        _apply_migrations(connection)

        if no_demo:
            print("[demo] Omitido por --no-demo")
        else:
            _run_sql_file(connection, DEMO_PATH)
    finally:
        connection.close()

    apply_seed(reset_passwords, args)

    print()
    print("Listo. Siguiente paso:")
    print("  iniciar_api.bat")
    print()
    print("Web móvil: http://127.0.0.1:8000/app/")
    print("API docs:  http://127.0.0.1:8000/docs")
    return 0


def _table_names_from(connection) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name AS nombre
              FROM information_schema.tables
             WHERE table_schema = %s
            """,
            (settings.DB_NAME,),
        )
        return {row["nombre"] for row in cursor.fetchall()}


# ---------------------------------------------------------------------------
# Listado y verificación
# ---------------------------------------------------------------------------

def list_state() -> int:
    _print_header("ESTADO · Roles, permisos y usuarios")

    for row in db.fetch_all("SELECT id, nombre, descripcion FROM roles ORDER BY id"):
        print(f"\n[{row['id']}] {row['nombre']} — {row['descripcion']}")
        permisos = db.fetch_all(
            "SELECT permiso FROM rol_permisos WHERE rol_id = %s ORDER BY permiso",
            (row["id"],),
        )
        if permisos:
            for permiso in permisos:
                print(f"      · {permiso['permiso']}")
        else:
            print("      (sin permisos asignados)")

    print("\nUsuarios:")
    usuarios = db.fetch_all(
        """
        SELECT u.username, r.nombre AS rol, u.activo, u.ultimo_acceso,
               COALESCE(CONCAT_WS(' ', p.nombre, p.apellidos), '—') AS nombre
          FROM usuarios u
          JOIN roles r ON r.id = u.rol_id
          LEFT JOIN personal p ON p.id = u.personal_id
         ORDER BY u.username
        """
    )
    if not usuarios:
        print("  (ninguno; ejecuta init_db.py)")
    for row in usuarios:
        estado = "activo" if row["activo"] else "inactivo"
        print(f"  {row['username']:<16} {row['rol']:<16} {estado:<9} {row['nombre']}")
    return 0


def check_connection() -> int:
    _print_header("CHECK · Conexión y esquema")
    print(f"MySQL: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"APP_ENV: {settings.APP_ENV}")
    print(f"SECRET_KEY: {'configurada' if settings.SECRET_KEY else 'NO configurada'}")

    if not _database_exists():
        print(f"\n[ERROR] La base '{settings.DB_NAME}' no existe.")
        print("Ejecuta: api\\.venv\\Scripts\\python.exe scripts\\init_db.py")
        return 1

    connection = _connection(with_database=True)
    try:
        tables = _table_names_from(connection)
    finally:
        connection.close()

    print(f"Tablas: {len(tables)}")

    missing = CORE_TABLES - tables
    if missing:
        print("\n[ERROR] Faltan tablas: " + ", ".join(sorted(missing)))
        print("Ejecuta init_db.py o usa --reset si el esquema está corrupto.")
        return 1

    if "rol_permisos" not in tables:
        print("\n[ERROR] Falta 'rol_permisos'.")
        print("Ejecuta init_db.py para aplicar las migraciones.")
        return 1

    print("Estado: OK")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inicializa Haydeén Sistema: .env, base de datos, esquema, "
            "migraciones, demo, roles y usuarios."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  api\\.venv\\Scripts\\python.exe scripts\\init_db.py\n"
            "  api\\.venv\\Scripts\\python.exe scripts\\init_db.py --check\n"
            "  api\\.venv\\Scripts\\python.exe scripts\\init_db.py --reset\n"
            "  api\\.venv\\Scripts\\python.exe scripts\\init_db.py --export-seed\n"
        ),
    )
    parser.add_argument("--reset", action="store_true", help="Recrea el esquema (destructivo).")
    parser.add_argument("--no-demo", action="store_true", help="No carga database/demo_data.sql.")
    parser.add_argument(
        "--reset-passwords",
        action="store_true",
        help="Rota las contraseñas de los usuarios existentes.",
    )
    parser.add_argument(
        "--export-seed",
        nargs="?",
        const=str(DEFAULT_EXPORT),
        metavar="RUTA",
        help=f"Exporta un seed JSON anonimizado (por defecto: {DEFAULT_EXPORT}).",
    )
    parser.add_argument(
        "--import-seed",
        nargs="?",
        const=str(DEFAULT_EXPORT),
        metavar="RUTA",
        help="Importa un seed JSON generado con --export-seed.",
    )
    parser.add_argument("--list", action="store_true", help="Muestra roles, permisos y usuarios.")
    parser.add_argument("--check", action="store_true", help="Verifica conexión, base y tablas.")

    for user in USERS:
        parser.add_argument(
            f"--password-{user['arg']}",
            dest=f"password_{user['arg']}",
            metavar="CLAVE",
            help=(
                f"Contraseña inicial de '{user['username']}' "
                f"(mín. {MIN_PASSWORD_LENGTH} caracteres)."
            ),
        )

    return parser


def _print_error(exc: BaseException) -> None:
    print("\n" + "=" * 68, file=sys.stderr)
    print(" ERROR", file=sys.stderr)
    print("=" * 68, file=sys.stderr)
    print(f"Tipo: {type(exc).__name__}", file=sys.stderr)
    print(f"Detalle: {exc}", file=sys.stderr)

    try:
        import pymysql  # noqa: PLC0415

        if isinstance(exc, pymysql.err.OperationalError):
            print("\nNo se pudo conectar a MySQL.", file=sys.stderr)
            if settings is not None:
                print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}", file=sys.stderr)
                print(f"Usuario: {settings.DB_USER}", file=sys.stderr)
                print(f"Base: {settings.DB_NAME}", file=sys.stderr)
            print("Revisa que Laragon esté encendido y que api\\.env sea correcto.", file=sys.stderr)
    except ImportError:
        pass

    print("\nTraza completa:", file=sys.stderr)
    traceback.print_exc()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    actions = [
        args.check,
        args.list,
        args.export_seed is not None,
        args.import_seed is not None,
    ]
    if sum(bool(action) for action in actions) > 1:
        parser.error("Usa solo una acción: --check, --list, --export-seed o --import-seed.")

    try:
        bootstrap()

        if args.check:
            return check_connection()
        if args.list:
            return list_state()
        if args.export_seed is not None:
            return export_seed(Path(args.export_seed))
        if args.import_seed is not None:
            return import_seed(Path(args.import_seed))

        return initialize(
            reset=args.reset,
            no_demo=args.no_demo,
            reset_passwords=args.reset_passwords,
            args=args,
        )
    except KeyboardInterrupt:
        print("\nCancelado.", file=sys.stderr)
        return 130
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        _print_error(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
