#!/bin/bash
# SmartSupply — Setup del entorno de desarrollo
# Uso: bash setup.sh

set -e

echo "==> Verificando python3.11..."
if ! command -v python3.11 &>/dev/null; then
  echo "ERROR: python3.11 no encontrado."
  echo "Instalar con: brew install python@3.11"
  exit 1
fi
echo "    OK: $(python3.11 --version)"

echo "==> Creando entorno virtual con python3.11..."
python3.11 -m venv venv
echo "    OK: venv creado"

echo "==> Activando venv..."
source venv/bin/activate

echo "==> Instalando dependencias del backend..."
pip install --upgrade pip -q
pip install -r backend/requirements.txt

echo "==> Instalando dependencias del frontend..."
cd frontend && npm install && cd ..

echo ""
echo "Setup completo. Para trabajar:"
echo ""
echo "  # Backend"
echo "  source venv/bin/activate"
echo "  cd backend && uvicorn app.main:app --reload"
echo ""
echo "  # Frontend (otra terminal)"
echo "  cd frontend && npm run dev"
echo ""
echo "  # Copiar y completar variables de entorno:"
echo "  cp backend/.env.example backend/.env"
