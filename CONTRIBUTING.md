# Guía de Contribución

Gracias por querer mejorar Haydeén Sistema. Esta guía describe el flujo de trabajo, las convenciones y los controles mínimos para mantener un proyecto claro, seguro y mantenible.

> **Seguridad primero:** si encontraste una vulnerabilidad, **no abras un issue público**. Sigue el proceso de [`SECURITY.md`](SECURITY.md).

## Código de conducta

- Trata a todas las personas con respeto.
- No se toleran acoso, discriminación, ataques personales ni divulgación de datos privados.
- Prioriza el bienestar de los pacientes y la privacidad de sus datos.
- Acepta críticas técnicas con apertura y argumenta con evidencia.
- En desacuerdos de diseño, busca la opción más simple, segura y mantenible.

Este proyecto adopta los principios del [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

## Formas de contribuir

- Reportar errores con pasos de reproducción.
- Proponer mejoras funcionales o de experiencia de usuario.
- Mejorar documentación, capturas o textos.
- Escribir pruebas automatizadas.
- Corregir errores o vulnerabilidades.
- Traducir o revisar la terminología clínica.

Para cambios grandes, abre primero un issue con la propuesta y el alcance. Así evitamos trabajo duplicado.

## Configuración del entorno

Sigue la sección de instalación de [`README.md`](README.md). Resumen:

```powershell
python -m venv api\.venv
api\.venv\Scripts\python.exe -m pip install -r api\requirements.txt

python -m venv desktop\.venv
desktop\.venv\Scripts\python.exe -m pip install -r desktop\requirements.txt

Copy-Item api\.env.example api\.env
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\import_demo.ps1
```

No uses datos reales de pacientes en desarrollo. Usa los datos de `database/demo_data.sql` o datos sintéticos.

## Modelo de ramas

| Rama | Propósito | Origen | Destino |
| --- | --- | --- | --- |
| `main` | Código estable y publicable | — | — |
| `dev` | Integración del equipo | `main` | `main` |
| `feature/<ticket>-<slug>` | Nueva funcionalidad | `dev` | `dev` |
| `fix/<ticket>-<slug>` | Corrección no urgente | `dev` | `dev` |
| `hotfix/<ticket>-<slug>` | Corrección urgente de producción | `main` | `main` y `dev` |
| `docs/<slug>` | Documentación | `dev` | `dev` |
| `chore/<slug>` | Mantenimiento, dependencias, tooling | `dev` | `dev` |
| `security/<slug>` | Corrección de seguridad | `main` | `main` y `dev` |

Reglas:

- Una rama por cambio lógico.
- Mantén las ramas cortas y actualiza con `git rebase dev` antes del PR.
- No hagas merge de `dev` hacia tu rama si puedes hacer rebase.
- No subas ramas personales con nombres genéricos (`test`, `cambios`, `final`).

Ejemplos:

```text
feature/123-exportar-pacientes-csv
fix/145-corregir-imc-menor-edad
hotfix/201-revocar-sesiones
docs/actualizar-instalacion-lan
security/210-rate-limit-login
```

## Commits convencionales

Usamos [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):

```text
<tipo>(<alcance>): <descripción breve en imperativo>

[cuerpo opcional]

[footer opcional]
```

### Tipos permitidos

| Tipo | Uso |
| --- | --- |
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de un error |
| `docs` | Documentación |
| `style` | Formato sin cambios de lógica |
| `refactor` | Reestructuración sin cambiar comportamiento |
| `perf` | Mejora de rendimiento |
| `test` | Pruebas |
| `build` | Sistema de build o dependencias |
| `ci` | Integración continua |
| `chore` | Mantenimiento |
| `revert` | Revertir un cambio |
| `security` | Corrección o endurecimiento de seguridad |

### Alcances sugeridos

`api`, `desktop`, `web`, `db`, `auth`, `inventory`, `patients`, `treatments`, `docs`, `scripts`, `deps`, `release`.

### Ejemplos

```text
feat(web): agregar búsqueda de pacientes por habitación
fix(api): validar presión sistólica y diastólica juntas
docs(readme): documentar acceso desde LAN
security(auth): agregar rate limiting al login
refactor(db): centralizar consultas de inventario
```

### Cambios incompatibles

Añade `!` después del tipo/alcance y explica el cambio en el footer:

```text
feat(api)!: cambiar el formato de respuesta de /api/pacientes

BREAKING CHANGE: el campo `paciente` ahora se llama `nombre_completo`.
```

### Buenos hábitos

- Un commit = un cambio coherente.
- Imperativo y en español: “agrega”, “corrige”, “documenta”.
- Máximo ~72 caracteres en el asunto.
- No mezcles refactorizaciones grandes con correcciones funcionales.
- Firma tus commits con DCO: `git commit -s`.

## Pull requests

### Antes de abrir el PR

- [ ] La rama está actualizada con `main`.
- [ ] El cambio está probado localmente.
- [ ] No hay secretos, `.env`, tokens, volcados ni datos de pacientes.
- [ ] La documentación se actualizó si cambió el comportamiento.
- [ ] Los commits siguen Conventional Commits.
- [ ] El PR tiene un alcance revisable.

### Plantilla de PR

```markdown
## Qué cambia

Describe el cambio en 2–5 líneas.

## Por qué

Explica el problema, el issue relacionado y el impacto esperado.

Closes #<ticket>

## Cómo probar

1. ...
2. ...
3. ...

## Evidencia

- Capturas de escritorio/móvil si aplica.
- Respuestas de API o logs relevantes (sin datos sensibles).

## Checklist

- [ ] Probé la API localmente.
- [ ] Probé el panel de escritorio si apliqué cambios de UI.
- [ ] Probé la app móvil si apliqué cambios de UI.
- [ ] Actualicé README/SECURITY/CONTRIBUTING si aplica.
- [ ] No incluí secretos ni datos reales.
- [ ] Ejecuté las verificaciones de `SECURITY_CHECKLIST.md` si el cambio es sensible.
```

### Revisión

- Se requiere al menos **una aprobación** para cambios normales.
- Los cambios de seguridad, autenticación, permisos o esquema requieren **dos aprobaciones**.
- El autor resuelve los comentarios; el revisor aprueba.
- Usa **Squash and merge** con un título conventional commit.
- No hagas merge con checks rojos o conflictos pendientes.

## Estilo de código

### Python

- PEP 8, 4 espacios, máximo ~100 caracteres.
- Usa `from __future__ import annotations` en módulos nuevos.
- Tipa funciones y métodos públicos.
- Docstrings breves en módulos y funciones no triviales.
- No uses ORM: SQL explícito y parametrizado.
- Nunca concatenes entrada de usuario en SQL; usa `%s` y parámetros.
- Usa `logging`, no `print`, en la API.
- Maneja excepciones específicas y no silencies errores sin registro.
- Mantén la lógica de negocio en la API, no en los clientes.

### JavaScript

- ES Modules, 2 espacios, punto y coma.
- `const` por defecto; `let` solo si se reasigna.
- Escapa datos dinámicos antes de insertarlos en HTML (`esc` en `web/js/app.js`).
- No uses `eval`, `Function` ni `innerHTML` con datos no confiables.
- No guardes secretos en el frontend. El token va en `localStorage` solo porque es una app de LAN; para producción evalúa cookies `HttpOnly` + CSRF.
- Mantén el diseño mobile-first y objetivos táctiles de al menos 44 px.

### SQL

- Palabras clave en mayúsculas y nombres de tabla/columna entre backticks.
- `utf8mb4` y `utf8mb4_unicode_ci`.
- Claves foráneas explícitas con `ON UPDATE`/`ON DELETE` justificados.
- Índices para columnas de búsqueda y claves foráneas.
- No borres columnas ni tablas sin migración y aprobación.
- Los cambios de esquema deben ser idempotentes o reversibles.

### UI y textos

- Textos de interfaz en español, claros y sin jerga innecesaria.
- Errores accionables: qué pasó y qué hacer.
- No muestres trazas internas al usuario final.
- Respeta `prefers-reduced-motion` y el tamaño táctil.
- Las capturas deben usar datos sintéticos.

## Pruebas y verificación

### Verificación rápida

```powershell
# Sintaxis Python
python -m py_compile api\main.py api\db.py api\security.py api\config.py desktop\admin_panel.py

# Sintaxis JavaScript
node --check web\js\app.js
node --check web\js\api.js
```

### Smoke test de API

Con la API en ejecución:

```powershell
$base = "http://127.0.0.1:8000/api"
$login = Invoke-RestMethod -Uri "$base/auth/login" -Method Post `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"<CLAVE_DEL_SEEDER>"}'
$headers = @{ Authorization = "Bearer $($login.token)" }

Invoke-RestMethod -Uri "$base/pacientes" -Headers $headers | Out-Null
Invoke-RestMethod -Uri "$base/personal" -Headers $headers | Out-Null
Invoke-RestMethod -Uri "$base/inventario" -Headers $headers | Out-Null
Invoke-RestMethod -Uri "$base/tratamientos" -Headers $headers | Out-Null
Invoke-RestMethod -Uri "$base/control-diario" -Headers $headers | Out-Null

"Smoke test OK"
```

### Panel de escritorio

1. Inicia la API.
2. Ejecuta `desktop\.venv\Scripts\python.exe admin_panel.py`.
3. Inicia sesión y recorre todos los módulos.
4. Verifica que las tablas carguen filas y que el control diario cambie de pestaña.

### App móvil

1. Abre `http://127.0.0.1:8000/app/`.
2. Inicia sesión.
3. Prueba búsqueda, navegación, modal de signos y administración.
4. Si tienes Playwright, agrega o ejecuta pruebas E2E con datos sintéticos.

### Base de datos

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\import_demo.ps1
```

Verifica que los acentos se conserven (`Martínez`, `Ríos`, `González`) y que no se dupliquen registros al ejecutar dos veces.

## Seguridad en contribuciones

- No incluyas `.env`, contraseñas, tokens, claves, certificados ni volcados.
- No incluyas datos reales de pacientes, familiares o personal.
- Usa datos sintéticos en pruebas y capturas.
- Si el cambio toca autenticación, permisos, SQL, sesiones o inventario, completa [`SECURITY_CHECKLIST.md`](SECURITY_CHECKLIST.md).
- Reporta vulnerabilidades por el canal privado de [`SECURITY.md`](SECURITY.md).
- Nunca desactives una validación de seguridad para “hacer que funcione”.

## DCO y licencia de contribuciones

Al enviar un pull request aceptas que tu contribución se licencie bajo la **MIT License** del proyecto. Firma tus commits con el [Developer Certificate of Origin](https://developercertificate.org/):

```powershell
git commit -s -m "feat(web): agregar búsqueda por habitación"
```

El `Signed-off-by` certifica que tienes derecho a contribuir el código. No se requiere CLA adicional.

## Publicaciones y versiones

- Versionado semántico: `MAJOR.MINOR.PATCH`.
- Etiqueta: `v0.1.0`.
- Actualiza el `CHANGELOG.md` si existe.
- Los cambios incompatibles suben `MAJOR`.
- Las correcciones de seguridad se documentan sin revelar detalles explotables antes del parche.
- Genera el instalador de escritorio solo desde una rama etiquetada y verificada.

## ¿Dudas?

Abre un issue de tipo `question` con contexto, versión y lo que ya intentaste. Para temas sensibles, usa el canal privado de seguridad.
