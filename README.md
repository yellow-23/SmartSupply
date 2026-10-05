# SmartSupply

Tesis de Ingeniería Civil en Informática — Universidad Andrés Bello, 2025-2026.

Plataforma de predicción de demanda y reabastecimiento automático para distribuidoras chilenas. Entrena varios modelos de forecasting por SKU (ARIMA, Prophet, XGBoost, LSTM), selecciona automáticamente el mejor por producto (AMS) y calcula políticas de reabastecimiento (EOQ y (s, S)).

**Hipótesis:** la asignación automática de modelo por SKU (AMS) empata la precisión del mejor estimador individual y reduce el riesgo de aplicar un modelo subóptimo a todo el catálogo, frente a usar un único modelo fijo para todos los productos.

---

## Estructura del repositorio

```
SmartSupply/
├── backend/            # API REST (FastAPI) + servicios de negocio
│   └── app/
│       ├── api/        # Routers: auth, forecast, inventory, orders, ingest, stocky, admin, notify...
│       ├── models/     # Schemas Pydantic + ORM
│       └── services/   # Lógica: forecast, inventario, ingesta IA, Stocky, notificaciones
│
├── forecasting/        # Modelos de predicción (ARIMA, Prophet, XGBoost, LSTM) + selector AMS
│   ├── data/           # Dataset Kaggle (no se sube al repo)
│   └── src/
│
├── inventory/          # EOQ, política (s, S), generador de órdenes, simulador
│   └── src/
│
├── etl/                # Descarga → limpieza → carga a Supabase del dataset de benchmarking
│   └── scripts/
│
├── frontend/           # Dashboard (React + Vite)
│   └── src/
│
└── docs/               # Documento de tesis y diagramas
```

---

## Integrantes

| Integrante | Módulo | Responsabilidad |
|---|---|---|
| Ignacio Duarte | `forecasting/` | ARIMA, Prophet, XGBoost, LSTM, AMS |
| Matias Muñoz | `inventory/` | EOQ, política (s, S), simulador |
| Cristobal Flores | `backend/`, `etl/`, `frontend/` | API, ETL, dashboard, ingesta IA |

---

## Setup

Requisitos: Python 3.11, Node 18+, cuenta Supabase, Git.

### Backend

```bash
cd backend
python -m venv venv        # o usar el venv de la raíz del repo
venv\Scripts\activate       # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

Creá `backend/.env` con:

```
DATABASE_URL=postgresql://...@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=anon-key
ANTHROPIC_API_KEY=sk-ant-...
CRON_SECRET=cualquier-string   # solo hace falta si vas a probar /api/notify
```

```bash
uvicorn app.main:app --reload
```

API en `http://localhost:8000`, docs en `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Necesita `VITE_API_URL`, `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY` (mismos valores de Supabase que el backend).

### Forecasting / Inventory

```bash
cd forecasting  # o inventory
pip install -r requirements.txt
```

### ETL (cargar el dataset de benchmarking)

```bash
cd etl
python scripts/01_download_kaggle.py
python scripts/02_clean.py
python scripts/03_load_supabase.py
```

---

## Dataset de benchmarking

**Store Sales — Corporación Favorita** (Kaggle): 3.000.888 filas, 54 tiendas, 33 familias de productos, 2013-01-01 a 2017-08-15. Se usa para validar la hipótesis del AMS. No reemplaza la ingesta IA — son complementarios: cualquier negocio real carga sus propios datos vía imagen/Excel/PDF.

---

## Stack

| Capa | Tecnología |
|---|---|
| Forecasting | Python, statsmodels (ARIMA), Prophet, XGBoost, PyTorch (LSTM) |
| Inventario | Python, NumPy, SciPy |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Auth | Supabase Auth (email/password + Google OAuth) |
| Base de datos | PostgreSQL (Supabase) |
| Ingesta IA | Claude (Anthropic) — visión, Excel, agente Stocky |
| Frontend | React, Vite, Recharts, TanStack Query, Zustand |
| Deploy | Render (backend) + Cloudflare Pages (frontend) |

---

## Ramas y commits

Ver [`CONVENTIONS.md`](./CONVENTIONS.md).

```
main      → estable
feat/xxx  → funcionalidad nueva
fix/xxx   → corrección de bug
docs/xxx  → solo documentación
```
