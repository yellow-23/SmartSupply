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

Modelo Claude usado: `claude-haiku-4-5-20251001` para imagenes y PDFs, `claude-sonnet-4-6` para Excel con columnas ambiguas.

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
│   ├── main.py              # FastAPI + CORS + 9 routers (auth, forecast, inventory, products, orders, sales, ingest, ingests, businesses, stocky)
│   ├── database.py          # SQLAlchemy engine + sesion + get_db
│   ├── models/
│   │   ├── schemas.py       # Pydantic models
│   │   └── orm.py           # ORM: User, Business, UserBusiness, SalesHistory, Store, IngestLog, Product, StockLevel, PurchaseOrder, ...
│   ├── api/
│   │   ├── auth.py          # POST /login, POST /register, forgot/reset-password + get_current_user
│   │   ├── forecast.py      # Prediccion de demanda (AMS real)
│   │   ├── inventory.py     # GET /alerts, GET /{family}, GET /{family}/metrics
│   │   ├── products.py      # CRUD de productos/SKUs por negocio
│   │   ├── orders.py        # Ordenes de compra + generacion automatica
│   │   ├── sales.py         # Datos historicos reales desde Supabase
│   │   ├── ingest.py        # Ingesta IA: /preview, /confirm, /chat
│   │   ├── ingests.py       # Gestion de cargas: listar, revertir, eliminar
│   │   ├── businesses.py    # Negocios scoped por user_businesses
│   │   └── stocky.py        # POST /stocky/chat - asistente global con herramientas
│   └── services/
│       ├── forecast_service.py   # AMS real: ARIMA/Prophet/XGBoost + last-wins por ingest_id
│       ├── inventory_service.py  # EOQ + politica (s,S) + simulador desde sales_history real
│       ├── ingest_service.py     # Claude API - extrae datos de imagen/Excel/PDF
│       ├── ingest_validator.py   # Validador de calidad antes de cargar
│       └── stocky_service.py     # Loop agentivo Claude Haiku con 5 herramientas de BD
├── backend/scripts/
│   ├── create_user.py            # Crea usuario admin manualmente (usar python3.11)
│   ├── migrate_s3_ingest_log.sql # Migracion S3: ingest_log, sales_history.ingest_id
│   ├── migrate_s4_inventory.sql  # Migracion S4: products, stock_levels, purchase_orders, user_businesses
│   ├── backfill_s3_ingest_log.py # Backfill cargas historicas para businesses existentes
│   └── migrate_s2f.sql           # Migracion S2-F: sales_history.sales_unit
├── etl/scripts/
│   ├── 01_download_kaggle.py  # Descomprime el zip (hecho)
│   ├── 02_clean.py            # Limpieza y feature engineering (hecho)
│   └── 03_load_supabase.py    # Carga a Supabase via REST (hecho)
├── forecasting/src/         # arima, prophet, xgboost (DIRMO), lstm + selector.py (AMS operativo)
├── inventory/src/           # eoq, s_s_policy, order_generator, simulator (operativos)
├── frontend/src/
│   ├── api/
│   │   ├── axios.instance.ts  # Axios con interceptor JWT + redirect 401
│   │   ├── data.ts            # Negocios, ubicaciones, cargas, registros
│   │   ├── forecast.ts        # fetchForecast, fetchSalesHistory
│   │   ├── inventory.ts       # fetchAlerts, fetchInventoryStatus, fetchInventoryMetrics, generateOrders
│   │   ├── ingest.ts          # preview, confirm, chat con tipos QualityIssue
│   │   ├── products.ts        # CRUD productos
│   │   └── stocky.ts          # chatStocky
│   ├── store/
│   │   └── authStore.ts       # Zustand persist - login/logout reales
│   ├── components/
│   │   ├── layout/
│   │   │   ├── ProtectedRoute.tsx
│   │   │   ├── Sidebar.tsx        # queryClient.clear() en logout
│   │   │   └── AppShell.tsx       # Incluye StockyFloat global
│   │   ├── StockyFloat.tsx        # Asistente flotante bottom-right con historial
│   │   └── ui/AlertsSummaryPanel.tsx
│   └── pages/
│       ├── Login.tsx / Register.tsx / ForgotPassword.tsx / ResetPassword.tsx
│       ├── Dashboard.tsx      # KPIs + chart reales, queryKey con user.id
│       ├── Forecast.tsx       # AMS real, labels CLP/uds dinamicos
│       ├── Datos.tsx          # Drill-down negocio->ubicacion->cargas->registros
│       ├── Inventory.tsx      # Alertas reales desde sales_history, politica (s,S)
│       ├── Orders.tsx         # Ordenes reales con cambio de estado
│       ├── Products.tsx       # Selector de negocio dinamico, sin defaults
│       └── Ingest.tsx         # Preview+validacion+selector destino+Stocky
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

