# SmartSupply â€” Contexto del Proyecto

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
1. Usuario sube archivo via dashboard â†’ `POST /api/ingest/preview`
2. Backend envia a Claude (vision/docs) con prompt de extraccion
3. Claude devuelve JSON normalizado con fechas, familias y ventas
4. Usuario revisa preview y confirma â†’ `POST /api/ingest/confirm`
5. Backend hace upsert a `sales_history`
6. El pipeline de forecasting e inventario corre sobre esos datos

Modelo Claude usado: `claude-opus-4-7` para imagenes y PDFs, `claude-sonnet-4-6` para Excel con columnas ambiguas.

## Dataset de desarrollo

**Store Sales â€” Corporacion Favorita** (Kaggle), ya descargado en `datasets/raw/`.
Usado como dataset de benchmarking para validar la hipotesis AMS.
No reemplaza la ingesta IA â€” son complementarios.

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
â”œâ”€â”€ backend/app/
â”‚   â”œâ”€â”€ main.py              # FastAPI + CORS + 6 routers registrados
â”‚   â”œâ”€â”€ database.py          # SQLAlchemy engine + sesion + get_db
â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ schemas.py       # Todos los Pydantic models
â”‚   â”‚   â””â”€â”€ orm.py           # SQLAlchemy ORM (SalesHistory, Store, OilPrice, Holiday)
â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ forecast.py      # Prediccion de demanda
â”‚   â”‚   â”œâ”€â”€ inventory.py     # Estado e inventario
â”‚   â”‚   â”œâ”€â”€ products.py      # SKUs
â”‚   â”‚   â”œâ”€â”€ orders.py        # Ordenes de compra
â”‚   â”‚   â”œâ”€â”€ sales.py         # Datos historicos reales desde Supabase
â”‚   â”‚   â””â”€â”€ ingest.py        # Ingesta IA â€” sube archivo, Claude extrae, carga a BD
â”‚   â””â”€â”€ services/
â”‚       â”œâ”€â”€ forecast_service.py   # Mock hasta que Int.1 implemente modelos
â”‚       â”œâ”€â”€ inventory_service.py  # Mock hasta que Int.2 implemente logica
â”‚       â””â”€â”€ ingest_service.py     # Claude API â€” extrae datos de cualquier archivo
â”œâ”€â”€ etl/scripts/
â”‚   â”œâ”€â”€ 01_download_kaggle.py  # Descomprime el zip (hecho)
â”‚   â”œâ”€â”€ 02_clean.py            # Limpieza y feature engineering (hecho)
â”‚   â””â”€â”€ 03_load_supabase.py    # Carga a Supabase via REST (hecho)
â”œâ”€â”€ forecasting/src/         # arima, prophet, xgboost, lstm + selector.py (esqueletos)
â”œâ”€â”€ inventory/src/           # eoq, s_s_policy, order_generator, simulator (esqueletos)
â”œâ”€â”€ frontend/                # React + Vite + Recharts + Axios (pendiente)
â””â”€â”€ datasets/raw/            # CSVs del dataset (en .gitignore)
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
- [x] SQLAlchemy conectado a Supabase â€” endpoints devuelven datos reales
- [x] ETL completo â€” datos de Corporacion Favorita cargados en Supabase
- [x] Modulo de ingesta IA â€” Claude extrae datos de imagenes, Excel y PDF

### Completado
- [x] Dashboard React (Sprints 1-6 completados: UI/UX completa con Tailwind)
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


