param(
    [string]$BindHost = "",
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root "api\.venv\Scripts\python.exe"
$envFile = Join-Path $root "api\.env"

if (-not (Test-Path $python)) {
    throw "No se encontró el entorno virtual en api\.venv. Crea el entorno e instala api\requirements.txt."
}

# Carga api/.env sin sobrescribir variables ya definidas en el proceso.
if (Test-Path $envFile) {
    Get-Content $envFile -Encoding UTF8 | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $name = $Matches[1]
            $value = $Matches[2].Trim()
            if (-not [Environment]::GetEnvironmentVariable($name)) {
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
}

if (-not $BindHost) {
    $BindHost = if ($env:API_HOST) { $env:API_HOST } else { "0.0.0.0" }
}
if ($Port -le 0) {
    $Port = if ($env:API_PORT) { [int]$env:API_PORT } else { 8000 }
}

Write-Host "API Haydeén en http://${BindHost}:$Port" -ForegroundColor Green
Write-Host "Documentación: http://127.0.0.1:$Port/docs" -ForegroundColor Green
Write-Host "App móvil:    http://127.0.0.1:$Port/app/" -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener." -ForegroundColor Yellow

Push-Location (Join-Path $root "api")
try {
    & $python -m uvicorn main:app --host $BindHost --port $Port
}
finally {
    Pop-Location
}
