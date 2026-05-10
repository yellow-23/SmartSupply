# SmartSupply — Contexto del Proyecto

## Que es esto

Tesis de Ingenieria Civil en Informatica, UNAB. 3 integrantes.
Plataforma de prediccion de demanda y reabastecimiento automatico para distribuidoras chilenas.

**Hipotesis**: seleccionar automaticamente el mejor modelo de forecasting por SKU (AMS) reduce el MAPE y el capital inmovilizado vs. usar un modelo unico para todos los productos.

## Roles por integrante

| Integrante | Modulo | Responsabilidad |
|------------|--------|-----------------|
| Int. 1 | `forecasting/` | ARIMA, Prophet, XGBoost, LSTM, AMS (selector automatico) |
| Int. 2 | `inventory/` | EOQ, politica (s,S), generador de ordenes, simulador |
| Int. 3 (Cristobal) | `backend/`, `etl/`, `frontend/` | API REST, ETL, Dashboard |

## Dataset

**Store Sales — Corporacion Favorita** (Kaggle), ya descargado en `datasets/raw/`.

| Archivo | Descripcion |
|---------|-------------|
| `train.csv` | 3,000,888 filas. Columnas: `id, date, store_nbr, family, sales, onpromotion` |
| `stores.csv` | 54 tiendas con ciudad, estado, tipo y cluster |
| `oil.csv` | Precio del petroleo diario (Ecuador) |
| `holidays_events.csv` | Feriados y eventos nacionales/regionales |
| `transactions.csv` | Transacciones diarias por tienda |

Rango temporal: 2013-01-01 a 2017-08-15. 54 tiendas, 33 familias de productos.

## Estructura del repo

```
SmartSupply/
├── backend/app/
│   ├── main.py              # FastAPI + CORS + 4 routers registrados
│   ├── models/schemas.py    # Todos los Pydantic models
│   ├── api/                 # forecast.py, inventory.py, products.py, orders.py
│   └── services/            # forecast_service.py, inventory_service.py
├── etl/scripts/
│   ├── 01_download_kaggle.py  # Descomprime el zip (ya hecho)
│   ├── 02_clean.py            # Limpieza y feature engineering — PENDIENTE implementar
│   └── 03_load_supabase.py    # Carga a PostgreSQL — PENDIENTE implementar
├── forecasting/src/         # arima, prophet, xgboost, lstm + selector.py (esqueletos)
├── inventory/src/           # eoq, s_s_policy, order_generator, simulator (esqueletos)
├── frontend/                # React + Vite + Recharts + Axios (sin implementar aun)
└── datasets/raw/            # CSVs del dataset (en .gitignore)
```

## Stack tecnologico

- **Backend**: FastAPI 0.111, Pydantic v2, SQLAlchemy 2.0, uvicorn
- **Base de datos**: PostgreSQL via Supabase
- **ETL**: pandas, psycopg2-binary / SQLAlchemy
- **Forecasting**: statsmodels (ARIMA), prophet, xgboost, torch (LSTM)
- **Frontend**: React + Vite + Recharts + Axios
- **Variables de entorno**: `backend/.env` (no commitear, basarse en `.env.example`)

## Variables de entorno necesarias

```
DATABASE_URL=postgresql://user:password@host:5432/smartsupply
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=anon-key
```

## Schema de base de datos (objetivo)

Tablas principales que el ETL debe crear y poblar:

- **`sales_history`**: `(id, date, store_nbr, family, sales, onpromotion)` — fuente de verdad para forecasting
- **`stores`**: `(store_nbr, city, state, type, cluster)`
- **`oil_prices`**: `(date, dcoilwtico)` — precio del crudo, feature exogena
- **`holidays`**: `(date, type, locale, locale_name, description, transferred)`
- **`products`**: tabla de SKUs del sistema (definida en schemas.py)
- **`orders`**: ordenes de compra generadas por el sistema

## Convenciones de ramas y commits

Ramas: `feat/`, `fix/`, `docs/`, `exp/`
Commits: Conventional Commits — `feat: ...`, `fix: ...`, `docs: ...`, `chore: ...`

## Estado actual y proximos pasos

### Completado
- [x] Estructura de carpetas y archivos base
- [x] Backend FastAPI con routers y schemas completos
- [x] Esqueletos de forecasting e inventario para los otros integrantes
- [x] Dataset descargado y descomprimido

### En progreso / pendiente
- [ ] **ETL `02_clean.py`**: implementar limpieza real del dataset
- [ ] **ETL `03_load_supabase.py`**: implementar carga a PostgreSQL con SQLAlchemy
- [ ] Crear tablas en Supabase (migraciones SQL)
- [ ] Conectar backend a la BD real (endpoints devuelven datos reales)
- [ ] Dashboard React
- [ ] Int. 1: implementar modelos de forecasting
- [ ] Int. 2: implementar logica de inventario

## Como correr el backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # completar credenciales
uvicorn app.main:app --reload
# -> http://localhost:8000/docs
```

## Como correr el ETL

```bash
cd etl/scripts
python 02_clean.py      # genera forecasting/data/train_clean.csv
python 03_load_supabase.py  # carga a Supabase
```
