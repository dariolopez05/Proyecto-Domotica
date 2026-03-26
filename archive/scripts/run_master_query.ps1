# Script para ejecutar master_query.sql y guardar en CSV
# Uso: .\run_master_query.ps1 -Host localhost -Port 5432 -Database homeassistant -User postgres -Password ""

param(
    [string]$Host = "localhost",
    [string]$Port = "5432",
    [string]$Database = "homeassistant",
    [string]$User = "postgres",
    [string]$Password = ""
)

# Configurar variables de entorno
$env:DB_HOST = $Host
$env:DB_PORT = $Port
$env:DB_NAME = $Database
$env:DB_USER = $User
$env:DB_PASSWORD = $Password

# Obtener ruta del script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Ejecutando Master Query" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuración de conexión:" -ForegroundColor Yellow
Write-Host "  Host: $Host"
Write-Host "  Port: $Port"
Write-Host "  Database: $Database"
Write-Host "  User: $User"
Write-Host ""

# Ejecutar script Python
python "$scriptDir\run_master_query.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Green
    Write-Host "✓ Proceso completado exitosamente" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "El CSV se encuentra en:" -ForegroundColor Yellow
    Write-Host "  $projectRoot\data\gold\master_query_result.csv" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Red
    Write-Host "✗ Error durante la ejecución" -ForegroundColor Red
    Write-Host "======================================" -ForegroundColor Red
}

