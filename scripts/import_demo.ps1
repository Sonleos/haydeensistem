param(
    [switch]$SchemaOnly,
    [switch]$DemoOnly,
    [switch]$SkipSeed,
    [string]$DbHost = "127.0.0.1",
    [int]$DbPort = 3306,
    [string]$DbUser = "root",
    [string]$DbPassword = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

function Resolve-MySqlClient {
    if ($env:MYSQL_EXE -and (Test-Path $env:MYSQL_EXE)) {
        return $env:MYSQL_EXE
    }

    $laragonRoot = "C:\laragon\bin\mysql"
    if (Test-Path $laragonRoot) {
        $candidate = Get-ChildItem -Path $laragonRoot -Recurse -Filter mysql.exe -File -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($candidate) {
            return $candidate.FullName
        }
    }

    $command = Get-Command mysql.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    throw "No se encontró mysql.exe. Define la variable MYSQL_EXE o agrega MySQL al PATH."
}

$mysql = Resolve-MySqlClient
$mysqlArgs = @("-h", $DbHost, "-P", "$DbPort", "-u", $DbUser, "--default-character-set=utf8mb4")
if ($DbPassword) {
    $mysqlArgs += "-p$DbPassword"
}
$mysqlArgsLine = ($mysqlArgs | ForEach-Object {
    if ($_ -match '\s') { '"' + $_ + '"' } else { $_ }
}) -join " "

function Import-SqlFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "No existe el archivo SQL: $Path"
    }

    Write-Host "Importando $Path ..." -ForegroundColor Cyan

    # La redirección con cmd conserva los bytes UTF-8 del archivo.
    # No usar Get-Content | mysql.exe porque la tubería de PowerShell
    # convierte los acentos a '?' según la página de códigos de la consola.
    cmd /c "`"$mysql`" $mysqlArgsLine < `"$Path`""

    if ($LASTEXITCODE -ne 0) {
        throw "MySQL devolvió el código $LASTEXITCODE al importar $Path"
    }
}

if (-not $DemoOnly) {
    Write-Host "ATENCIÓN: schema.sql elimina y recrea todas las tablas." -ForegroundColor Yellow
    Import-SqlFile (Join-Path $root "database\schema.sql")
}

if (-not $SchemaOnly) {
    Import-SqlFile (Join-Path $root "database\demo_data.sql")
}

if (-not $SkipSeed) {
    $python = Join-Path $root "api\.venv\Scripts\python.exe"
    if (Test-Path $python) {
        Write-Host ""
        Write-Host "Creando roles, permisos y usuarios base..." -ForegroundColor Cyan
        & $python (Join-Path $root "scripts\seed_system.py") --apply
        if ($LASTEXITCODE -ne 0) {
            throw "El seeder falló con código $LASTEXITCODE."
        }
    }
    else {
        Write-Warning "No se encontró api\.venv. Ejecuta manualmente: python scripts\seed_system.py --apply"
    }
}

Write-Host ""
Write-Host "Importación completada. Usa las credenciales mostradas por el seeder." -ForegroundColor Green
