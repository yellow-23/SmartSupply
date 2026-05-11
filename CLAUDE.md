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
| Int. 3 (Cristobal) | `backend/`, `etl/`, `frontend/` | API REST, ETL, Dashboard, Ingesta IA |

## Vision de ingesta IA (parte de la tesis)

Una distributiodra chilena real no tiene datos estructurados. El sistema debe aceptar cualquier formato:
- Fotos de cuadernos, pizarras, tickets
- Excel o CSV desordenados
- PDFs escaneados o reportes

**Flujo**:
1. Usuario sube archivo via dashboard → `POST /api/ingest/preview`
2. Backend envia a Claude (vision/docs) con prompt de extraccion
3. Claude devuelve JSON normalizado con fechas, familias y ventas
4. Usuario revisa preview y confirma → `POST /api/ingest/confirm`
5. Backend hace upsert a `sales_history`
6. El pipeline de forecasting e inventario corre sobre esos datos

Modelo Claude usado: `claude-opus-4-7` para imagenes y PDFs, `claude-sonnet-4-6` para Excel con columnas ambiguas.

## Dataset de desarrollo

**Store Sales — Corporacion Favorita** (Kaggle), ya descargado en `datasets/raw/`.
Usado como dataset de benchmarking para validar la hipotesis AMS.
No reemplaza la ingesta IA — son complementarios.

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
│   ├── main.py              # FastAPI + CORS + 6 routers registrados
│   ├── database.py          # SQLAlchemy engine + sesion + get_db
│   ├── models/
│   │   ├── schemas.py       # Todos los Pydantic models
│   │   └── orm.py           # SQLAlchemy ORM (SalesHistory, Store, OilPrice, Holiday)
│   ├── api/
│   │   ├── forecast.py      # Prediccion de demanda
│   │   ├── inventory.py     # Estado e inventario
│   │   ├── products.py      # SKUs
│   │   ├── orders.py        # Ordenes de compra
│   │   ├── sales.py         # Datos historicos reales desde Supabase
│   │   └── ingest.py        # Ingesta IA — sube archivo, Claude extrae, carga a BD
│   └── services/
│       ├── forecast_service.py   # Mock hasta que Int.1 implemente modelos
│       ├── inventory_service.py  # Mock hasta que Int.2 implemente logica
│       └── ingest_service.py     # Claude API — extrae datos de cualquier archivo
├── etl/scripts/
│   ├── 01_download_kaggle.py  # Descomprime el zip (hecho)
│   ├── 02_clean.py            # Limpieza y feature engineering (hecho)
│   └── 03_load_supabase.py    # Carga a Supabase via REST (hecho)
├── forecasting/src/         # arima, prophet, xgboost, lstm + selector.py (esqueletos)
├── inventory/src/           # eoq, s_s_policy, order_generator, simulator (esqueletos)
├── frontend/                # React + Vite + Recharts + Axios (pendiente)
└── datasets/raw/            # CSVs del dataset (en .gitignore)
```

## Stack tecnologico

- **Backend**: FastAPI 0.111, Pydantic v2, SQLAlchemy 2.0, uvicorn
- **Base de datos**: PostgreSQL via Supabase (connection pooler puerto 6543)
- **ETL**: pandas, psycopg2-binary, supabase-py
- **Ingesta IA**: anthropic SDK, Claude Opus 4.7 / Sonnet 4.6
- **Forecasting**: statsmodels (ARIMA), prophet, xgboost, torch (LSTM)
- **Frontend**: React + Vite + Recharts + Axios
- **Python**: 3.11 (3.14 no compatible con pydantic-core)
- **Variables de entorno**: `backend/.env` (no commitear, basarse en `.env.example`)

## Variables de entorno necesarias

```
DATABASE_URL=postgresql://...@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=anon-key
ANTHROPIC_API_KEY=sk-ant-...
```

## Schema de base de datos

- **`sales_history`**: `(id, date, store_nbr, family, sales, onpromotion, lag_7, lag_14, rolling_mean_7, day_of_week, month)`
- **`stores`**: `(store_nbr, city, state, type, cluster)`
- **`oil_prices`**: `(date, dcoilwtico)`
- **`holidays`**: `(date, type, locale, locale_name, description, transferred)`

## Estado actual

### Completado
- [x] Estructura de carpetas y archivos base
- [x] Backend FastAPI con 6 routers (forecast, inventory, products, orders, sales, ingest)
- [x] SQLAlchemy conectado a Supabase — endpoints devuelven datos reales
- [x] ETL completo — datos de Corporacion Favorita cargados en Supabase
- [x] Modulo de ingesta IA — Claude extrae datos de imagenes, Excel y PDF

### Pendiente
- [ ] Dashboard React
- [ ] Agregar ANTHROPIC_API_KEY al .env y probar ingesta con archivo real
- [ ] Int. 1: implementar modelos de forecasting
- [ ] Int. 2: implementar logica de inventario

## Como correr el backend

```bash
cd /ruta/SmartSupply
python3.11 -m venv venv --without-pip
source venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python3.11  # solo primera vez
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload
# -> http://localhost:8000/docs
```
