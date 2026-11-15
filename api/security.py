from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException

from config import settings
from db import db

PBKDF2_ITERATIONS = 260_000


def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_text)
        salt = base64.b64decode(salt_text)
        expected = base64.b64decode(digest_text)
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(candidate, expected)
    except (ValueError, TypeError, binascii.Error):
        return False


def create_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Hash del token que se guarda en la base de datos.

    Si SECRET_KEY está definida se usa HMAC-SHA256, de modo que una copia de
    la tabla `sesiones` no baste para reutilizar los tokens. Sin SECRET_KEY se
    mantiene SHA-256 puro por compatibilidad con instalaciones de desarrollo.
    """
    if settings.SECRET_KEY:
        return hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _permisos_de(rol_id: int) -> list[str]:
    filas = db.fetch_all(
        "SELECT permiso FROM rol_permisos WHERE rol_id = %s ORDER BY permiso",
        (rol_id,),
    )
    return [fila["permiso"] for fila in filas]


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Formato de autorización inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.fetch_one(
        """
        SELECT u.id,
               u.username,
               u.personal_id,
               u.rol_id,
               r.nombre AS rol,
               COALESCE(NULLIF(CONCAT_WS(' ', p.nombre, p.apellidos), ''), u.username)
                   AS nombre_completo
        FROM sesiones s
        JOIN usuarios u ON u.id = s.usuario_id
        JOIN roles r ON r.id = u.rol_id
        LEFT JOIN personal p ON p.id = u.personal_id
        WHERE s.token_hash = %s
          AND s.expira_en > NOW()
          AND u.activo = 1
        LIMIT 1
        """,
        (hash_token(token),),
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida o expirada",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user["permisos"] = _permisos_de(user["rol_id"])
    return user


def require_permiso(*permisos: str):
    """Dependencia de autorización por permiso.

    `admin` recibe el comodín `*`. El resto de roles solo accede a los
    permisos otorgados en `rol_permisos`.
    """

    def dependency(user: dict = Depends(get_current_user)) -> dict:
        otorgados = set(user.get("permisos") or [])
        if "*" in otorgados or otorgados.intersection(permisos):
            return user
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para realizar esta operación",
        )

    return dependency
