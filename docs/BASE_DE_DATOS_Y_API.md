# Base de datos y API

Referencia del modelo relacional y de la superficie HTTP del sistema.

## 1. Modelo de datos

- Motor: **MySQL 8.0+** (probado en 8.4.3).
- Codificación: `utf8mb4` / `utf8mb4_unicode_ci`.
- **15 tablas de dominio** + `rol_permisos` para autorización.
- Claves foráneas explícitas, índices en columnas de búsqueda y `CHECK` para rangos clínicos.
- Sin ORM: las consultas viven en `api/main.py` y `api/security.py`.

### 1.1 Tablas

| # | Tabla | Propósito | Claves y relaciones |
| --- | --- | --- | --- |
| 1 | `roles` | Catálogo de roles | `nombre` único |
| 2 | `rol_permisos` | Permisos por rol (`modulo:accion`) | FK `rol_id` → `roles`, PK compuesta |
| 3 | `personal` | Personal de la residencia | FK `rol_id` → `roles`, `documento` único |
| 4 | `turnos` | Turnos por persona y fecha | FK `personal_id` → `personal` |
| 5 | `usuarios` | Credenciales de acceso | FK `personal_id` → `personal`, FK `rol_id` → `roles`, `username` único |
| 6 | `sesiones` | Tokens Bearer activos | FK `usuario_id` → `usuarios`, `token_hash` único |
| 7 | `pacientes` | Expediente del residente | `documento` único, IMC generado |
| 8 | `medicamentos` | Catálogo farmacológico | — |
| 9 | `inventario_lotes` | Lotes y stock | FK `medicamento_id` → `medicamentos`, único (`medicamento_id`, `codigo_lote`) |
| 10 | `tratamientos` | Prescripción activa | FK `paciente_id`, FK `medicamento_id` |
| 11 | `tratamiento_horarios` | Horas de cada tratamiento | FK `tratamiento_id`, único (`tratamiento_id`, `hora`) |
| 12 | `administraciones_medicamento` | Registro de dosis administradas | FK `tratamiento_id`, `horario_id`, `lote_id`, `personal_id` |
| 13 | `movimientos_inventario` | Entradas, salidas y ajustes | FK `lote_id`, `personal_id` |
| 14 | `signos_vitales` | TA, FC, SpO₂, FR y temperatura | FK `paciente_id`, `personal_id` |
| 15 | `dxtx` | Glucosa e insulina | FK `paciente_id`, `personal_id` |
| 16 | `control_panales` | Registro de pañales | FK `paciente_id`, `personal_id` |

### 1.2 Relaciones principales

```text
roles 1──N personal 1──N turnos
  │            │
  │            └──1 usuarios 1──N sesiones
  │
  └──1 rol_permisos

pacientes 1──N tratamientos N──1 medicamentos
     │             │
     │             ├──N tratamiento_horarios
     │             └──N administraciones_medicamento
     │                          │
     │                          ├──1 inventario_lotes N──1 medicamentos
     │                          └──1 personal
     │
     ├──N signos_vitales
     ├──N dxtx
     └──N control_panales

inventario_lotes 1──N movimientos_inventario
```

Reglas de borrado:

- `ON DELETE RESTRICT` en tratamientos, medicamentos y movimientos: no se borra historial clínico ni farmacológico.
- `ON DELETE CASCADE` en horarios y sesiones: dependientes sin valor histórico propio.
- `ON DELETE SET NULL` en referencias opcionales a personal (el registro clínico sobrevive a la baja del empleado).

## 2. Reglas de negocio

### 2.1 IMC calculado

`pacientes.imc` es una columna **generada y almacenada**:

```sql
CASE
  WHEN peso_kg IS NOT NULL AND talla_m IS NOT NULL AND talla_m > 0
    THEN ROUND(peso_kg / (talla_m * talla_m), 2)
  ELSE NULL
END
```

- No se escribe desde la API; MySQL la recalcula al cambiar peso o talla.
- `CHECK (talla_m > 0)` evita división por cero.
- La API devuelve `imc` ya calculado en `GET /api/pacientes`.

### 2.2 Stock y alertas de inventario

- Disponible por medicamento: `SUM(inventario_lotes.cantidad_disponible)`.
- `stock_bajo = 1` cuando el disponible es menor que `medicamentos.stock_minimo`.
- El dashboard cuenta medicamentos en esa condición.
- Los lotes se ordenan por `fecha_caducidad` para priorizar FEFO (first expired, first out).

