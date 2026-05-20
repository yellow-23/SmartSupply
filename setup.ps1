# SmartSupply — Setup del entorno de desarrollo (Windows)
# Uso: .\setup.ps1

$ErrorActionPreference = "Stop"

Write-Host "==> Verificando python3.11..."
try {
    $version = & py -3.11 --version 2>&1
    Write-Host "    OK: $version"
} catch {
    Write-Host "ERROR: python3.11 no encontrado."
    Write-Host "Instalar con: winget install Python.Python.3.11"
    exit 1
}

Write-Host "==> Creando entorno virtual con python3.11..."
py -3.11 -m venv venv
Write-Host "    OK: venv creado"

Write-Host "==> Instalando dependencias del backend..."
& .\venv\Scripts\pip install --upgrade pip -q
& .\venv\Scripts\pip install -r backend\requirements.txt

Write-Host "==> Instalando dependencias del frontend..."
Set-Location frontend
npm install
Set-Location ..

if (-not (Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host ""
    Write-Host "IMPORTANTE: Edita backend\.env con tus credenciales reales antes de iniciar el servidor."
}

Write-Host ""
Write-Host "Setup completo. Para trabajar:"
Write-Host ""
Write-Host "  # Backend (PowerShell)"
Write-Host "  .\venv\Scripts\activate"
Write-Host "  cd backend; python -m uvicorn app.main:app --reload"
Write-Host ""
Write-Host "  # Frontend (otra terminal)"
Write-Host "  cd frontend; npm run dev"
