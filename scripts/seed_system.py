#!/usr/bin/env python
"""Seeder seguro de Haydeén Sistema.

Crea roles, permisos y usuarios base usando el hash PBKDF2-SHA256 real del
proyecto (`api/security.py`). No contiene contraseñas en texto plano: si no se
indican por CLI o variable de entorno, genera contraseñas aleatorias y las
muestra una sola vez.

Uso:
    python scripts/seed_system.py --apply
    python scripts/seed_system.py --apply --reset-passwords
    python scripts/seed_system.py --export-seed
    python scripts/seed_system.py --import-seed
    python scripts/seed_system.py --list
    python scripts/seed_system.py --check

Las contraseñas también pueden definirse así:
    SEED_ADMIN_PASSWORD=... SEED_MEDICO_PASSWORD=... python scripts/seed_system.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import string
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from config import settings  # noqa: E402
from db import db  # noqa: E402
from security import hash_password  # noqa: E402

SEED_VERSION = 1
DEFAULT_EXPORT = ROOT / "database" / "seeds" / "initial_data.json"
MIN_PASSWORD_LENGTH = 12

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


# ---------------------------------------------------------------------------
# Utilidades
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
# Aplicar roles, permisos y usuarios
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
            "Registro creado por seed_system.py",
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


def apply_seed(reset: bool, args: argparse.Namespace) -> int:
    _print_header("SEED · Roles, permisos y usuarios base")

    resolved: list[tuple[dict[str, str], str, str]] = []
    for user in USERS:
        password, origin = _resolve_password(user, args)
        _validate_password(user, password)
        resolved.append((user, password, origin))

    results: list[tuple[str, str, str, str | None]] = []

    try:
        with db.cursor(commit=True) as cursor:
            _ensure_roles(cursor)
            _ensure_permissions(cursor)

            for user, password, _origin in resolved:
                rol_id = _role_id(cursor, user["rol"])
                personal_id = _ensure_personal(cursor, user, rol_id)
                estado, shown = _ensure_user(
                    cursor, user, rol_id, personal_id, password, reset
                )
                results.append((user["username"], user["rol"], estado, shown))
    except Exception as exc:
        if "rol_permisos" in str(exc):
            print(
                "\nFalta la tabla 'rol_permisos'. Ejecuta la migración:\n"
                "  database/migrations/001_rol_permisos.sql\n",
                file=sys.stderr,
            )
        raise

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

    # Solo se exportan pacientes con documento de demostración (PAC-* o
    # DEMO-*). Así el seed nunca arrastra identificadores de personas reales
    # y sigue siendo idempotente al reimportarlo en la misma base.
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
    print(f"Roles: {len(roles)} · Usuarios: {len(usuarios)} · "
          f"Medicamentos: {len(medicamentos)} · Lotes: {len(lotes)} · "
          f"Pacientes anonimizados: {len(pacientes)}")
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
        print("  (ninguno; ejecuta --apply)")
    for row in usuarios:
        estado = "activo" if row["activo"] else "inactivo"
        print(f"  {row['username']:<16} {row['rol']:<16} {estado:<9} {row['nombre']}")
    return 0


def check_connection() -> int:
    _print_header("CHECK · Conexión y esquema")
    print(f"MySQL: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"APP_ENV: {settings.APP_ENV}")
    print(f"SECRET_KEY: {'configurada' if settings.SECRET_KEY else 'NO configurada'}")

    row = db.ping()
    print(f"ping: {row}")

    tablas = db.fetch_all(
        """
        SELECT table_name AS nombre
          FROM information_schema.tables
         WHERE table_schema = %s
         ORDER BY table_name
        """,
        (settings.DB_NAME,),
    )
    print(f"Tablas: {len(tablas)}")
    if not any(t["nombre"] == "rol_permisos" for t in tablas):
        print("\nAVISO: falta 'rol_permisos'. Ejecuta la migración 001.")
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seeder seguro de roles, permisos y usuarios de Haydeén Sistema.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--apply", action="store_true", help="Crea/actualiza roles, permisos y usuarios.")
    parser.add_argument(
        "--reset-passwords",
        action="store_true",
        help="Rota la contraseña de usuarios existentes (con --apply).",
    )
    parser.add_argument(
        "--export-seed",
        nargs="?",
        const=str(DEFAULT_EXPORT),
        metavar="RUTA",
        help=f"Exporta seed JSON anonimizado (por defecto: {DEFAULT_EXPORT}).",
    )
    parser.add_argument(
        "--import-seed",
        nargs="?",
        const=str(DEFAULT_EXPORT),
        metavar="RUTA",
        help="Importa un seed JSON generado con --export-seed.",
    )
    parser.add_argument("--list", action="store_true", help="Muestra roles, permisos y usuarios.")
    parser.add_argument("--check", action="store_true", help="Verifica conexión y tablas.")

    for user in USERS:
        parser.add_argument(
            f"--password-{user['arg']}",
            dest=f"password_{user['arg']}",
            metavar="CLAVE",
            help=f"Contraseña inicial de '{user['username']}' (mín. {MIN_PASSWORD_LENGTH} caracteres).",
        )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    actions = [
        args.apply,
        args.export_seed is not None,
        args.import_seed is not None,
        args.list,
        args.check,
    ]
    if not any(actions):
        parser.print_help()
        print("\nIndica al menos una acción: --apply, --export-seed, --import-seed, --list o --check.")
        return 2

    try:
        if args.check:
            return check_connection()
        if args.list:
            return list_state()
        if args.export_seed is not None:
            return export_seed(Path(args.export_seed))
        if args.import_seed is not None:
            return import_seed(Path(args.import_seed))
        if args.apply:
            return apply_seed(args.reset_passwords, args)
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        print(
            "Verifica que MySQL esté activo en Laragon y que api/.env sea correcto.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
