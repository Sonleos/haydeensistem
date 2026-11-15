# Arquitectura y estructura

Documento técnico de referencia para el equipo de desarrollo. Describe la estructura real del repositorio y las decisiones de diseño que la sostienen.

## 1. Vista general

Haydeén Sistema es una aplicación **híbrida de tres capas**:

```text
Clientes                    Servidor                      Datos
────────                    ────────                      ─────
Desktop (CustomTkinter) ─┐
                         ├─► API REST (FastAPI/Uvicorn) ─► MySQL 8
Web móvil (HTML/JS) ─────┘        │
                                  └─► /app sirve la web móvil
```

- **Un solo backend** expone JSON y sirve la app móvil como archivos estáticos.
- **Dos clientes** consumen la misma API y comparten reglas de negocio.
- **Sin ORM**: SQL explícito y parametrizado con PyMySQL.
- **Autorización en el servidor**: los clientes nunca deciden permisos.

## 2. Árbol de directorios

```text
haydeensistem/
│
├── api/                          # Backend FastAPI
│   ├── main.py                   # App, modelos Pydantic, endpoints, montaje de /app
│   ├── db.py                     # Pool de conexiones thread-safe sobre PyMySQL
│   ├── security.py               # PBKDF2, HMAC de tokens, get_current_user, require_permiso
│   ├── config.py                 # Settings desde api/.env (python-dotenv)
│   ├── requirements.txt          # Dependencias del backend
│   ├── .env.example              # Plantilla de variables (sin secretos)
│   ├── .env                      # Configuración local (ignorada por Git)
│   └── .venv/                    # Entorno virtual (ignorado por Git)
│
├── database/
│   ├── schema.sql                # Esquema completo: 15 tablas de dominio + rol_permisos
│   ├── demo_data.sql             # Datos sintéticos idempotentes para demo
│   ├── migrations/
│   │   └── 001_rol_permisos.sql  # Migración incremental idempotente
│   └── seeds/
│       ├── .gitkeep
│       └── initial_data.json     # Exportación local (ignorada por Git)
│
├── desktop/
│   ├── admin_panel.py            # Panel CustomTkinter: login, dashboard y tablas
│   ├── assets/                   # Iconos e imágenes del panel
│   ├── requirements.txt          # customtkinter, requests, pillow
│   └── .venv/                    # Entorno virtual (ignorado por Git)
│
├── web/
│   ├── index.html                # Shell mobile-first (login + app)
│   ├── css/
│   │   └── styles.css            # Ajustes propios sobre Tailwind
│   ├── js/
│   │   ├── api.js                # Cliente HTTP, token y manejo de errores
│   │   └── app.js                # Estado, render, modales y formularios
│   └── assets/                   # Recursos estáticos
│
├── scripts/
│   ├── seed_system.py            # Roles, permisos, usuarios, export/import JSON
│   ├── import_demo.ps1           # Esquema + demo + seeder (UTF-8 seguro)
│   └── start_api.ps1             # Arranque local/LAN leyendo api/.env
│
├── docs/
│   ├── ARQUITECTURA_Y_ESTRUCTURA.md
│   ├── BASE_DE_DATOS_Y_API.md
│   ├── GUIA_COLABORACION.md
│   └── screenshots/              # SVG placeholder + guía de capturas
│
├── packaging/
│   ├── pyinstaller/              # Specs y recursos para el ejecutable
│   └── inno_setup/               # Script .iss del instalador Windows
│
├── .github/
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/
│       ├── config.yml
│       ├── bug_report.yml
│       └── feature_request.yml
│
├── .gitignore                    # Secretos, venv, cachés, logs, dumps, seeds
├── .dockerignore                 # Contexto mínimo si se usa Docker
├── .gitattributes                # EOL y UTF-8 consistentes
├── README.md
├── SECURITY.md
├── SECURITY_CHECKLIST.md
├── CONTRIBUTING.md
├── LICENSE                       # MIT
└── NOTICE                        # Copyright, aviso médico y terceros
```

## 3. Decisiones de diseño

### 3.1 Pool de conexiones ligero sin ORM

**Decisión:** implementar `MySQLPool` en `api/db.py` con `queue.LifoQueue` y `threading.Lock`.

**Motivos:**

- Uvicorn ejecuta endpoints síncronos en un threadpool; el pool debe ser thread-safe.
- Un ORM añade abstracción, dependencias y consultas menos predecibles para reportes con `GROUP BY`, subconsultas y `FOR UPDATE`.
- El SQL explícito permite revisar índices, bloqueos y planes de ejecución.
- El pool es pequeño (5 conexiones por defecto) y suficiente para una LAN clínica.

**Comportamiento:**

- `acquire()` reutiliza conexiones LIFO, hace `ping(reconnect=True)` y descarta conexiones rotas.
- `cursor(commit=True)` confirma; en cualquier otro caso hace `rollback`.
- `release()` siempre limpia la transacción antes de devolver la conexión.
- `close_all()` se ejecuta en el `lifespan` de FastAPI.

**Riesgo asumido:** no hay migraciones automáticas ni capa de repositorio. La disciplina de SQL y migraciones recae en el equipo (ver [`GUIA_COLABORACION.md`](GUIA_COLABORACION.md)).

### 3.2 Seguridad con PBKDF2 y tokens Bearer

**Contraseñas**

```text
pbkdf2_sha256$260000$<salt_base64>$<digest_base64>
```

- Salt aleatorio de 16 bytes por usuario.
- 260 000 iteraciones SHA-256.
- Comparación con `hmac.compare_digest` para evitar timing attacks.

**Tokens**

