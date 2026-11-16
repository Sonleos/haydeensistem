@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PY=api\.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo [ERROR] No existe api\.venv.
    echo.
    echo Crea el entorno una sola vez con:
    echo   python -m venv api\.venv
    echo   api\.venv\Scripts\python.exe -m pip install -r api\requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "api\.env" (
    echo [ERROR] No existe api\.env.
    echo Ejecuta primero:
    echo   api\.venv\Scripts\python.exe scripts\init_db.py
    echo.
    pause
    exit /b 1
)

"%PY%" scripts\run_api.py
if errorlevel 1 pause
endlocal
