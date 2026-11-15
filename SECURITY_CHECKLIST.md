# Checklist de Seguridad Pre-Push

Lista de verificación **obligatoria** antes del primer `git push` y antes de cualquier despliegue con datos reales.

> Este documento es operativo, no una certificación. Marca cada casilla solo cuando hayas comprobado el resultado con el comando o la prueba indicada. Si un ítem marcado como **BLOQUEANTE** falla, no publiques ni desplegues.

**Leyenda**

| Símbolo | Significado |
| --- | --- |
| 🔴 BLOQUEANTE | Impide el push o el despliegue hasta corregirse |
| 🟠 ALTO | Debe resolverse antes de usar datos reales |
| 🟡 MEDIO | Aceptable en demo/LAN, no en producción |
| ⚪ INFORMATIVO | Registro de deuda técnica conocida |

---

## 0. Estado del repositorio

- [ ] 🔴 El directorio no contiene repositorios Git anidados ni restos de otro proyecto.

```powershell
Get-ChildItem -Recurse -Force -Directory -Filter .git |
  Where-Object { $_.FullName -ne (Join-Path $PWD '.git') } |
  Select-Object FullName
```

- [ ] 🔴 `.gitignore` está en la raíz y cubre secretos, entornos virtuales, cachés, logs y volcados.
- [ ] 🔴 `git init` se ejecutó **después** de revisar este checklist, o el historial está limpio.

```powershell
git status --short
git log --oneline --all
```

---

## 1. Secretos y credenciales

- [ ] 🔴 `api/.env` existe en disco pero **no** está rastreado.

```powershell
git check-ignore -v api/.env
git ls-files --error-unmatch api/.env 2>$null
```

La segunda orden debe fallar. Si devuelve una ruta, el archivo está rastreado:

```powershell
git rm --cached api/.env
```

- [ ] 🔴 No hay contraseñas, tokens, claves privadas ni cadenas de conexión en el código.

```powershell
git grep -n -I -E "(password|passwd|secret|token|api[_-]?key|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY)\s*[:=]" -- `
  "*.py" "*.js" "*.ps1" "*.sql" "*.json" "*.md" "*.example"
```

Revisa cada coincidencia. Son aceptables nombres de variables y textos de documentación; **no** lo son valores reales.

- [ ] 🔴 No hay archivos `.env`, `.pem`, `.key`, `.pfx`, `.p12`, `.jks` ni volcados en el índice.

```powershell
git ls-files | Select-String -Pattern "\.(env|pem|key|pfx|p12|jks|dump|bak)$|\.sql\.gz$|\.sql\.zip$"
```

- [ ] 🔴 El historial no contiene secretos (relevante si ya hiciste commits).

```powershell
# Opción A: gitleaks (recomendado)
docker run --rm -v "${PWD}:/repo" zricethezav/gitleaks:latest detect -s /repo -v

# Opción B: sin Docker, revisar el diff completo
git log -p --all | Select-String -Pattern "admin123|SEED_[A-Z_]*PASSWORD\s*=\s*\S+|DB_PASSWORD\s*=\s*\S+"
```

> Si un secreto ya entró al historial, **no basta con borrarlo del último commit**. Rota la credencial y reescribe el historial (`git filter-repo`) antes de publicar.

- [ ] 🔴 `api/.env.example` solo contiene valores vacíos o de ejemplo, nunca credenciales reales.
- [ ] 🟠 El correo y el usuario de GitHub en `SECURITY.md` fueron reemplazados (`<OWNER>`, `<REPO>`, `security@example.com`).

```powershell
Select-String -Path SECURITY.md -Pattern "<OWNER>|<REPO>|security@example.com"
```

- [ ] 🟠 `NOTICE` tiene el titular real en lugar de `[NOMBRE DEL TITULAR O ENTIDAD]`.

---

## 2. Base de datos y SQL

- [ ] 🔴 `database/schema.sql` no contiene credenciales reales, cadenas de conexión ni rutas absolutas de tu equipo.
- [ ] 🔴 `database/demo_data.sql` solo contiene datos sintéticos. Sin nombres, documentos, teléfonos ni diagnósticos de personas reales.

```powershell
git grep -n -I -E "INSERT INTO .*(pacientes|personal|usuarios)" -- "database/*.sql" |
  Measure-Object
```

Revisa manualmente una muestra de cada tabla.

- [ ] 🔴 `schema.sql` **no** contiene usuarios ni hashes de contraseña. Los usuarios se crean con `scripts/seed_system.py`.
- [ ] 🔴 `database/seeds/*.json` está ignorado por Git y no se subió (contiene hashes PBKDF2).
- [ ] 🟠 Las contraseñas generadas por el seeder se rotaron antes de compartir el entorno.
- [ ] 🟠 El usuario MySQL de la aplicación **no** es `root`. Tiene solo `SELECT, INSERT, UPDATE, DELETE` sobre `haydeensistem`.

```sql
-- Ejecutar como administrador de MySQL
CREATE USER 'haydeen_app'@'localhost' IDENTIFIED BY '<CLAVE_FUERTE>';
GRANT SELECT, INSERT, UPDATE, DELETE ON haydeensistem.* TO 'haydeen_app'@'localhost';
FLUSH PRIVILEGES;
```

- [ ] 🟠 El usuario de aplicación no tiene `DROP`, `ALTER`, `GRANT OPTION` ni acceso a `mysql.*`.
- [ ] 🟡 Los respaldos se generan con un usuario dedicado y se almacenan cifrados fuera del repositorio.

---

## 3. Autenticación, sesiones y autorización

- [ ] 🔴 Las contraseñas se almacenan con PBKDF2-SHA256 (o Argon2/bcrypt), nunca en texto plano ni con MD5/SHA1.
- [ ] 🔴 Los tokens de sesión se guardan como hash en la base de datos (`token_hash`), no en claro.
- [ ] 🔴 `SESSION_HOURS` tiene un valor razonable (≤ 12 h en clínica; ≤ 1 h en equipos compartidos).
- [ ] 🟠 Existe un endpoint de **logout** que borra la sesión en el servidor. *Estado actual: no implementado.*
- [ ] 🔴 Existe **RBAC** por rol en cada endpoint sensible. *Implementado con `rol_permisos` y `require_permiso()`.*
- [ ] 🔴 `SECRET_KEY` está definida y no se comparte por chat ni se sube al repositorio.
- [ ] 🟠 La matriz de permisos se revisó: cada rol tiene solo lo necesario. *Ver `seed_system.py --list`.*
- [ ] 🟠 Al cambiar `SECRET_KEY` se aceptaron como invalidadas las sesiones activas.
- [ ] 🟠 Existe **rate limiting** y bloqueo progresivo en `/api/auth/login`. *Estado actual: no implementado.*
- [ ] 🟠 Las sesiones vencidas se limpian periódicamente.

```sql
DELETE FROM sesiones WHERE expira_en < UTC_TIMESTAMP();
```

- [ ] 🟡 Se registra el intento fallido de login (sin guardar la contraseña) para detectar fuerza bruta.
- [ ] 🟡 El token se guarda en `localStorage` solo por la naturaleza LAN de la app. Para Internet, migrar a cookie `HttpOnly` + `SameSite` + CSRF.

---

## 4. Entradas, consultas y salidas

- [ ] 🔴 Todas las consultas usan parámetros `%s` de PyMySQL. Sin f-strings, `.format()` ni concatenación con datos de usuario.

```powershell
git grep -n -I -E "(execute|executemany)\(.*(f\"|f'|\.format\(|% \()" -- "api/*.py"
```

Debe devolver vacío.

- [ ] 🔴 Los `POST` validan tipos, rangos y campos obligatorios con Pydantic.
- [ ] 🔴 Los valores clínicos tienen rangos plausibles (p. ej. temperatura 30–45 °C, SpO₂ 0–100 %, TA sistólica > diastólica).
- [ ] 🔴 El frontend escapa HTML antes de insertar datos dinámicos (`esc()` en `web/js/app.js`).
- [ ] 🟠 Los mensajes de error no exponen trazas, SQL ni rutas internas al cliente.
- [ ] 🟠 Los IDs de paciente, tratamiento y lote se validan contra la base de datos; no se confía en el cliente (evitar IDOR).
- [ ] 🟡 Los formularios móviles tienen límites de longitud y `inputmode`/`type` adecuados.
- [ ] 🟡 La administración de medicamentos verifica lote, caducidad y stock antes de descontar.

---

## 5. Red, transporte y configuración

- [ ] 🔴 `CORS_ORIGINS` **no** es `*` fuera de desarrollo local.

```powershell
Select-String -Path api\.env -Pattern "^CORS_ORIGINS="
```

- [ ] 🔴 La API no está expuesta directamente a Internet. Solo LAN, VPN o reverse proxy.
- [ ] 🔴 El Firewall de Windows limita el puerto 8000 a la subred local, no a `Any`.

```powershell
Get-NetFirewallRule -DisplayName "Haydeen API 8000" |
  Get-NetFirewallAddressFilter
```

- [ ] 🟠 En producción se usa **HTTPS** con certificado válido (Caddy, Nginx o Traefik) y HSTS.
- [ ] 🟠 `uvicorn` no se ejecuta con `--reload` en producción.
- [ ] 🟠 El panel de escritorio apunta a la URL correcta mediante `API_BASE_URL`; no hay IPs de desarrollo en el código.
- [ ] 🟡 Se añaden cabeceras de seguridad: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy`.
- [ ] 🟡 Tailwind por CDN se reemplaza por un build local para evitar dependencia y CSP laxa.

---

## 6. Dependencias y cadena de suministro

- [ ] 🟠 Las dependencias están fijadas con rangos razonables y se auditan.

```powershell
api\.venv\Scripts\python.exe -m pip install pip-audit
api\.venv\Scripts\python.exe -m pip_audit -r api\requirements.txt
desktop\.venv\Scripts\python.exe -m pip_audit -r desktop\requirements.txt
```

- [ ] 🟠 No hay dependencias abandonadas ni paquetes con nombres sospechosos (typosquatting).
- [ ] 🟡 Los `requirements.txt` se actualizan de forma controlada y probada.
- [ ] 🟡 Se verifica la integridad de los artefactos descargados (hashes o lockfile).

---

## 7. Datos, privacidad y registros

- [ ] 🔴 No hay datos reales de pacientes en el repositorio, issues, capturas ni mensajes de commit.
- [ ] 🔴 Las capturas de `docs/screenshots/` usan datos sintéticos.
- [ ] 🔴 Los logs no incluyen contraseñas, tokens, cuerpos de request con datos clínicos ni documentos de identidad.
- [ ] 🟠 Los logs tienen retención definida y acceso restringido.
- [ ] 🟠 Existe base legal, consentimiento y aviso de privacidad para el tratamiento de datos.
- [ ] 🟠 Se evaluó el impacto en privacidad (PIA/DPIA) y la normativa local aplicable.
- [ ] 🟡 Los respaldos están cifrados y su restauración fue probada.
- [ ] 🟡 Existe un procedimiento documentado de brecha de seguridad.

---

## 8. Verificación funcional antes del push

- [ ] 🔴 La API arranca sin errores y responde en `/api/ping`.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/ping
```

- [ ] 🔴 El login funciona y devuelve token.
- [ ] 🔴 Los listados principales responden con datos (pacientes, personal, inventario, tratamientos, control diario).
- [ ] 🔴 El panel de escritorio abre y carga las tablas.
- [ ] 🔴 La app móvil abre en `http://127.0.0.1:8000/app/`, permite login y navegación.
- [ ] 🔴 La importación demo conserva acentos y `ñ` (`Martínez`, `Ríos`, `González`).
- [ ] 🟠 La importación demo es idempotente: ejecutarla dos veces no duplica registros.
- [ ] 🟡 Se probó el flujo completo: login → paciente → signos vitales → administración con descuento de stock.

---

## 9. Comandos finales antes de `git push`

Ejecuta en orden y revisa la salida de cada uno.

```powershell
# 1. Qué se va a subir exactamente
git status
git diff --cached --stat
git diff --cached

# 2. Lista completa de archivos rastreados
git ls-files

# 3. Confirmar que los secretos están ignorados
git check-ignore -v api/.env api/.venv desktop/.venv

# 4. Buscar patrones de secretos en el índice
git grep --cached -n -I -E "(admin123|SEED_[A-Z_]*PASSWORD\s*=\s*\S+|DB_PASSWORD\s*=\s*\S+|BEGIN .*PRIVATE KEY)"

# 5. Revisar tamaño y tipo de archivos (evitar binarios y dumps)
git ls-files -s | ForEach-Object { $_ }

# 6. Verificar que no hay archivos mayores a 5 MB
git ls-files | ForEach-Object {
  if (Test-Path $_) {
    $f = Get-Item $_
    if ($f.Length -gt 5MB) { "{0}  {1:N2} MB" -f $f.FullName, ($f.Length / 1MB) }
  }
}
```

- [ ] 🔴 La salida de `git ls-files` no incluye `.env`, `.venv`, `__pycache__`, `*.log`, `*.sql.gz`, capturas con datos reales ni binarios de build.
- [ ] 🔴 El commit no mezcla artefactos generados con código fuente.
- [ ] 🟠 El remoto es el correcto y el repositorio es privado si aún no está listo para publicación.

```powershell
git remote -v
```

---

## 10. Deuda técnica conocida (no bloquea demo, sí producción)

| # | Laguna | Riesgo | Estado | Mitigación mínima |
| --- | --- | --- | --- | --- |
| 1 | Sin RBAC granular por rol | Alto | **Resuelto** | `rol_permisos` + `require_permiso()` |
| 2 | Sin logout ni revocación en servidor | Alto | Abierto | `DELETE FROM sesiones WHERE token_hash = ?` |
| 3 | Sin rate limiting en login | Alto | Abierto | Middleware por IP + backoff |
| 4 | `CORS_ORIGINS=*` por defecto | Medio | Abierto | Fijar orígenes reales |
| 5 | Usuarios con contraseña conocida en `schema.sql` | Alto | **Resuelto** | Seeder con claves aleatorias |
| 6 | HTTP sin TLS | Alto | Abierto | Reverse proxy con HTTPS |
| 7 | Sin auditoría genérica de cambios | Medio | Abierto | Tabla `auditoria` con usuario, acción, entidad |
| 8 | Sin respaldos automáticos | Alto | Abierto | Job programado + restauración probada |
| 9 | Sin CI ni pruebas automatizadas | Medio | Abierto | GitHub Actions + pytest/Playwright |
| 10 | Tailwind por CDN | Bajo | Aceptado | Build local |
| 11 | Token en `localStorage` | Medio | Aceptado en LAN | Cookies `HttpOnly` + CSRF |
| 12 | Descuento de inventario por presentación | Medio | Documentado | Conversión de dosis a unidades |
| 13 | Seed JSON contiene hashes de usuarios | Medio | Mitigado | `.gitignore` + permisos de archivo |
| 14 | Sin permisos de escritura de pacientes | Bajo | Abierto | Añadir `pacientes:escribir` al catálogo |

---

## 11. Criterio de no-go

**No hagas `git push` ni despliegues si se cumple cualquiera de estas condiciones:**

- Hay un secreto real en el índice o en el historial.
- Hay datos reales de pacientes en cualquier archivo.
- `CORS_ORIGINS=*` en un entorno accesible fuera de tu equipo.
- Una contraseña del seeder circula por chat/correo o no se rotó tras la puesta en marcha.
- `database/seeds/initial_data.json` está rastreado por Git.
- El login, los listados o el registro de administración fallan.
- No puedes restaurar un respaldo.

---

## 12. Registro de verificación

| Fecha | Verificador | Commit / rama | Resultado | Notas |
| --- | --- | --- | --- | --- |
| | | | | |

> Guarda este registro en el ticket de release. Un checklist sin evidencia es solo una intención.