### 2.3 Administración de medicamentos

`POST /api/administraciones` aplica estas reglas dentro de una transacción:

1. El tratamiento debe existir y estar `activo`.
2. Si `estado != "omitido"`, `dosis_aplicada` debe ser mayor que cero.
3. La vía debe pertenecer al catálogo permitido.
4. Si se envía `horario_id`, debe pertenecer al tratamiento.
5. Si se envía `lote_id`, debe corresponder al medicamento del tratamiento.
6. El lote se lee con `SELECT ... FOR UPDATE` para evitar carreras.
7. Se exige `cantidad_disponible >= 1`.
8. Se inserta la administración.
9. Se descuenta **una unidad de presentación** del lote.
10. Se registra un movimiento `salida` con el motivo.

> El descuento es por presentación, no por miligramos. La conversión fina de dosis a unidades queda para el módulo de farmacia.

### 2.4 Sesiones

- El token se genera con 48 bytes aleatorios (`token_urlsafe`).
- En `sesiones` solo se almacena su hash (HMAC-SHA256 si hay `SECRET_KEY`).
- `expira_en` se calcula con `SESSION_HOURS`.
- En cada login se eliminan sesiones vencidas.
- `GET /api/auth/me` resuelve usuario, rol y permisos.

### 2.5 Validaciones clínicas

| Campo | Rango |
| --- | --- |
| Presión sistólica | 40–300 mmHg |
| Presión diastólica | 20–200 mmHg |
| Frecuencia cardiaca | 20–300 lpm |
| Saturación O₂ | 0–100 % |
| Frecuencia respiratoria | 4–80 rpm |
| Temperatura | 30.0–45.0 °C |
| Dosis de tratamiento | > 0 |
| Cantidad de movimiento | > 0 |

Se validan en Pydantic **y** con `CHECK` en MySQL: dos barreras independientes.

### 2.6 Datos demo

- `database/demo_data.sql` es idempotente (`INSERT IGNORE` / `WHERE NOT EXISTS`).
- Usa documentos `PAC-*`, `MED-*`, `ENF-*`, `FAR-*`, `REC-*` y teléfonos `555-*`.
- No contiene usuarios ni contraseñas: los crea `scripts/init_db.py`.
- `init_db.py --export-seed` solo exporta pacientes con documento `PAC-*` o `DEMO-*` y anonimiza nombre y contacto.

## 3. API REST

Base local: `http://127.0.0.1:8000/api`
Documentación interactiva: `http://127.0.0.1:8000/docs`

### 3.1 Autenticación

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| `POST` | `/auth/login` | público | Devuelve `token`, `expires_in` y datos del usuario |
| `GET` | `/auth/me` | autenticado | Usuario, rol y lista de permisos |

```cmd
curl -X POST http://127.0.0.1:8000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"<TU_CLAVE>\"}"
```

Copia el `token` y úsalo así:

```cmd
curl http://127.0.0.1:8000/api/auth/me ^
  -H "Authorization: Bearer <TU_TOKEN>"
```

### 3.2 Sistema y dashboard

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| `GET` | `/ping` | público | Estado simple del servicio |
| `GET` | `/health` | público | MySQL, versión y estado del pool |
| `GET` | `/dashboard/stats` | `dashboard:leer` | Totales operativos del día |

`/dashboard/stats` devuelve: pacientes activos, personal activo, turnos de hoy, tratamientos activos, signos, DXTX, pañales y stock bajo.

### 3.3 Pacientes

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| `GET` | `/pacientes` | `pacientes:leer` | Expedientes con edad, IMC y tratamientos activos |

Incluye datos de contacto y alergias. **Es información clínica sensible**: no debe registrarse en logs ni capturas.

### 3.4 Personal

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| `GET` | `/personal` | `personal:leer` | Personal con rol y turno de hoy |

### 3.5 Inventario

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| `GET` | `/inventario` | `inventario:leer` | Medicamentos con disponible, lotes y alerta |
| `GET` | `/inventario/lotes` | `inventario:leer` | Lotes; filtros `medicamento_id` y `solo_disponibles` |

```cmd
curl "http://127.0.0.1:8000/api/inventario/lotes?medicamento_id=1&solo_disponibles=true" ^
  -H "Authorization: Bearer <TU_TOKEN>"
```

### 3.6 Tratamientos

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| `GET` | `/tratamientos` | `tratamientos:leer` | Tratamientos con paciente, medicamento y horarios |
| `POST` | `/administraciones` | `administracion:escribir` | Registra dosis y descuenta stock |

