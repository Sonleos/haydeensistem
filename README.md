<div align="center">

# 🩺 Haydeén Sistema

**Gestión geriátrica híbrida: API REST, panel de escritorio y app móvil para enfermería.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![CustomTkinter](https://img.shields.io/badge/Desktop-CustomTkinter-1F6AA5)](https://customtkinter.tomschimansky.com/)
[![Tailwind CSS](https://img.shields.io/badge/Mobile-Tailwind%20CSS-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-MVP%20funcional-yellow.svg)](#-roadmap)

[Inicio en 3 pasos](#-inicio-rápido-3-pasos) · [Arquitectura](#-arquitectura-híbrida) · [Roles](#-roles-y-permisos) · [Comandos](#-comandos-útiles) · [Documentación](#-documentación-técnica)

</div>

---

> [!WARNING]
> **Aviso clínico.** Haydeén Sistema es una herramienta de apoyo administrativo y de registro. **No es un dispositivo médico**, no emite diagnósticos ni recomendaciones terapéuticas y no sustituye el criterio de profesionales sanitarios. Valida los flujos, la seguridad, la privacidad y la normativa aplicable antes de usarlo con pacientes reales. Consulta [`NOTICE`](NOTICE) y [`SECURITY.md`](SECURITY.md).

## 📌 Resumen ejecutivo

Haydeén Sistema centraliza la operación diaria de una residencia geriátrica o unidad de cuidados:

- **Pacientes**: expediente, residencia, habitación, peso, talla, IMC calculado, diagnóstico y alergias.
- **Personal y turnos**: roles, estado y turno del día.
- **Inventario**: medicamentos por lote, stock mínimo y caducidades.
- **Tratamientos**: dosis, vía, frecuencia y horarios.
- **Control diario**: signos vitales, DXTX (glucosa/insulina) y pañales.
- **App móvil**: consulta y registro en piso, con descuento de inventario al administrar.

Una sola API alimenta dos clientes: un **panel de escritorio** para administración y una **app web mobile-first** para enfermería.

## 🚀 Inicio rápido (3 pasos)

> Requisito previo: Laragon instalado con MySQL 8 y Python 3.10+.

### Paso 1 · Enciende Laragon

Abre Laragon y pulsa **Start All**. MySQL debe escuchar en `127.0.0.1:3306`.

### Paso 2 · Inicializa todo con un comando

Desde la raíz del proyecto, en **cmd**:

```cmd
api\.venv\Scripts\python.exe scripts\init_db.py
```

Ese único comando:

- crea `api/.env` si no existe y genera `SECRET_KEY`;
- crea la base `haydeensistem` si no existe;
- aplica el esquema y las migraciones;
- carga los datos demo;
- crea roles, permisos y los cuatro usuarios base;
- muestra las contraseñas generadas **una sola vez**.

Anota las contraseñas. No se vuelven a mostrar.

### Paso 3 · Arranca la API

Doble clic en **`iniciar_api.bat`** o desde cmd:

```cmd
iniciar_api.bat
```

| Recurso | URL |
| --- | --- |
| API | <http://127.0.0.1:8000> |
| OpenAPI | <http://127.0.0.1:8000/docs> |
| App móvil | <http://127.0.0.1:8000/app/> |
| Health check | <http://127.0.0.1:8000/api/health> |

Para el panel de escritorio, doble clic en **`iniciar_escritorio.bat`**.

> No necesitas activar `.venv`, no necesitas PowerShell y no necesitas ejecutar `mysql.exe` a mano.

### Primera vez: crea los entornos virtuales

Solo si acabas de clonar el repositorio. No actives nada; llama directamente al Python de cada entorno:

```cmd
python -m venv api\.venv
api\.venv\Scripts\python.exe -m pip install --upgrade pip
api\.venv\Scripts\python.exe -m pip install -r api\requirements.txt

python -m venv desktop\.venv
desktop\.venv\Scripts\python.exe -m pip install --upgrade pip
desktop\.venv\Scripts\python.exe -m pip install -r desktop\requirements.txt
```

### Abrir los clientes

- **Web móvil:** `http://127.0.0.1:8000/app/` en la PC.
- **Móvil real:** `http://<IP_LAN_DEL_SERVIDOR>:8000/app/` en la misma red.
- **Escritorio:** `iniciar_escritorio.bat`.

Obtén la IP local con:

```cmd
ipconfig
```

Si el móvil no conecta, permite el puerto en el Firewall (cmd como administrador):

```cmd
netsh advfirewall firewall add rule name="Haydeen API 8000" dir=in action=allow protocol=TCP localport=8000
```

> No expongas la API directamente a Internet. Usa VPN o reverse proxy con HTTPS.

## 🏗️ Arquitectura híbrida

```text
┌──────────────────────────────┐          ┌──────────────────────────────┐
│  PANEL DE ESCRITORIO         │          │  APP MÓVIL (NAVEGADOR)       │
│  Python + CustomTkinter      │          │  HTML + JS + Tailwind CSS    │
│  admin_panel.py              │          │  web/index.html              │
└──────────────┬───────────────┘          └──────────────┬───────────────┘
               │                                         │
               │  HTTP/JSON + Authorization: Bearer      │
               └──────────────────┬──────────────────────┘
                                  ▼
                 ┌────────────────────────────────────┐
                 │  API REST · FastAPI + Uvicorn      │
                 │  http://HOST:8000                  │
                 │  /api/*      endpoints JSON        │
                 │  /app/*      app móvil estática    │
                 │  /docs       OpenAPI interactivo   │
                 └────────────────┬───────────────────┘
                                  │  PyMySQL + pool (5 conexiones)
                                  ▼
                 ┌────────────────────────────────────┐
                 │  MySQL 8 · utf8mb4                 │
                 │  Base: haydeensistem               │
                 │  15 tablas de dominio              │
                 │  + rol_permisos                    │
                 └────────────────────────────────────┘
```

**Flujo de una petición**

1. El cliente envía usuario y contraseña a `POST /api/auth/login`.
2. La API verifica PBKDF2-SHA256 y crea un token aleatorio.
3. En la base solo se guarda `HMAC-SHA256(token, SECRET_KEY)`, nunca el token en claro.
4. Cada petición viaja con `Authorization: Bearer <token>`.
5. La dependencia `require_permiso()` valida el permiso del rol antes de ejecutar la consulta.
6. La API consulta MySQL con SQL parametrizado y devuelve JSON.

## 🧰 Stack tecnológico

| Capa | Tecnología |
| --- | --- |
| Lenguaje | Python 3.10+ (probado en 3.14.10) |
| API | FastAPI `>=0.115,<1.0`, Uvicorn `>=0.30,<1.0` |
| Base de datos | MySQL 8.0+ (probado en 8.4.3), PyMySQL `>=1.1,<2.0` |
| Validación | Pydantic v2 |
| Escritorio | CustomTkinter `>=5.2.2,<6.0`, Requests, Pillow |
| Móvil | HTML5, JavaScript ES Modules, Tailwind CSS |
| Seguridad | PBKDF2-SHA256 (260 000 iteraciones), HMAC-SHA256, permisos por rol |
| Scripts | Python 3.10+ y lanzadores `.bat` para `cmd` |
| Empaquetado | PyInstaller + Inno Setup (estructura preparada) |

## ✅ Requisitos del entorno

| Requisito | Detalle |
| --- | --- |
| Sistema operativo | Windows 10/11 para el panel. API y web son multiplataforma. |
| Laragon | MySQL 8 en `127.0.0.1:3306`. |
| Python | 3.10 o superior. |
| Consola | `cmd` o doble clic en los `.bat`. No se requiere PowerShell. |
| Git | Para clonar y versionar. |
| Navegador | Chrome, Edge, Firefox o Safari actualizado. |
| Opcional | Node.js 18+ solo para pruebas E2E. |

**Hardware objetivo**

| Rol | Mínimo recomendado |
| --- | --- |
| PC servidor (API + MySQL) | 2 vCPU, 4 GB RAM, 10 GB SSD, red 100 Mbps |
| PC de administración | 2 vCPU, 4 GB RAM, pantalla 1366×768 |
| Móvil de enfermería | Android/iOS actualizado, navegador moderno |
| Red | LAN con IP fija o reserva DHCP para el servidor |

No se requiere Docker.

## 🧪 Comando único de pruebas

Con la API levantada o apagada, el script se encarga de todo:

```cmd
api\.venv\Scripts\python.exe scripts\test_sistema.py
```

También puedes hacer doble clic en **`probar_sistema.bat`**.

Verifica:

- conexión a MySQL;
- `/api/ping` y `/api/health`;
- rechazo sin token (`401`);
- login de un usuario temporal;
- endpoints principales (`200`);
- RBAC: `administrativo` recibe `403` en tratamientos;
- limpieza de los usuarios temporales.

## 🛠️ Comandos útiles

| Comando | Qué hace |
| --- | --- |
| `api\.venv\Scripts\python.exe scripts\init_db.py` | Inicializa o actualiza todo (idempotente). |
| `... init_db.py --check` | Verifica conexión, base y tablas. |
| `... init_db.py --list` | Muestra roles, permisos y usuarios. |
| `... init_db.py --reset` | Recrea el esquema desde cero (**destructivo**). |
| `... init_db.py --no-demo` | Inicializa sin datos demo. |
| `... init_db.py --reset-passwords` | Rota las contraseñas existentes. |
| `... init_db.py --export-seed` | Exporta un seed JSON anonimizado. |
| `... init_db.py --import-seed RUTA` | Importa un seed JSON. |
| `api\.venv\Scripts\python.exe scripts\test_sistema.py` | Prueba rápida de BD, API y RBAC. |
| `iniciar_api.bat` | Arranca la API leyendo `api/.env`. |
| `iniciar_escritorio.bat` | Abre el panel CustomTkinter. |

## 🧯 Solución de problemas

| Síntoma | Solución |
| --- | --- |
| `Can't connect to MySQL server` | Laragon no está encendido o `DB_HOST`/`DB_PORT` no coinciden. `init_db.py` muestra el error técnico exacto. |
| `No existe api\.venv` | Ejecuta los comandos de “Primera vez” y vuelve a intentar. |
| `No existe api\.env` | Ejecuta `api\.venv\Scripts\python.exe scripts\init_db.py`. |
| Olvidé las contraseñas | `api\.venv\Scripts\python.exe scripts\init_db.py --reset-passwords`. |
| El puerto 8000 está ocupado | Cambia `API_PORT` en `api/.env` y vuelve a ejecutar `iniciar_api.bat`. |
| La app móvil no abre desde el teléfono | Revisa la IP LAN, el firewall y que la API escuche en `0.0.0.0`. |
| Ves acentos raros en `cmd` | Ejecuta `chcp 65001` antes del comando. Los `.bat` ya lo configuran. |
| Quiero empezar de cero | `api\.venv\Scripts\python.exe scripts\init_db.py --reset`. |

## 👥 Roles y permisos

`init_db.py` crea cuatro usuarios operativos. Los roles `farmacia` y `recepcion` existen en el esquema para asignación futura.

| Usuario | Rol | Acceso |
| --- | --- | --- |
| `admin` | `admin` | Total (`*`): todos los módulos y escrituras. |
| `medico` | `medico` | Lectura clínica, tratamientos y administración de medicamentos. |
| `enfermero` | `enfermeria` | Signos vitales, DXTX, pañales y administración con descuento de stock. |
| `administrativo` | `administrativo` | Inventario, personal y lectura de pacientes. |

Matriz técnica de permisos:

| Permiso | admin | medico | enfermeria | administrativo | farmacia | recepcion |
| --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `dashboard:leer` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `pacientes:leer` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `personal:leer` | ✅ | ✅ | — | ✅ | — | ✅ |
| `personal:escribir` | ✅ | — | — | ✅ | — | — |
| `inventario:leer` | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| `inventario:escribir` | ✅ | — | — | ✅ | ✅ | — |
| `tratamientos:leer` | ✅ | ✅ | ✅ | — | ✅ | — |
| `tratamientos:escribir` | ✅ | ✅ | — | — | — | — |
| `control:leer` | ✅ | ✅ | ✅ | — | — | — |
| `control:escribir` | ✅ | — | ✅ | — | — | — |
| `administracion:escribir` | ✅ | ✅ | ✅ | — | — | — |

Los permisos viven en la tabla `rol_permisos` y se aplican con `require_permiso()` en cada endpoint. `admin` usa el comodín `*`.

### Contraseñas

- `init_db.py` genera contraseñas aleatorias (16 caracteres) si no se indican.
- También puedes fijarlas por CLI o variable de entorno:

```cmd
api\.venv\Scripts\python.exe scripts\init_db.py --password-admin "UnaClaveLarga#2026" --password-medico "OtraClaveLarga#2026"
```

```cmd
set SEED_ENFERMERO_PASSWORD=ClaveEnfermeria#2026
api\.venv\Scripts\python.exe scripts\init_db.py
```

- Para rotar todas las claves existentes:

```cmd
api\.venv\Scripts\python.exe scripts\init_db.py --reset-passwords
```

Nunca hay contraseñas en texto plano dentro del repositorio ni en `schema.sql`.

## 🌱 Seeds y datos iniciales

`scripts/init_db.py` usa la conexión real de `api/db.py` y el hash de `api/security.py`.

```cmd
:: Crear/actualizar todo
api\.venv\Scripts\python.exe scripts\init_db.py

:: Ver roles, permisos y usuarios
api\.venv\Scripts\python.exe scripts\init_db.py --list

:: Verificar conexión y esquema
api\.venv\Scripts\python.exe scripts\init_db.py --check

:: Exportar configuración + catálogo + pacientes demo anonimizados
api\.venv\Scripts\python.exe scripts\init_db.py --export-seed

:: Importar un seed en otra instalación
api\.venv\Scripts\python.exe scripts\init_db.py --import-seed database\seeds\initial_data.json
```

El JSON se escribe en `database/seeds/initial_data.json` con `encoding="utf-8"` y `ensure_ascii=False`, por lo que conserva acentos y `ñ`. Incluye:

- roles y matriz de permisos;
- usuarios con su `password_hash` PBKDF2 (nunca la contraseña);
- catálogo de medicamentos y lotes;
- pacientes demo **anonimizados** (sin contacto familiar ni teléfono).

> El archivo contiene hashes y datos clínicos: está en `.gitignore` y no debe publicarse. La importación es idempotente.

## 🔌 API en una mirada

| Módulo | Endpoints |
| --- | --- |
| Auth | `POST /api/auth/login`, `GET /api/auth/me` |
| Sistema | `GET /api/ping`, `GET /api/health`, `GET /api/dashboard/stats` |
| Pacientes | `GET /api/pacientes` |
| Personal | `GET /api/personal` |
| Inventario | `GET /api/inventario`, `GET /api/inventario/lotes` |
| Tratamientos | `GET /api/tratamientos`, `POST /api/administraciones` |
| Control diario | `GET /api/control-diario`, `POST /api/signos-vitales` |

Detalle de tablas, reglas de negocio y ejemplos en [`docs/BASE_DE_DATOS_Y_API.md`](docs/BASE_DE_DATOS_Y_API.md).

## 📁 Estructura del proyecto

```text
haydeensistem/
├── api/                      # FastAPI + PyMySQL
│   ├── main.py               # Endpoints, modelos y montaje de /app
│   ├── db.py                 # Pool de conexiones thread-safe
│   ├── security.py           # PBKDF2, HMAC de tokens y permisos
│   ├── config.py             # Variables de entorno
│   ├── requirements.txt
│   ├── .env.example
│   └── .venv/                # Ignorado por Git
├── database/
│   ├── schema.sql            # Esquema completo (16 tablas)
│   ├── demo_data.sql         # Datos sintéticos idempotentes
│   ├── migrations/           # Migraciones incrementales
│   └── seeds/                # Exportaciones JSON (ignoradas por Git)
├── desktop/
│   ├── admin_panel.py        # Panel CustomTkinter
│   └── assets/
├── web/
│   ├── index.html            # Shell móvil
│   ├── css/styles.css
│   └── js/api.js, app.js
├── scripts/
│   ├── init_db.py            # Inicialización completa e idempotente
│   ├── run_api.py            # Arranque de Uvicorn leyendo api/.env
│   └── test_sistema.py       # Prueba rápida de BD, API y RBAC
├── docs/                     # Documentación técnica y capturas
├── packaging/                # PyInstaller e Inno Setup
├── .github/                  # Plantillas de PR e issues
├── iniciar_api.bat           # Arranque con doble clic
├── iniciar_escritorio.bat    # Panel de escritorio
├── probar_sistema.bat        # Pruebas con doble clic
├── README.md
├── SECURITY.md
├── SECURITY_CHECKLIST.md
├── CONTRIBUTING.md
├── LICENSE
└── NOTICE
```

## 🔐 Seguridad

- Contraseñas con **PBKDF2-SHA256** y salt aleatorio (260 000 iteraciones).
- Tokens de sesión aleatorios; en reposo solo se guarda **HMAC-SHA256** con `SECRET_KEY`.
- **RBAC** por rol en cada endpoint mediante `require_permiso()`.
- SQL **parametrizado** en todas las consultas.
- Validación de entrada con **Pydantic** y `CHECK` en MySQL.
- Cero credenciales en el repositorio: `.env` ignorado y `schema.sql` sin usuarios.
- `init_db.py` genera `SECRET_KEY` y contraseñas aleatorias; nunca escribe claves en el código.
- Frontend móvil con escape de HTML antes de insertar datos dinámicos.

Pendiente antes de producción: logout con revocación en servidor, rate limiting, HTTPS, auditoría genérica y respaldos automáticos. Revisa [`SECURITY_CHECKLIST.md`](SECURITY_CHECKLIST.md).

## 📚 Documentación técnica

| Documento | Contenido |
| --- | --- |
| [`docs/ARQUITECTURA_Y_ESTRUCTURA.md`](docs/ARQUITECTURA_Y_ESTRUCTURA.md) | Árbol detallado y decisiones de diseño |
| [`docs/BASE_DE_DATOS_Y_API.md`](docs/BASE_DE_DATOS_Y_API.md) | Tablas, relaciones, reglas y endpoints |
| [`docs/GUIA_COLABORACION.md`](docs/GUIA_COLABORACION.md) | Ramas, migraciones y flujo de equipo |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Convenciones de código y commits |
| [`SECURITY.md`](SECURITY.md) | Reporte de vulnerabilidades |
| [`SECURITY_CHECKLIST.md`](SECURITY_CHECKLIST.md) | Verificación pre-push |
| [`docs/screenshots/`](docs/screenshots/) | Capturas placeholder editables |

## 🗺️ Roadmap

- [x] API FastAPI + MySQL con SQL parametrizado.
- [x] Panel de escritorio con dashboard y listados reales.
- [x] App móvil con login, pacientes, tratamientos y control diario.
- [x] Registro de signos vitales y administración con descuento de inventario.
- [x] RBAC por rol y permisos en base de datos.
- [x] Inicialización unificada con `init_db.py` y lanzadores `.bat`.
- [x] Prueba rápida con `test_sistema.py`.
- [ ] Logout con revocación de sesión en servidor.
- [ ] Rate limiting y bloqueo progresivo en login.
- [ ] Auditoría genérica de cambios.
- [ ] HTTPS con reverse proxy y HSTS.
- [ ] Respaldos automáticos cifrados y restauración probada.
- [ ] Pruebas automatizadas y CI.
- [ ] Instaladores con PyInstaller + Inno Setup.
- [ ] Tailwind compilado localmente.

## 📄 Licencia

Distribuido bajo **MIT License**. Consulta [`LICENSE`](LICENSE) y [`NOTICE`](NOTICE).

MIT permite uso comercial y educativo, exige conservar el aviso de copyright y limita la responsabilidad sobre el software. **No sustituye las obligaciones sanitarias, de privacidad ni la responsabilidad por negligencia.** El aviso clínico completo está en [`NOTICE`](NOTICE).

---

<div align="center">

Hecho para apoyo operativo en residencias geriátricas.

**No es un dispositivo médico. Verifica siempre con personal sanitario cualificado.**

</div>