- `secrets.token_urlsafe(48)` al iniciar sesión.
- En `sesiones` solo se guarda `hash_token(token)`.
- Con `SECRET_KEY` definida, el hash es `HMAC-SHA256(SECRET_KEY, token)`; una fuga de la tabla no permite reutilizar tokens.
- Expiración por `SESSION_HOURS` y limpieza de sesiones vencidas en cada login.
- Cambiar `SECRET_KEY` invalida todas las sesiones (comportamiento intencional).

**Autorización**

- `rol_permisos` relaciona roles con permisos textuales (`modulo:accion`).
- `get_current_user()` resuelve usuario, rol y permisos en una consulta.
- `require_permiso("x")` es una dependencia de FastAPI que devuelve 403 si falta el permiso.
- `admin` recibe `*`; el resto de roles solo sus permisos explícitos.
- Los permisos se evalúan **siempre en el servidor**.

### 3.3 Comunicación REST entre clientes

- Formato JSON, sin GraphQL ni RPC.
- Autenticación stateless desde el punto de vista del cliente: `Authorization: Bearer`.
- La app móvil se sirve desde `/app`, por lo que en producción comparte origen con la API y no necesita CORS.
- El panel de escritorio usa `requests` y `API_BASE_URL` configurable.
- Errores con `detail` legible; los clientes muestran el mensaje sin exponer trazas.

**Consecuencia:** cualquier cliente nuevo (otra app, integración, BI) solo necesita la API y un token.

### 3.4 App móvil sin build step

- HTML + JavaScript ES Modules + Tailwind por CDN.
- Sin bundler: el despliegue es copiar archivos estáticos.
- Ventaja: simplicidad operativa en una LAN clínica.
- Deuda: Tailwind por CDN y ausencia de CSP estricta. El roadmap incluye un build local.

### 3.5 Preparación para PyInstaller e Inno Setup

- `desktop/admin_panel.py` es un único entrypoint con imports explícitos.
- `packaging/pyinstaller/` aloja el `.spec` y recursos.
- `packaging/inno_setup/` aloja el `.iss` del instalador.
- El panel acepta `API_BASE_URL` por entorno, de modo que el instalador puede apuntar al servidor de la residencia.
- Los artefactos (`build/`, `dist/`, `*.spec` fuera de `packaging/`) están ignorados por Git.

## 4. Flujo de autenticación y autorización

```text
Cliente                         API                              MySQL
   │                             │                                 │
   │ POST /api/auth/login        │                                 │
   │ {username, password}        │                                 │
   ├────────────────────────────►│ SELECT usuario + rol            │
   │                             ├────────────────────────────────►│
   │                             │ verify_password (PBKDF2)        │
   │                             │ token = secrets.token_urlsafe() │
   │                             │ INSERT sesiones(token_hash)     │
   │                             ├────────────────────────────────►│
   │ 200 {token, usuario}        │                                 │
   │◄────────────────────────────┤                                 │
   │                             │                                 │
   │ GET /api/pacientes          │                                 │
   │ Authorization: Bearer ...   │                                 │
   ├────────────────────────────►│ get_current_user()              │
   │                             │ require_permiso("pacientes:leer")│
   │                             │ SELECT ... WHERE token_hash=%s  │
   │                             ├────────────────────────────────►│
   │ 200 [ ... ]                 │                                 │
   │◄────────────────────────────┤                                 │
```

## 5. Configuración y entornos

| Entorno | `APP_ENV` | `CORS_ORIGINS` | `SECRET_KEY` | MySQL |
| --- | --- | --- | --- | --- |
| Local | `development` | `*` | Recomendada | `root` local |
| LAN de pruebas | `development` | IP/host del servidor | Obligatoria en la práctica | usuario dedicado |
| Producción | `production` | Dominio HTTPS exacto | Obligatoria (falla al arrancar si falta) | usuario con permisos mínimos |

`config.py` lanza `RuntimeError` si `APP_ENV=production` y `SECRET_KEY` está vacía. Es una barrera deliberada para evitar despliegues inseguros por omisión.

## 6. Topología de despliegue recomendada

```text
                 LAN clínica / VPN
┌────────────┐   ┌────────────┐   ┌────────────┐
│ PC admin   │   │ Móvil 1    │   │ Móvil N    │
└─────┬──────┘   └─────┬──────┘   └─────┬──────┘
      └────────────────┼────────────────┘
                       ▼
            ┌──────────────────────┐
            │ Reverse proxy HTTPS  │  (Caddy/Nginx, opcional en LAN)
            └──────────┬───────────┘
                       ▼
            ┌──────────────────────┐
            │ Servidor Windows     │
            │ Uvicorn :8000        │
            │ MySQL 8 :3306        │
            └──────────────────────┘
```

- Firewall restringido a la subred clínica.
- Sin exposición directa a Internet.
- Respaldos cifrados fuera del servidor.
- Reloj sincronizado (NTP): la expiración de sesiones y los registros clínicos dependen de la hora.

## 7. Deuda técnica y evolución

| Área | Estado | Próximo paso |
| --- | --- | --- |
| Autorización | Implementada por permiso | Añadir permisos de escritura de pacientes/personal |
| Sesiones | Expiración y limpieza | Endpoint de logout con borrado en servidor |
| Login | Sin límite de intentos | Rate limiting por IP + backoff |
| Transporte | HTTP en LAN | HTTPS con reverse proxy |
| Auditoría | Movimientos de inventario | Tabla `auditoria` genérica |
| Pruebas | Manuales | pytest + Playwright + CI |
| Frontend | Tailwind CDN | Build local + CSP |
| Observabilidad | Logs de aplicación | Métricas y alertas |

Cualquier cambio estructural debe reflejarse en este documento y en [`BASE_DE_DATOS_Y_API.md`](BASE_DE_DATOS_Y_API.md).