```json
{
  "tratamiento_id": 1,
  "horario_id": 1,
  "lote_id": 1,
  "dosis_aplicada": 1,
  "via_administracion": "oral",
  "estado": "administrado",
  "observaciones": "Sin incidencias"
}
```

### 3.7 Control diario

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| `GET` | `/control-diario` | `control:leer` | Signos, DXTX y pañales del día (`?fecha=YYYY-MM-DD`) |
| `POST` | `/signos-vitales` | `control:escribir` | Registra signos vitales |

```json
{
  "paciente_id": 1,
  "presion_sistolica": 120,
  "presion_diastolica": 80,
  "bpm": 78,
  "saturacion_o2": 96,
  "frecuencia_respiratoria": 18,
  "temperatura": 36.5,
  "observaciones": "Paciente estable"
}
```

### 3.8 Códigos de error

| Código | Significado |
| --- | --- |
| `400` | Datos inválidos, lote/horario incoherente o falta de medidas |
| `401` | Token ausente, inválido o expirado |
| `403` | El rol no tiene el permiso requerido |
| `404` | Paciente, tratamiento o recurso inexistente |
| `409` | Conflicto: tratamiento inactivo o lote sin stock |
| `422` | Error de validación de Pydantic |
| `500` | Error interno (se registra en logs, no se expone la traza) |
| `503` | MySQL no disponible |

## 4. Inicialización y migraciones

**Regla del equipo:** `schema.sql` no se sobrescribe para cambios incrementales.

1. `schema.sql` describe el estado base para instalaciones nuevas.
2. Cada cambio va en `database/migrations/NNN_descripcion.sql`, idempotente.
3. `scripts/init_db.py` aplica automáticamente todas las migraciones en orden.
4. La migración se prueba sobre una copia de la base.
5. Se actualiza `schema.sql` (para nuevos entornos) y la documentación.
6. Se registra en el PR con el SQL exacto y el plan de reversa.

### Inicializar o actualizar

```cmd
api\.venv\Scripts\python.exe scripts\init_db.py
```

- Si la base no existe, crea todo.
- Si ya existe, **no ejecuta `schema.sql`**: solo aplica migraciones y demo.
- `init_db.py` adapta el `USE` de los archivos SQL a `DB_NAME`, así que puedes cambiar de base sin editar los `.sql`.
- `--reset` recrea el esquema desde cero (**destructivo**).
- `--no-demo` omite los datos sintéticos.
- `--check` verifica conexión, base y tablas.
- `--list` muestra roles, permisos y usuarios.

### Migración existente

| Archivo | Contenido |
| --- | --- |
| `001_rol_permisos.sql` | Crea `rol_permisos`, agrega rol `administrativo` y su matriz de permisos |

Para añadir una migración:

1. Crea `database/migrations/002_descripcion.sql`.
2. Hazla idempotente (`CREATE TABLE IF NOT EXISTS`, `INSERT IGNORE`, etc.).
3. Ejecuta `api\.venv\Scripts\python.exe scripts\init_db.py`.
4. Verifica con `--check` y `--list`.
5. Actualiza este documento y `schema.sql`.

No uses `mysql.exe`, rutas de Laragon ni scripts PowerShell. `init_db.py` ya ejecuta el SQL con PyMySQL y UTF-8.

## 5. Consultas de diagnóstico

```sql
-- Usuarios, rol y último acceso
SELECT u.username, r.nombre AS rol, u.activo, u.ultimo_acceso
  FROM usuarios u JOIN roles r ON r.id = u.rol_id
 ORDER BY u.username;

-- Permisos efectivos
SELECT r.nombre AS rol, rp.permiso
  FROM rol_permisos rp JOIN roles r ON r.id = rp.rol_id
 ORDER BY r.nombre, rp.permiso;

-- Stock por medicamento
SELECT m.nombre, COALESCE(SUM(l.cantidad_disponible), 0) AS disponible,
       m.stock_minimo
  FROM medicamentos m
  LEFT JOIN inventario_lotes l ON l.medicamento_id = m.id
 GROUP BY m.id, m.nombre, m.stock_minimo
 ORDER BY m.nombre;

-- Sesiones activas
SELECT COUNT(*) AS activas FROM sesiones WHERE expira_en > NOW();
```

También puedes usar:

```cmd
api\.venv\Scripts\python.exe scripts\init_db.py --list
api\.venv\Scripts\python.exe scripts\test_sistema.py
```
