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

"%PY%" scripts\test_sistema.py %*
set "EXIT_CODE=%ERRORLEVEL%"
echo.
pause
endlocal
exit /b %EXIT_CODE%
