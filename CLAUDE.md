# SmartSupply - Contexto del Proyecto

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

Una distribuidora chilena real no tiene datos estructurados. El sistema debe aceptar cualquier formato:
- Fotos de cuadernos, pizarras, tickets
- Excel o CSV desordenados
- PDFs escaneados o reportes

**Flujo**:
1. Usuario sube archivo via dashboard -> `POST /api/ingest/preview`
2. Backend envia a Claude (vision/docs) con prompt de extraccion
3. Claude devuelve JSON normalizado con fechas, familias y ventas
4. Usuario revisa preview y confirma -> `POST /api/ingest/confirm`
5. Backend hace upsert a `sales_history`
6. El pipeline de forecasting e inventario corre sobre esos datos

Modelo Claude usado: `claude-opus-4-7` para imagenes y PDFs, `claude-sonnet-4-6` para Excel con columnas ambiguas.

## Dataset de desarrollo

**Store Sales - Corporacion Favorita** (Kaggle), ya descargado en `datasets/raw/`.
Usado como dataset de benchmarking para validar la hipotesis AMS.
No reemplaza la ingesta IA - son complementarios.

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
│   ├── main.py              # FastAPI + CORS + 7 routers registrados (incluye auth)
│   ├── database.py          # SQLAlchemy engine + sesion + get_db
│   ├── models/
│   │   ├── schemas.py       # Pydantic models
│   │   └── orm.py           # SQLAlchemy ORM (User, Business, SalesHistory, Store, OilPrice, Holiday)
│   ├── api/
│   │   ├── auth.py          # POST /login, POST /register + get_current_user dependency
│   │   ├── forecast.py      # Prediccion de demanda
│   │   ├── inventory.py     # Estado e inventario
│   │   ├── products.py      # SKUs
│   │   ├── orders.py        # Ordenes de compra
│   │   ├── sales.py         # Datos historicos reales desde Supabase
│   │   └── ingest.py        # Ingesta IA - sube archivo, Claude extrae, carga a BD
│   └── services/
│       ├── forecast_service.py   # Mock hasta que Int.1 implemente modelos
│       ├── inventory_service.py  # Mock hasta que Int.2 implemente logica
│       └── ingest_service.py     # Claude API - extrae datos de cualquier archivo
├── backend/scripts/
│   └── create_user.py       # Crea usuario admin manualmente (usar python3.11)
├── etl/scripts/
│   ├── 01_download_kaggle.py  # Descomprime el zip (hecho)
│   ├── 02_clean.py            # Limpieza y feature engineering (hecho)
│   └── 03_load_supabase.py    # Carga a Supabase via REST (hecho)
├── forecasting/src/         # arima, prophet, xgboost, lstm + selector.py (esqueletos)
├── inventory/src/           # eoq, s_s_policy, order_generator, simulator (esqueletos)
├── frontend/src/
│   ├── api/
│   │   ├── axios.instance.ts  # Axios con interceptor JWT + redirect 401
│   │   └── client.ts          # Re-exporta axios.instance.ts
│   ├── store/
│   │   └── authStore.ts       # Zustand persist - login/logout reales, sin mocks
│   ├── components/layout/
│   │   ├── ProtectedRoute.tsx # Redirect a /login si no autenticado
│   │   ├── Sidebar.tsx        # Muestra nombre y rol del usuario real
│   │   ├── AppShell.tsx
│   │   └── TopBar.tsx
│   └── pages/
│       ├── Login.tsx          # Conectado a POST /api/auth/login
│       ├── Register.tsx       # Conectado a POST /api/auth/register
│       ├── Dashboard.tsx      # UI completa, datos mockeados (pendiente S2-B)
│       ├── Forecast.tsx       # UI completa, datos mockeados (pendiente S3)
│       ├── Inventory.tsx      # UI completa, datos mockeados (pendiente S4)
│       ├── Orders.tsx         # UI completa, datos mockeados (pendiente S4)
│       ├── Products.tsx       # UI completa, datos mockeados (pendiente S2-C)
│       └── Ingest.tsx         # UI completa, sin conectar (pendiente S3)
└── datasets/raw/            # CSVs del dataset (en .gitignore)
```

## Stack tecnologico

- **Backend**: FastAPI 0.111, Pydantic v2, SQLAlchemy 2.0, uvicorn
- **Auth**: JWT con python-jose, bcrypt 5.0.0 (NO usar passlib - incompatible con bcrypt>=4)
- **Base de datos**: PostgreSQL via Supabase (connection pooler puerto 6543)
- **ETL**: pandas, psycopg2-binary, supabase-py
- **Ingesta IA**: anthropic SDK, Claude Opus 4.7 / Sonnet 4.6
- **Forecasting**: statsmodels (ARIMA), prophet, xgboost, torch (LSTM)
- **Frontend**: React + Vite + Recharts + Axios + Zustand + TanStack Query
- **Python**: 3.11 — SIEMPRE usar `python3.11` explicitamente (el venv tiene 3.11 y 3.12, los paquetes estan en 3.11)
- **Variables de entorno**: `backend/.env` (no commitear, basarse en `.env.example`)

## Variables de entorno necesarias

```
DATABASE_URL=postgresql://...@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=anon-key
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=secreto-largo-y-aleatorio
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8
```

## Schema de base de datos

- **`users`**: `(id, name, email, hashed_password, role, business_id, is_active, created_at)` - creada manualmente en Supabase public schema
- **`businesses`**: `(id, name, rut, city, type, created_at)`
- **`sales_history`**: `(id, date, store_nbr, family, sales, onpromotion, lag_7, lag_14, rolling_mean_7, day_of_week, month)`
- **`stores`**: `(store_nbr, city, state, type, cluster)`
- **`oil_prices`**: `(date, dcoilwtico)`
- **`holidays`**: `(date, type, locale, locale_name, description, transferred)`

## Notas importantes de infraestructura

- **Supabase proyecto**: `xqiehkshtedrodhtdkzv` (region sa-east-1). Se pausa automaticamente en tier gratuito por inactividad. Si la DB no conecta, restaurar desde Supabase dashboard o via MCP.
- **Tabla `users`**: fue creada via `execute_sql` en schema `public` (NO via `apply_migration` - ese tool la creo en schema incorrecto).
- **bcrypt**: el venv tiene bcrypt 5.0.0 que rompe passlib 1.7.4. Usar `import bcrypt` directamente en el codigo de auth.

## Como correr el proyecto

```bash
# Backend
cd SmartSupply/backend
source ../venv/bin/activate
python3.11 -m uvicorn app.main:app --reload
# -> http://localhost:8000/docs