- **`users`**: `(id, name, email, hashed_password, role, business_id, is_active, created_at)`
- **`businesses`**: `(id, name, rut, city, type, owner_user_id, created_at)`
- **`user_businesses`**: `(id, user_id, business_id, role)` - many-to-many; role: owner|member. Controla acceso en businesses.py, ingests.py
- **`sales_history`**: `(id, business_id, date, store_nbr, family, sales, onpromotion, sales_unit, ingest_id, ...)`
- **`ingest_log`**: `(id, business_id, store_nbr, user_id, filename, file_type, records_loaded, sales_unit, date_range_start, date_range_end, families JSONB, status active|reverted, created_at)`
- **`products`**: `(id, business_id, store_nbr, family, unit_cost, order_cost, holding_rate, lead_time_days, moq)` - todos opcionales; Stocky los completa
- **`stock_levels`**: `(id, business_id, store_nbr, family, quantity, updated_at)`
- **`purchase_orders`**: `(id, business_id, store_nbr, family, quantity, trigger_stock, reorder_point_s, order_up_to_S, policy_used, status, created_at, expected_delivery, received_at)`
- **`password_reset_tokens`**: `(id, user_id, token, expires_at, used)`
- **`stores`**: `(store_nbr, city, state, type, cluster)`

## Notas importantes de infraestructura

- **Supabase proyecto**: `xqiehkshtedrodhtdkzv` (region sa-east-1). Se pausa automaticamente en tier gratuito por inactividad. Si la DB no conecta, restaurar desde Supabase dashboard o via MCP.
- **Tabla `users`**: fue creada via `execute_sql` en schema `public` (NO via `apply_migration` - ese tool la creo en schema incorrecto).
- **bcrypt**: el venv tiene bcrypt 5.0.0 que rompe passlib 1.7.4. Usar `import bcrypt` directamente en el codigo de auth.

## Como correr el proyecto

### Primera vez (setup)
```bash
# Requiere python3.11 — instalar si no lo tienes:
brew install python@3.11

# Desde la raiz del repo:
bash setup.sh

# Copiar y completar variables de entorno:
cp backend/.env.example backend/.env
# Editar backend/.env con DATABASE_URL, JWT_SECRET, etc.
```

### Dia a dia
```bash
# Backend
source venv/bin/activate
cd backend && uvicorn app.main:app --reload
# -> http://localhost:8000/docs

# Frontend (otra terminal)
cd frontend && npm run dev
# -> http://localhost:5173
```

### Problema comun: "No module named X" con venv activado
Significa que `python`/`pip` apuntan a la version incorrecta dentro del venv. Arreglar con:
```bash
ln -sf python3.11 venv/bin/python
ln -sf python3.11 venv/bin/python3
```
Verificar: `python --version` debe decir `Python 3.11.x`

## Estado actual (2026-05-26)

### Completado - Sprint 4 Inventario + Ordenes + Stocky global (2026-05-26, mergeado a dev)

Rama `feature/s4-inventario-ordenes` mergeada a `dev`. Tambien mergeado `feature/xgboost-direct-forecast` (Int.1: XGBoost DIRMO + tests AMS reales).

