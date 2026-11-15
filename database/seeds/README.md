# Seeds

Esta carpeta almacena exportaciones locales de `scripts/seed_system.py`.

```powershell
api\.venv\Scripts\python.exe scripts\seed_system.py --export-seed
api\.venv\Scripts\python.exe scripts\seed_system.py --import-seed database\seeds\initial_data.json
```

## Contenido

- `initial_data.json`: roles, permisos, usuarios con `password_hash` PBKDF2, catálogo de medicamentos, lotes y pacientes demo anonimizados.
- `.gitkeep`: conserva la carpeta en el repositorio.

## Importante

- Los `*.json` están **ignorados por Git** (`.gitignore`): contienen hashes de credenciales y datos clínicos.
- No los compartas por chat, correo ni issues.
- La importación es idempotente: no duplica medicamentos, lotes ni pacientes.
- Los pacientes exportados solo incluyen documentos `PAC-*` o `DEMO-*`, con nombre y contacto anonimizados.
- Si el archivo se filtra, rota las contraseñas con:

```powershell
api\.venv\Scripts\python.exe scripts\seed_system.py --apply --reset-passwords
```
