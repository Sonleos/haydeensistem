## Qué cambia

Describe el cambio en 2–5 líneas.

## Por qué

Explica el problema, el issue relacionado y el impacto esperado.

Closes #<ticket>

## Tipo de cambio

- [ ] `feat` Nueva funcionalidad
- [ ] `fix` Corrección de error
- [ ] `security` Endurecimiento o parche
- [ ] `db` Esquema o migración
- [ ] `docs` Documentación
- [ ] `refactor` / `perf` / `test` / `chore`

## Cómo probar

1. ...
2. ...
3. ...

## Evidencia

- Capturas de escritorio/móvil si aplica (datos sintéticos).
- Respuestas de API o logs relevantes (sin datos sensibles).

## Checklist

- [ ] La rama está actualizada con `dev`.
- [ ] `api\.venv\Scripts\python.exe scripts\test_sistema.py` termina en verde.
- [ ] Probé la API localmente con `iniciar_api.bat`.
- [ ] Probé el panel de escritorio si cambié UI.
- [ ] Probé la app móvil si cambié UI.
- [ ] Probé la matriz de permisos si cambié roles o endpoints.
- [ ] No incluí `.env`, secretos, seeds JSON ni datos reales.
- [ ] Actualicé README/docs si cambió el comportamiento.
- [ ] Si toqué SQL, incluí migración idempotente y plan de reversa.
- [ ] Los commits siguen Conventional Commits y están firmados con `-s`.

## Impacto en seguridad

- [ ] No aplica.
- [ ] Requiere dos revisores (auth, permisos, SQL, inventario).
- [ ] Requiere rotación de credenciales o sesiones.

Describe cualquier riesgo residual:
