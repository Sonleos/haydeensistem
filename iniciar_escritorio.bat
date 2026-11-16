@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PY=%~dp0desktop\.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo [ERROR] No existe desktop\.venv.
    echo.
    echo Crea el entorno una sola vez con:
    echo   python -m venv desktop\.venv
    echo   desktop\.venv\Scripts\python.exe -m pip install -r desktop\requirements.txt
    echo.
    pause
    exit /b 1
)

pushd desktop
"%PY%" admin_panel.py
set "EXIT_CODE=%ERRORLEVEL%"
popd

if not "%EXIT_CODE%"=="0" pause
endlocal
exit /b %EXIT_CODE%
