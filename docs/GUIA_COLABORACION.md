# Guía de colaboración

Flujo de trabajo para el equipo de desarrollo de Haydeén Sistema.

> Para reportar vulnerabilidades usa el canal privado de [`SECURITY.md`](../SECURITY.md). No abras issues públicos con detalles explotables.

## 1. Incorporación al proyecto

1. Instala Laragon, Python 3.10+ y Git.
2. Clona el repositorio y crea los entornos virtuales (`README.md`, guía rápida).
3. Copia `api/.env.example` a `api/.env` y genera tu `SECRET_KEY`.
4. Ejecuta `scripts/import_demo.ps1` para crear esquema, demo y usuarios.
5. Verifica `scripts/seed_system.py --check` y abre `/docs`.
6. Lee [`ARQUITECTURA_Y_ESTRUCTURA.md`](ARQUITECTURA_Y_ESTRUCTURA.md) y [`BASE_DE_DATOS_Y_API.md`](BASE_DE_DATOS_Y_API.md).

Nunca uses datos reales de pacientes en desarrollo. Usa `database/demo_data.sql` o datos sintéticos.

## 2. Ramas

| Rama | Propósito | Origen | Destino |
| --- | --- | --- | --- |
| `main` | Código estable y desplegable | — | — |
| `dev` | Integración del equipo | `main` | `main` |
| `feature/<ticket>-<slug>` | Nueva funcionalidad | `dev` | `dev` |
| `fix/<ticket>-<slug>` | Corrección no urgente | `dev` | `dev` |
| `hotfix/<ticket>-<slug>` | Corrección urgente | `main` | `main` y `dev` |
| `docs/<slug>` | Documentación | `dev` | `dev` |
| `security/<slug>` | Endurecimiento o parche | `main` | `main` y `dev` |

Reglas:

- Una rama por cambio lógico.
- Actualiza con `git rebase dev` antes del PR.
- No subas ramas genéricas (`test`, `cambios`, `final`).
- `main` solo recibe merges desde PR aprobados.

Ejemplos:

```text
feature/142-exportar-pacientes-csv
fix/158-corregir-imc-talla-cero
security/171-rate-limit-login
docs/actualizar-guia-lan
```

## 3. Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):

```text
<tipo>(<alcance>): <descripción en imperativo>

[cuerpo opcional]

[footer opcional]
```

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `security`.

Alcances: `api`, `desktop`, `web`, `db`, `auth`, `inventory`, `patients`, `treatments`, `docs`, `scripts`, `deps`, `release`.

```text
feat(web): agregar búsqueda por habitación
fix(api): validar presión sistólica y diastólica juntas
security(auth): aplicar rate limiting al login
db(migration): agregar tabla de auditoría
```

Firma tus commits con DCO:

```powershell
git commit -s -m "feat(api): agregar endpoint de logout"
```

## 4. Cambios en la base de datos

**Regla de oro:** `schema.sql` no se sobrescribe para cambios incrementales.

### Procedimiento

1. Crea `database/migrations/NNN_descripcion.sql` con el siguiente número libre.
2. Hazla **idempotente** (`CREATE TABLE IF NOT EXISTS`, `INSERT IGNORE`, `ADD COLUMN IF NOT EXISTS` cuando aplique).
3. No elimines columnas ni tablas con datos sin un plan de migración y respaldo.
4. Prueba sobre una copia de la base, no sobre la de un compañero.
5. Actualiza también `schema.sql` para instalaciones nuevas.
6. Documenta en el PR: SQL ejecutado, impacto, tiempo estimado y plan de reversa.
7. Actualiza [`BASE_DE_DATOS_Y_API.md`](BASE_DE_DATOS_Y_API.md) si cambian tablas, reglas o endpoints.

### Plantilla de migración

```sql
-- ============================================================
-- Migración NNN · Descripción breve
-- Idempotente. No elimina datos.
-- ============================================================

USE `haydeensistem`;
SET NAMES utf8mb4;

-- Cambios aquí.
```

### Prohibido

- `DROP DATABASE` o `TRUNCATE` en migraciones.
- Credenciales, rutas locales o datos reales en archivos SQL.
- Ejecutar migraciones en producción sin respaldo verificado.
- Modificar una migración ya aplicada: crea una nueva.

## 5. Pull requests

Antes de abrir el PR:

- [ ] Rama actualizada con `dev`.
- [ ] Cambio probado en API, escritorio y/o móvil según corresponda.
- [ ] Sin secretos, `.env`, volcados ni datos reales.
- [ ] Documentación actualizada.
- [ ] Commits con Conventional Commits y `Signed-off-by`.
- [ ] Si toca SQL, incluye la migración y el plan de reversa.

Flujo:

1. Abre el PR con la plantilla de `.github/pull_request_template.md`.
2. Asigna al menos un revisor; dos si toca autenticación, permisos, SQL o inventario.
3. Resuelve comentarios y mantén el PR pequeño.
4. Squash and merge con título conventional commit.
5. Elimina la rama después del merge.

No se hace merge con conflictos, checks rojos o revisión pendiente.

## 6. Revisión de código

El revisor comprueba:

- **Seguridad:** SQL parametrizado, permisos correctos, sin secretos, sin datos reales.
- **Corrección:** reglas clínicas y de inventario intactas.
- **Consistencia:** estilo del proyecto, nombres en español, mensajes claros.
- **Pruebas:** evidencia de los flujos tocados.
- **Documentación:** README/docs/migraciones actualizados.

Comentarios: sé específico, propón alternativas y distingue bloqueante de sugerencia.

## 7. Estilo y pruebas

Resumen; el detalle está en [`CONTRIBUTING.md`](../CONTRIBUTING.md).

```powershell
# Sintaxis
api\.venv\Scripts\python.exe -m py_compile api\main.py api\db.py api\security.py api\config.py scripts\seed_system.py desktop\admin_panel.py
node --check web\js\api.js
node --check web\js\app.js

# Seeder
api\.venv\Scripts\python.exe scripts\seed_system.py --check
api\.venv\Scripts\python.exe scripts\seed_system.py --list

# Smoke test de API
$login = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" -Method Post `
  -ContentType "application/json" -Body '{"username":"admin","password":"<CLAVE>"}'
$headers = @{ Authorization = "Bearer $($login.token)" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/pacientes" -Headers $headers | Out-Null
```

Prueba siempre:

- Login correcto e incorrecto.
- Matriz de permisos si cambiaste roles.
- Registro de signos y administración con descuento de stock.
- Importación demo dos veces (idempotencia y acentos).
- Export/import de seed en una base limpia.

## 8. Seguridad en el equipo

- Cada desarrollador usa su propia `SECRET_KEY` local.
- No compartas `api/.env` por chat ni correo.
- No subas `database/seeds/*.json`: contiene hashes.
- Rota contraseñas con `seed_system.py --apply --reset-passwords` si sospechas exposición.
- No desactives `require_permiso()` para “probar rápido”.
- Reporta vulnerabilidades por el canal privado.

## 9. Releases

1. Congela `dev` y ejecuta el checklist pre-push.
2. Actualiza versión en `api/config.py` y documentación.
3. Etiqueta `vMAJOR.MINOR.PATCH`.
4. Genera el instalador solo desde una etiqueta verificada.
5. Publica notas sin revelar detalles explotables antes del parche.

## 10. ¿Dudas?

Abre un issue de tipo `question` con contexto, versión y lo que ya intentaste. Para temas sensibles, usa el canal privado de seguridad.
