from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import settings
from db import db
from security import (
    create_session_token,
    get_current_user,
    hash_token,
    require_permiso,
    verify_password,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("haydeensistem.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.SECRET_KEY:
        logger.warning(
            "SECRET_KEY no configurada: los tokens se guardan con SHA-256 simple. "
            "Define SECRET_KEY en api/.env para usar HMAC-SHA256."
        )
    try:
        db.ping()
        logger.info(
            "MySQL conectado en %s:%s/%s",
            settings.DB_HOST,
            settings.DB_PORT,
            settings.DB_NAME,
        )
    except Exception as exc:
        logger.warning("MySQL no disponible al iniciar: %s", exc)

    yield

    db.close_all()
    logger.info("Pool de conexiones MySQL cerrado")


app = FastAPI(
    title=settings.APP_NAME,
    description="API REST para la gestión clínica y administrativa del geriátrico.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class LoginUser(BaseModel):
    id: int
    username: str
    rol: str
    nombre_completo: str


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: LoginUser


class SignosVitalesCreate(BaseModel):
    paciente_id: int = Field(gt=0)
    presion_sistolica: int | None = Field(default=None, ge=40, le=300)
    presion_diastolica: int | None = Field(default=None, ge=20, le=200)
    bpm: int | None = Field(default=None, ge=20, le=300)
    saturacion_o2: int | None = Field(default=None, ge=0, le=100)
    frecuencia_respiratoria: int | None = Field(default=None, ge=4, le=80)
    temperatura: float | None = Field(default=None, ge=30, le=45)
    observaciones: str | None = Field(default=None, max_length=255)


class AdministracionCreate(BaseModel):
    tratamiento_id: int = Field(gt=0)
    horario_id: int | None = Field(default=None, gt=0)
    lote_id: int | None = Field(default=None, gt=0)
    dosis_aplicada: float = Field(ge=0)
    via_administracion: str | None = None
    estado: Literal["administrado", "omitido", "retrasado"] = "administrado"
    observaciones: str | None = Field(default=None, max_length=255)


VIAS_ADMINISTRACION = {
    "oral",
    "venosa",
    "intramuscular",
    "subcutanea",
    "topica",
    "rectal",
    "inhalatoria",
    "sublingual",
    "otra",
}


ESTADISTICAS_SQL = """
SELECT
  (SELECT COUNT(*) FROM pacientes WHERE estado = 'activo') AS pacientes_activos,
  (SELECT COUNT(*) FROM personal WHERE estado IN ('activo', 'libre')) AS personal_activo,
  (SELECT COUNT(*) FROM turnos
     WHERE fecha = CURDATE() AND estado IN ('programado', 'en_curso')) AS turnos_hoy,
  (SELECT COUNT(*) FROM tratamientos WHERE estado = 'activo') AS tratamientos_activos,
  (SELECT COUNT(*) FROM signos_vitales
     WHERE DATE(fecha_hora) = CURDATE()) AS signos_hoy,
  (SELECT COUNT(*) FROM dxtx
     WHERE DATE(fecha_hora) = CURDATE()) AS dxtx_hoy,
  (SELECT COUNT(*) FROM control_panales
     WHERE DATE(fecha_hora) = CURDATE()) AS panales_hoy,
  (SELECT COUNT(*) FROM (
      SELECT m.id
      FROM medicamentos m
      LEFT JOIN inventario_lotes l ON l.medicamento_id = m.id
      WHERE m.activo = 1
      GROUP BY m.id, m.stock_minimo
      HAVING COALESCE(SUM(l.cantidad_disponible), 0) < m.stock_minimo
  ) AS medicamentos_bajos) AS stock_bajo
"""


@app.get("/", tags=["Sistema"])
def root() -> dict:
    return {
        "servicio": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentacion": "/docs",
        "estado": "operativo",
    }


@app.get("/api/ping", tags=["Sistema"])
def ping() -> dict:
    return {
        "status": "ok",
        "servicio": settings.APP_NAME,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


@app.get("/api/health", tags=["Sistema"])
def health() -> dict:
    try:
        row = db.fetch_one(
            "SELECT DATABASE() AS base_datos, VERSION() AS version_mysql, NOW() AS ahora"
        )
    except Exception as exc:
        logger.exception("Health check de MySQL falló")
        raise HTTPException(
            status_code=503,
            detail="Base de datos no disponible",
        ) from exc

    return {
        "status": "ok",
        "base_datos": row["base_datos"],
        "mysql": row["version_mysql"],
        "servidor": row["ahora"].isoformat(sep=" ", timespec="seconds"),
        "pool": db.status,
    }


@app.post("/api/auth/login", response_model=LoginResponse, tags=["Autenticación"])
def login(payload: LoginRequest, request: Request) -> LoginResponse:
    username = payload.username.strip().lower()

    user = db.fetch_one(
        """
        SELECT u.id,
               u.username,
               u.password_hash,
               u.activo,
               r.nombre AS rol,
               COALESCE(NULLIF(CONCAT_WS(' ', p.nombre, p.apellidos), ''), u.username)
                   AS nombre_completo
        FROM usuarios u
        JOIN roles r ON r.id = u.rol_id
        LEFT JOIN personal p ON p.id = u.personal_id
        WHERE u.username = %s
        LIMIT 1
        """,
        (username,),
    )

    if (
        not user
        or not user["activo"]
        or not verify_password(payload.password, user["password_hash"])
    ):
        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos",
        )

    token = create_session_token()
    expires_at = datetime.now() + timedelta(hours=settings.SESSION_HOURS)
    client_ip = request.client.host if request.client else None
    user_agent = (request.headers.get("user-agent") or "")[:255] or None

    db.execute("DELETE FROM sesiones WHERE expira_en < NOW()")
    db.execute(
        """
        INSERT INTO sesiones (usuario_id, token_hash, expira_en, ip, user_agent)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user["id"], hash_token(token), expires_at, client_ip, user_agent),
    )
    db.execute(
        "UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s",
        (user["id"],),
    )

    logger.info("Inicio de sesión: %s (%s)", user["username"], client_ip)

    return LoginResponse(
        token=token,
        expires_in=settings.SESSION_HOURS * 3600,
        usuario=LoginUser(
            id=user["id"],
            username=user["username"],
            rol=user["rol"],
            nombre_completo=user["nombre_completo"],
        ),
    )


@app.get("/api/auth/me", tags=["Autenticación"])
def me(user: dict = Depends(get_current_user)) -> dict:
    return user


@app.get("/api/dashboard/stats", tags=["Dashboard"])
def dashboard_stats(_: dict = Depends(require_permiso("dashboard:leer"))) -> dict:
    try:
        stats = db.fetch_one(ESTADISTICAS_SQL)
    except Exception as exc:
        logger.exception("Error obteniendo estadísticas del dashboard")
        raise HTTPException(
            status_code=500,
            detail="No se pudieron obtener las estadísticas",
        ) from exc

    stats["generado_en"] = datetime.now().isoformat(timespec="seconds")
    return stats


@app.get("/api/pacientes", tags=["Pacientes"])
def listar_pacientes(_: dict = Depends(require_permiso("pacientes:leer"))) -> list[dict]:
    return db.fetch_all(
        """
        SELECT p.id,
               p.nombre,
               p.apellidos,
               p.documento,
               p.fecha_nacimiento,
               TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, CURDATE()) AS edad,
               p.sexo,
               p.tipo_residencia,
               p.habitacion,
               p.cama,
               p.contacto_familiar,
               p.telefono_contacto,
               p.alergias,
               p.diagnostico,
               p.peso_kg,
               p.talla_m,
               p.imc,
               p.estado,
               p.fecha_ingreso,
               (SELECT COUNT(*)
                  FROM tratamientos t
                 WHERE t.paciente_id = p.id AND t.estado = 'activo') AS tratamientos_activos
          FROM pacientes p
         ORDER BY p.apellidos, p.nombre
        """
    )


@app.get("/api/personal", tags=["Personal"])
def listar_personal(_: dict = Depends(require_permiso("personal:leer"))) -> list[dict]:
    return db.fetch_all(
        """
        SELECT p.id,
               p.nombre,
               p.apellidos,
               p.documento,
               p.telefono,
               p.email,
               r.nombre AS rol,
               p.estado,
               p.fecha_ingreso,
               (SELECT CONCAT(DATE_FORMAT(t.hora_inicio, '%H:%i'), ' - ',
                              DATE_FORMAT(t.hora_fin, '%H:%i'), ' (', t.tipo, ')')
                  FROM turnos t
                 WHERE t.personal_id = p.id AND t.fecha = CURDATE()
                 ORDER BY t.hora_inicio
                 LIMIT 1) AS turno_hoy,
               (SELECT t.estado
                  FROM turnos t
                 WHERE t.personal_id = p.id AND t.fecha = CURDATE()
                 ORDER BY t.hora_inicio
                 LIMIT 1) AS estado_turno
          FROM personal p
          JOIN roles r ON r.id = p.rol_id
         ORDER BY p.apellidos, p.nombre
        """
    )


@app.get("/api/inventario", tags=["Inventario"])
def listar_inventario(_: dict = Depends(require_permiso("inventario:leer"))) -> list[dict]:
    return db.fetch_all(
        """
        SELECT m.id,
               m.nombre,
               m.principio_activo,
               m.presentacion,
               m.concentracion,
               m.unidad,
               m.stock_minimo,
               m.requiere_refrigeracion,
               m.activo,
               COALESCE(SUM(l.cantidad_disponible), 0) AS disponible,
               COUNT(l.id) AS lotes,
               MIN(l.fecha_caducidad) AS proxima_caducidad,
               CASE
                 WHEN COALESCE(SUM(l.cantidad_disponible), 0) < m.stock_minimo THEN 1
                 ELSE 0
               END AS stock_bajo
          FROM medicamentos m
          LEFT JOIN inventario_lotes l ON l.medicamento_id = m.id
         GROUP BY m.id, m.nombre, m.principio_activo, m.presentacion,
                  m.concentracion, m.unidad, m.stock_minimo,
                  m.requiere_refrigeracion, m.activo
         ORDER BY stock_bajo DESC, m.nombre
        """
    )


@app.get("/api/inventario/lotes", tags=["Inventario"])
def listar_lotes(
    medicamento_id: int | None = None,
    solo_disponibles: bool = True,
    _: dict = Depends(require_permiso("inventario:leer")),
) -> list[dict]:
    return db.fetch_all(
        """
        SELECT l.id,
               l.medicamento_id,
               m.nombre AS medicamento,
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
         WHERE (%s IS NULL OR l.medicamento_id = %s)
           AND (%s = 0 OR l.cantidad_disponible > 0)
         ORDER BY l.fecha_caducidad, l.codigo_lote
        """,
        (
            medicamento_id,
            medicamento_id,
            1 if solo_disponibles else 0,
        ),
    )


@app.get("/api/tratamientos", tags=["Tratamientos"])
def listar_tratamientos(_: dict = Depends(require_permiso("tratamientos:leer"))) -> list[dict]:
    return db.fetch_all(
        """
        SELECT t.id,
               t.paciente_id,
               CONCAT_WS(' ', p.nombre, p.apellidos) AS paciente,
               p.tipo_residencia,
               p.habitacion,
               t.medicamento_id,
               m.nombre AS medicamento,
               m.concentracion,
               t.dosis,
               t.unidad_dosis,
               t.via_administracion,
               t.frecuencia_horas,
               DATE_FORMAT(t.fecha_inicio, '%Y-%m-%d %H:%i') AS fecha_inicio,
               DATE_FORMAT(t.fecha_fin, '%Y-%m-%d %H:%i') AS fecha_fin,
               t.prescrito_por,
               t.indicaciones,
               t.estado,
               (SELECT GROUP_CONCAT(DATE_FORMAT(h.hora, '%H:%i')
                                    ORDER BY h.hora SEPARATOR ', ')
                  FROM tratamiento_horarios h
                 WHERE h.tratamiento_id = t.id) AS horarios
          FROM tratamientos t
          JOIN pacientes p ON p.id = t.paciente_id
          JOIN medicamentos m ON m.id = t.medicamento_id
         ORDER BY FIELD(t.estado, 'activo', 'suspendido', 'finalizado'),
                  p.apellidos, m.nombre
        """
    )


@app.get("/api/control-diario", tags=["Control diario"])
def control_diario(
    fecha: str | None = None,
    _: dict = Depends(require_permiso("control:leer")),
) -> dict:
    if fecha:
        try:
            dia = date.fromisoformat(fecha)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Fecha inválida. Usa el formato YYYY-MM-DD",
            ) from exc
    else:
        dia = date.today()

    signos = db.fetch_all(
        """
        SELECT s.id,
               DATE_FORMAT(s.fecha_hora, '%%Y-%%m-%%d %%H:%%i') AS fecha_hora,
               CONCAT_WS(' ', p.nombre, p.apellidos) AS paciente,
               p.habitacion,
               CONCAT_WS(' ', per.nombre, per.apellidos) AS personal,
               s.presion_sistolica,
               s.presion_diastolica,
               s.bpm,
               s.saturacion_o2,
               s.frecuencia_respiratoria,
               s.temperatura,
               s.observaciones
          FROM signos_vitales s
          JOIN pacientes p ON p.id = s.paciente_id
          LEFT JOIN personal per ON per.id = s.personal_id
         WHERE DATE(s.fecha_hora) = %s
         ORDER BY s.fecha_hora DESC
        """,
        (dia,),
    )

    dxtx = db.fetch_all(
        """
        SELECT d.id,
               DATE_FORMAT(d.fecha_hora, '%%Y-%%m-%%d %%H:%%i') AS fecha_hora,
               CONCAT_WS(' ', p.nombre, p.apellidos) AS paciente,
               CONCAT_WS(' ', per.nombre, per.apellidos) AS personal,
               d.valor_mg_dl,
               d.tipo,
               d.insulina_aplicada,
               d.observaciones
          FROM dxtx d
          JOIN pacientes p ON p.id = d.paciente_id
          LEFT JOIN personal per ON per.id = d.personal_id
         WHERE DATE(d.fecha_hora) = %s
         ORDER BY d.fecha_hora DESC
        """,
        (dia,),
    )

    panales = db.fetch_all(
        """
        SELECT c.id,
               DATE_FORMAT(c.fecha_hora, '%%Y-%%m-%%d %%H:%%i') AS fecha_hora,
               CONCAT_WS(' ', p.nombre, p.apellidos) AS paciente,
               CONCAT_WS(' ', per.nombre, per.apellidos) AS personal,
               c.tipo,
               c.observaciones
          FROM control_panales c
          JOIN pacientes p ON p.id = c.paciente_id
          LEFT JOIN personal per ON per.id = c.personal_id
         WHERE DATE(c.fecha_hora) = %s
         ORDER BY c.fecha_hora DESC
        """,
        (dia,),
    )

    return {
        "fecha": dia.isoformat(),
        "signos": signos,
        "dxtx": dxtx,
        "panales": panales,
    }


@app.post("/api/signos-vitales", tags=["Control diario"])
def crear_signos_vitales(
    payload: SignosVitalesCreate,
    user: dict = Depends(require_permiso("control:escribir")),
) -> dict:
    paciente = db.fetch_one(
        "SELECT id FROM pacientes WHERE id = %s AND estado = 'activo'",
        (payload.paciente_id,),
    )
    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente no encontrado o inactivo",
        )

    if (payload.presion_sistolica is None) != (payload.presion_diastolica is None):
        raise HTTPException(
            status_code=400,
            detail="Registra presión sistólica y diastólica juntas",
        )

    medidas = (
        payload.presion_sistolica,
        payload.bpm,
        payload.saturacion_o2,
        payload.frecuencia_respiratoria,
        payload.temperatura,
    )
    if all(valor is None for valor in medidas):
        raise HTTPException(
            status_code=400,
            detail="Registra al menos un signo vital",
        )

    with db.cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO signos_vitales
              (paciente_id, personal_id, presion_sistolica, presion_diastolica,
               bpm, saturacion_o2, frecuencia_respiratoria, temperatura,
               observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payload.paciente_id,
                user.get("personal_id"),
                payload.presion_sistolica,
                payload.presion_diastolica,
                payload.bpm,
                payload.saturacion_o2,
                payload.frecuencia_respiratoria,
                payload.temperatura,
                payload.observaciones,
            ),
        )
        nuevo_id = cursor.lastrowid

    return {
        "id": nuevo_id,
        "mensaje": "Signos vitales registrados correctamente",
    }


@app.post("/api/administraciones", tags=["Tratamientos"])
def registrar_administracion(
    payload: AdministracionCreate,
    user: dict = Depends(require_permiso("administracion:escribir")),
) -> dict:
    tratamiento = db.fetch_one(
        """
        SELECT id, medicamento_id, via_administracion, estado
          FROM tratamientos
         WHERE id = %s
        """,
        (payload.tratamiento_id,),
    )
    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")

    if tratamiento["estado"] != "activo":
        raise HTTPException(
            status_code=409,
            detail="Solo se pueden administrar tratamientos activos",
        )

    if payload.estado != "omitido" and payload.dosis_aplicada <= 0:
        raise HTTPException(
            status_code=400,
            detail="La dosis aplicada debe ser mayor que cero",
        )

    via = payload.via_administracion or tratamiento["via_administracion"]
    if via not in VIAS_ADMINISTRACION:
        raise HTTPException(status_code=400, detail="Vía de administración inválida")

    if payload.horario_id is not None:
        horario = db.fetch_one(
            """
            SELECT id FROM tratamiento_horarios
             WHERE id = %s AND tratamiento_id = %s
            """,
            (payload.horario_id, payload.tratamiento_id),
        )
        if not horario:
            raise HTTPException(
                status_code=400,
                detail="El horario no pertenece al tratamiento",
            )

    lote_id = None if payload.estado == "omitido" else payload.lote_id
    dosis = 0.0 if payload.estado == "omitido" else payload.dosis_aplicada
    personal_id = user.get("personal_id")

    with db.cursor(commit=True) as cursor:
        if lote_id is not None:
            cursor.execute(
                """
                SELECT id, cantidad_disponible
                  FROM inventario_lotes
                 WHERE id = %s AND medicamento_id = %s
                 FOR UPDATE
                """,
                (lote_id, tratamiento["medicamento_id"]),
            )
            lote = cursor.fetchone()
            if not lote:
                raise HTTPException(
                    status_code=400,
                    detail="El lote no corresponde al medicamento del tratamiento",
                )
            if lote["cantidad_disponible"] < 1:
                raise HTTPException(
                    status_code=409,
                    detail="El lote no tiene stock disponible",
                )

        cursor.execute(
            """
            INSERT INTO administraciones_medicamento
              (tratamiento_id, horario_id, lote_id, personal_id, dosis_aplicada,
               via_administracion, estado, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payload.tratamiento_id,
                payload.horario_id,
                lote_id,
                personal_id,
                dosis,
                via,
                payload.estado,
                payload.observaciones,
            ),
        )
        administracion_id = cursor.lastrowid

        # Se descuenta una unidad de presentación por administración.
        # El módulo de farmacia puede ajustar la conversión de dosis a unidades.
        if lote_id is not None:
            cursor.execute(
                """
                UPDATE inventario_lotes
                   SET cantidad_disponible = cantidad_disponible - 1
                 WHERE id = %s
                """,
                (lote_id,),
            )
            cursor.execute(
                """
                INSERT INTO movimientos_inventario
                  (lote_id, tipo, cantidad, motivo, personal_id)
                VALUES (%s, 'salida', 1, %s, %s)
                """,
                (
                    lote_id,
                    f"Administración del tratamiento #{payload.tratamiento_id}",
                    personal_id,
                ),
            )

    return {
        "id": administracion_id,
        "mensaje": "Administración registrada correctamente",
    }


WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
