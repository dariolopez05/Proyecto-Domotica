# Script para ejecutar análisis del master query CSV
# Uso: .\analysis_master_query.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Análisis de Master Query" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Obtener ruta del script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

Write-Host "Ejecutando análisis..." -ForegroundColor Yellow

# Ejecutar script Python
python "$scriptDir\analysis_master_query.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Green
    Write-Host "✓ Análisis completado exitosamente" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Los archivos se encuentran en:" -ForegroundColor Yellow
    Write-Host "  $projectRoot\reports\master_query_analysis\" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Red
    Write-Host "✗ Error durante el análisis" -ForegroundColor Red
    Write-Host "======================================" -ForegroundColor Red
}