**Base de datos (migracion `backend/scripts/migrate_s4_inventory.sql` — aplicar en Supabase):**
- [x] `user_businesses (id, user_id, business_id, role)` - many-to-many; reemplaza modelo owner-unico
- [x] `products (id, business_id, store_nbr, family, unit_cost, order_cost, holding_rate, lead_time_days, moq)` - todos opcionales
- [x] `stock_levels (id, business_id, store_nbr, family, quantity, updated_at)`
- [x] `purchase_orders (id, business_id, store_nbr, family, quantity, ...)` con estados pending/confirmed/in_transit/received/cancelled

**Backend:**
- [x] `GET /api/inventory/alerts?business_id=&store_nbr=` - deriva familias desde `sales_history` (no requiere stock_levels previo); stock=0 si no hay nivel configurado
- [x] `GET /api/inventory/{family}` y `GET /api/inventory/{family}/metrics` - EOQ + (s,S) + simulador reales
- [x] `POST /api/orders/generate` - crea `purchase_orders` para todos los SKUs criticos (stock <= s)
- [x] `PATCH /api/orders/{id}/status` - transiciones de estado con validacion
- [x] `POST /api/stocky/chat` - loop agentivo Claude Haiku con herramientas: `list_products`, `list_stock_levels`, `list_orders`, `update_product`, `update_stock_level`
- [x] `user_businesses` integrado en `auth.py` (register), `businesses.py` (list/create), `ingests.py` (_assert_owner)
- [x] Fix `ingest.py`: `Product()` ya no usa campos obsoletos `sku_id`/`name`; solo `business_id`, `store_nbr`, `family`

**Frontend:**
- [x] `Inventory.tsx` conectado: alertas reales, detalle (s,S,EOQ), metricas 30 dias, boton generar ordenes
- [x] `Orders.tsx` conectado: tabla real con filtros, cambio de estado inline, contador por estado
- [x] `Products.tsx`: selector de negocio dinamico (sin defaults hardcodeados), CRUD completo
- [x] `StockyFloat.tsx`: boton flotante bottom-right, panel de chat 384px, chips de sugerencia, historial de mensajes
- [x] `AppShell.tsx`: incluye `<StockyFloat />` global en todas las paginas
- [x] `Dashboard.tsx`: queryKeys con `user.id` para evitar contaminacion entre usuarios
- [x] `Sidebar.tsx`: `queryClient.clear()` en logout

**Comportamiento clave:**
- Inventario funciona desde el primer dia: sin stock_levels, todas las familias con ventas aparecen como "critico" (stock=0 <= s calculado). Usuario configura stock real via Stocky o manualmente.
- Parametros de producto (unit_cost, lead_time, etc.) todos opcionales con defaults en `inventory_service.py`. Stocky los completa a pedido del usuario.
- Multi-negocio: un usuario puede pertenecer a varios negocios via `user_businesses`. `GET /api/businesses` devuelve solo los del usuario autenticado.

**Verificacion end-to-end (pancho gonzales, business_id=22, 5 familias):**
- Carga Excel 720 filas OK → inventario muestra 5 alertas criticas OK → generar ordenes crea 5 purchase_orders OK → Orders page muestra tabla OK → Stocky global responde con contexto de BD OK

### Completado - Sprint 3 Gestion de datos y cargas (2026-05-24, mergeado a dev 2026-05-25)

Jerarquia nueva: Usuario -> Negocios -> Ubicaciones -> Cargas -> Registros. Spec en
`docs/superpowers/specs/2026-05-24-gestion-datos-cargas-design.md`, plan en
`docs/superpowers/plans/2026-05-24-gestion-datos-cargas.md`. Rama `feature/s3-gestion-datos` mergeada a `dev`.

**Base de datos (migracion aplicada en Supabase):**
- [x] `ingest_log` tabla nueva: una fila por carga (business_id, store_nbr, user_id, filename, file_type, records_loaded, sales_unit, rango fechas, families JSONB, status active|reverted, created_at). Script `backend/scripts/migrate_s3_ingest_log.sql`
- [x] `businesses.owner_user_id` FK -> users: un negocio pertenece a un usuario
- [x] `sales_history.ingest_id` FK -> ingest_log: cada fila sabe de que carga vino
- [x] Constraint unica cambio de `sales_history_unique_record` a `uq_sales_history_load (business_id, store_nbr, date, family, ingest_id)` para permitir cargas separadas por el mismo dia+familia
- [x] Backfill `backend/scripts/backfill_s3_ingest_log.py`: creo una carga sintetica 'carga historica' (file_type='historic') por cada (business_id, store_nbr) existente y seteo owner_user_id. 3 cargas creadas (business 2, 18, 19)

**Cambio de comportamiento clave:**
- [x] El confirm de ingesta YA NO hace UPSERT. Cada carga inserta filas propias con su `ingest_id` sin sobrescribir. El solape entre cargas se resuelve al CONSULTAR (no al cargar)
- [x] `forecast_service._load_series_from_db` une con `ingest_log`, excluye cargas `reverted` y aplica "ultima gana" (mayor ingest_id por fecha). Los datos crudos quedan intactos y auditables

**Backend (endpoints nuevos):**
- [x] `GET /api/businesses` ahora scoped por `owner_user_id` (solo los negocios del usuario). `POST /api/businesses` setea owner. `GET /api/businesses/{id}/stores`
- [x] `backend/app/api/ingests.py`: `GET /api/ingests?business_id=&store_nbr=`, `GET /api/ingests/{id}` (filas de la carga), `POST /api/ingests/{id}/revert` (status='reverted', no borra), `DELETE /api/ingests/{id}` (hard delete carga + filas)
- [x] `IngestConfirm` gana `filename` y `file_type`; el confirm crea el `ingest_log` y tagea las filas
- [x] `PATCH /api/sales/record/{id}` y `DELETE /api/sales/record/{id}` para editar/eliminar filas individuales (con check de owner)

**Frontend:**
- [x] `frontend/src/api/data.ts`: cliente tipado de negocios, ubicaciones, cargas, registros
- [x] `frontend/src/pages/Datos.tsx`: pagina nueva en sidebar. Drill-down negocio -> ubicacion -> tabla de cargas (fecha, archivo, quien subio, filas, rango, unidad, estado). Expandir muestra registros con edicion inline de venta y borrado por fila. Acciones revertir/eliminar por carga. Boton "Preguntar a Stocky" por carga
- [x] Flujo de Ingesta: selector de negocio+ubicacion destino en el paso preview, con "+ Nuevo negocio". Confirmar bloqueado hasta elegir destino

**Stocky ampliado:**
- [x] En el chat de ingesta recibe contexto de cargas previas del negocio (`existing_loads`) para sugerir destino y avisar solapes
- [x] En la pagina Datos resume cualquier carga a pedido

**Consecuencia del modelo owner-unico:** el negocio 2 lo compartian 4 usuarios; ahora su owner es user 1 (`cristobal@distribuidora.cl`). Los users 2/3/4 ya no lo ven en `GET /api/businesses`. Reversible reasignando `owner_user_id`.

**Verificacion end-to-end (contra Supabase real):** login owner-scoped OK, listado de cargas con familias backfilleadas OK, detalle de registros OK, confirm crea carga OK, revert OK, delete (204) + limpieza OK, serie de forecast con JOIN activo OK. Frontend `vite build` limpio.

### Completado - Sprint 2-F Modo monto vs unidades (2026-05-23)

**Backend:**
- [x] `SalesHistory.sales_unit` columna nueva (`VARCHAR(10) DEFAULT 'units'`) en ORM y migración `backend/scripts/migrate_s2f.sql` (aplicar en Supabase)
- [x] `IngestPreview.sales_unit_detected: 'CLP' | 'units' | null` — el servicio lo setea según `LIKELY_CURRENCY`
- [x] `IngestConfirm.sales_unit: 'CLP' | 'units'` — el frontend envía la elección del usuario
- [x] `ingest.py` guarda `sales_unit` en cada fila de `sales_history` al confirmar (insert y update)
- [x] `ForecastResponse.sales_unit: 'CLP' | 'units'` — forecast service lo consulta desde DB
- [x] `forecast_service.py` detecta la unidad de la serie antes de cachear la respuesta

**Frontend:**
- [x] `IngestPreview.sales_unit_detected` en `ingest.ts`
- [x] `confirmIngest` acepta parámetro `sales_unit`
- [x] `Ingest.tsx` — tarjeta de selección "Unidades vendidas / Monto en pesos (CLP)" siempre visible en el paso preview; cuando `LIKELY_CURRENCY` detectado, `salesUnit` queda `null` y el botón Confirmar se bloquea hasta que el usuario elija explícitamente
- [x] `ForecastResponse.sales_unit` en `forecast.ts`
- [x] `Forecast.tsx` — labels dinámicos: `$X CLP` vs `X uds`, formateo chileno con `$` prefix para CLP
- [x] `Inventory.tsx` — banner de aviso para SKUs CLP (EOQ no aplica sin precio unitario); bandera `hasCLPSkus` lista para conectar en S4

### Completado - Sprint 2-E Validador de ingesta + fixes de modelos (2026-05-22, yellow-23)

**Backend - Validador (nuevo):**
- [x] `backend/app/services/ingest_validator.py` - detecta problemas antes de cargar:
  - `FUTURE_DATES` (warning): registros con `date > today`
  - `MIXED_GRANULARITY` (error, bloquea): gaps inconsistentes (ej: mensual + diario mezclados)
  - `MONTHLY_GRANULARITY` (warning): gap mediano >=25 dias
  - `WEEKLY_GRANULARITY` (info): gap mediano 5-25 dias
  - `SCALE_SHIFT` (warning): >5x cambio de mediana entre mitades temporales
  - `LIKELY_CURRENCY` (warning): >=50% de familias con mediana diaria >10k → probable son pesos CLP no unidades
- [x] `QualityIssue` schema (severity/code/family/message) + campo `quality_issues` en `IngestPreview`
- [x] `filter_loadable_records()` - defensa en profundidad: el `/confirm` filtra futuros y `sales=0` aunque el frontend los pase
- [x] Validador se invoca automaticamente en `IngestService._build_preview()` (cubre imagen, excel, PDF)

**Backend - Hardening de ingesta:**
- [x] `_get_column_mapping()` ahora intenta Sonnet primero, fallback automatico a Haiku si Sonnet retorna 529 (overloaded). Mensaje user-facing friendly, traceback completo solo en logs del backend
- [x] `_parse_date()` reescrito: `dayfirst=True` PRIMERO (convencion chilena dd/mm/yyyy), US como fallback. Elimina `infer_datetime_format` deprecated. Bug previo: fechas como `03/05/2026` se parseaban como `mar 5` (US) silenciosamente
- [x] `max_tokens` de column mapping subido de 600 a 1500 (evita truncamiento de JSON con archivos complejos)

**Backend - Fixes de modelos de forecasting:**
- [x] `forecasting/src/prophet_model.py` - `yearly_seasonality` ahora dinamico (activo solo si serie >=730 dias). Bug: con `True` hardcoded sobreajustaba en series cortas. WAPE bajo de 213% a 10.86% sobre datos sinteticos
- [x] `forecasting/src/arima_model.py` - grid search ahora incluye componente estacional semanal `seasonal_order=(P,D,Q,7)` cuando hay >=21 dias. Antes ARIMA predecia linea plana (la media); ahora captura ciclo semanal

**Backend - Forecast Service:**
- [x] `forecast_service._load_series_from_db()` filtra `date <= today` (evita que futuros polucionen el set de validacion del AMS)

**Frontend:**
- [x] `frontend/src/api/ingest.ts` - tipos `QualityIssue` y `IssueSeverity` (`'error' | 'warning' | 'info'`)
- [x] `Ingest.tsx` - panel de quality issues con colores por severidad (rojo/ambar/azul), boton Confirmar se bloquea si hay severidad `error`, Stocky recibe los issues en su contexto

**Base de datos:**
- [x] `UNIQUE (business_id, date, family, store_nbr)` en `sales_history` - previene duplicados en reingestas
- [x] Cleanup de businesses huerfanos (12-16) y reset de business 17 (Distribuidora salame), que tenia 1755 filas con granularidad mixta (mensual ene-oct 2025 + diario nov 2025+ + 30 registros futuros). Causa raiz invisible de WAPE 121% en el SKU CONGELADOS
- [x] Cargado business 18 (Distribuidora Santa Elena - Sucursal Ñuñoa): 1395 filas reales, 9 familias, rango 2025-11-24 → 2026-05-22, todas DIARIAS y consistentes. El validador detecto correctamente que son pesos (LIKELY_CURRENCY) y dejo proceder al usuario

**Validacion end-to-end:**
- [x] Forecast sobre data real ingestada: PANADERIA Y PASTELERIA business 18 → Prophet gana con WAPE 10.68% y detecta cierre dominical (~$3k vs ~$220k entre semana). El AMS funciona sobre data real, no solo sobre el dataset Kaggle

### Completado - Sprint 2-C Dashboard + Auth hardening (2026-05-20, nachytto)
- [x] `GET /api/dashboard/kpis` - SKUs en alerta, ordenes pendientes (MAPE y nivel servicio pendientes de modelos)
- [x] `GET /api/dashboard/chart-data` - ventas reales agregadas por dia, ultimas 4 semanas desde Supabase
- [x] `Dashboard.tsx` conectado a API real via React Query, sin datos mockeados
- [x] `AlertsSummaryPanel.tsx` - panel de alertas criticas de SKU en el dashboard
- [x] `POST /api/auth/forgot-password` - genera token con TTL 30 min, responde siempre 200
- [x] `POST /api/auth/reset-password` - valida token, actualiza hash, marca token como usado (one-time use)
- [x] Rate limiting en `/login` - 5 intentos fallidos por IP en ventana de 15 min, responde 429
- [x] `PasswordResetToken` ORM model + tabla `password_reset_tokens` en Supabase (con RLS activado)
- [x] `ForgotPassword.tsx` + `ResetPassword.tsx` - paginas nuevas con rutas en App.tsx
- [x] `ProtectedRoute.tsx` - soporte para roles
- [x] `require_admin()` dependency lista para proteger endpoints admin
- [x] `setup.ps1` - script de setup para Windows
- [x] Migration script: `backend/scripts/migrate_sprint2.sql` (ya aplicado en Supabase)

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

### Completado - Sprint 2-B Forecasting (2026-05-20)
- [x] Auth centralizado en `main.py` via `dependencies=[Depends(get_current_user)]` - todos los routers protegidos excepto `/api/auth`
- [x] `frontend/src/api/forecast.ts` - modulo con `fetchForecast` y `fetchSalesHistory`
- [x] `Forecast.tsx` conectado a la API real - selector de SKU con 33 familias, input de tienda, horizonte 7/14/30 dias
- [x] Grafico con historial real (ultimos 30 dias) + prediccion (linea continua / punteada)
- [x] Tarjeta modelo ganador con nombre y WAPE real del AMS
- [x] Resumen del pronostico: total estimado, promedio diario, precision del modelo en %
- [x] Estado de carga con spinner y mensaje explicativo (~30-90s por SKU)
- [x] Banner informativo sobre dataset de benchmarking Corporacion Favorita
- [x] Dependencias instaladas en venv: matplotlib, statsmodels, prophet, xgboost, scikit-learn
- [x] LSTM usa tensorflow (no instalado) - falla graciosamente, AMS igual elige entre ARIMA/Prophet/XGBoost

### Notas tecnicas importantes
- **LSTM**: el modelo espera `tensorflow` pero el venv tiene `torch`. Hay que migrar `lstm_model.py` a PyTorch o instalar tensorflow. Por ahora no bloquea - AMS lo descarta y elige el mejor entre los 3 restantes.
- **Latencia forecast**: cada request corre el AMS completo (30-90s). ARIMA ahora corre grid mas grande (144 combinaciones vs 18 anteriores) por la busqueda estacional. Considerar cache.
- **Dataset Kaggle**: business_id=1 se lee del CSV directamente (no esta en DB). business_id=2 (SmartSupply Demo) y business_id=18 (Santa Elena) son data real ingestada.
- **Currency vs units**: el sistema actualmente no distingue. La data de Santa Elena son pesos CLP pero el dashboard etiqueta todo como "uds". El validador avisa con `LIKELY_CURRENCY` pero no bloquea. La hipotesis de la tesis (AMS reduce capital inmovilizado) NO es testeable hasta que se implemente modo monto vs unidades (ver S2-F pendiente).
- **Fallback de modelos Claude**: ingesta intenta Sonnet primero, cae a Haiku en 529. Si ambos fallan, mensaje friendly al usuario y traceback completo en logs del backend.
- **Convencion de fechas**: `_parse_date` asume formato chileno (dd/mm/yyyy) por defecto. Para data de fuentes US habria que invertir el orden de intentos.

### Pendiente

**Proximo (top priority):**
- [ ] S5: Reportes exportables (PDF/Excel), Admin panel, recuperacion contrasena por email real (SMTP/Resend)
- [ ] S6: QA final + merge `dev -> main` + Tesis (deploy Render/Cloudflare ya en produccion desde 2026-08-24)

**Mejoras tecnicas acumuladas:**
- [ ] Tests automatizados de `_parse_date` y `validate_ingest_records` (no existen)
- [x] ~~Dashboard: poblar serie forecast en chart-data~~ RESUELTO 2026-08-24: suma por dia la prediccion cacheada de los SKUs que el usuario corrio en la pagina Forecast (`get_business_cached_forecasts`, TTL 1h del cache existente). Si el usuario aun no corrio ningun forecast, `forecast` sigue en `None` como antes.
- [x] ~~Cache de predicciones por SKU+tienda+horizonte~~ YA EXISTIA (`forecast_service.py`, TTL 1h); RESUELTO bug de invalidacion 2026-08-24 (no se limpiaba al ingestar/revertir/eliminar/editar)
- [x] ~~LSTM: migrar lstm_model.py de tensorflow a torch~~ RESUELTO (Sprint 5, `lstm_model.py` ya usa PyTorch)
- [x] ~~Dashboard: poblar mape_global y nivel_servicio~~ RESUELTO (`dashboard.py`, via `get_business_wapes`)
- [x] ~~hasCLPSkus en Inventory.tsx~~ RESUELTO (`inventory.py:51` calcula `has_clp_skus` real desde `sales_unit`)
- [x] ~~DEBUG=false en produccion~~ RESUELTO (`render.yaml` ya lo fija en `false`)
- [x] ~~RLS en Supabase~~ REVISADO 2026-08-24: `businesses`/`sales_history`/`stores` tenian politicas `ALL` abiertas a `public` (agujero real via anon key, sin relacion con el backend que usa `postgres`/bypassrls); se eliminaron. Resto de tablas ya denegaba por default.

**Bugs conocidos / deuda:**
- [x] ~~El UI de Forecast etiqueta valores en "uds" sin chequear si la data es CLP~~ RESUELTO en S2-F
- [x] ~~No hay endpoint para editar/eliminar registros de `sales_history`~~ RESUELTO en S3
- [x] ~~Tabla `ingest_log` (auditoria de cargas)~~ RESUELTO en S3
- [x] ~~S4: Inventario + Ordenes mockeados~~ RESUELTO en S4
- [x] ~~Un usuario solo podia tener un negocio (business_id en users)~~ RESUELTO en S4: user_businesses many-to-many
- [x] ~~Product() en ingest.py usaba campos obsoletos sku_id/name~~ RESUELTO en S4