# Frontend
cd SmartSupply/frontend
npm run dev
# -> http://localhost:5173
```

## Estado actual (2026-05-18)

### Completado - Sprint 1
- [x] Estructura de carpetas y archivos base
- [x] Backend FastAPI con routers (forecast, inventory, products, orders, sales, ingest, businesses)
- [x] SQLAlchemy conectado a Supabase
- [x] ETL completo - datos de Corporacion Favorita cargados en Supabase
- [x] Modulo de ingesta IA - Claude extrae datos de imagenes, Excel y PDF
- [x] Frontend UI/UX completa con Tailwind (todas las paginas con datos mockeados)

### Completado - Sprint 2-A (2026-05-18)
- [x] `POST /api/auth/login` - JWT real con python-jose + bcrypt
- [x] `POST /api/auth/register` - registro abierto
- [x] `get_current_user` - dependencia reutilizable para proteger endpoints
- [x] Modelo ORM `User` agregado a orm.py
- [x] Tabla `users` creada en Supabase public schema
- [x] Usuario admin creado: `cristobal@distribuidora.cl` / `demo1234`
- [x] `frontend/src/api/axios.instance.ts` - interceptor JWT automatico + redirect 401
- [x] `authStore.ts` - mock eliminado, login/logout llaman a la API real
- [x] `ProtectedRoute.tsx` - redirige a /login si no autenticado
- [x] `Login.tsx` - conectado a API real, spinner y mensaje de error
- [x] `Register.tsx` - pagina nueva con mismo estilo que Login
- [x] Sidebar - "Plan Pro" eliminado, muestra nombre y rol del usuario real

### Pendiente
- [ ] S2-B: GET /dashboard/kpis + conectar Dashboard a datos reales
- [ ] S2-C: CRUD de productos conectado a Supabase
- [ ] S3: AMS batch + Forecast end-to-end + Ingesta IA conectada
- [ ] S4: Inventario + Ordenes + Simulador (s,S)
- [ ] S5: Reportes + Admin + Notificaciones
- [ ] S6: QA + Deploy Render/Cloudflare + Tesis
- [ ] Recuperacion de contrasena por email (diferido - necesita servicio SMTP como Resend)
- [ ] ANTHROPIC_API_KEY en .env para probar ingesta con archivo real
