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

## Estado actual (2026-05-23)

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
- [ ] **S3: Más refinamiento del flujo de Ingesta** (filtros, edición manual de registros antes de confirmar)
- [ ] **S4: Inventario + Órdenes + Simulador (s,S)** — Int.2; conectar `hasCLPSkus` en `Inventory.tsx` una vez que haya datos reales de inventario
- [ ] S5: Reportes + Admin + Notificaciones + recuperacion contrasena por email real (SMTP)
- [ ] S6: QA + Deploy Render/Cloudflare + Tesis

**Mejoras tecnicas acumuladas:**
- [ ] Cache de predicciones por SKU+tienda+horizonte (reducir latencia 30-90s a <1s en hit)
- [ ] LSTM: migrar lstm_model.py de tensorflow a torch (ya instalado en venv)
- [ ] Dashboard: poblar `mape_global` y `nivel_servicio` cuando Int.1 e Int.2 expongan sus metricas
- [ ] Dashboard: poblar serie `forecast` en chart-data integrando el AMS
- [ ] DEBUG=false en produccion para no exponer debug_token en forgot-password
- [ ] RLS en Supabase para garantizar aislamiento por business_id (defensa en profundidad mas alla de filtros en queries)
- [ ] Tabla `ingest_log` (auditoria de quien subio que archivo cuando) para poder revertir cargas malas
- [ ] Tests automatizados de `_parse_date` y `validate_ingest_records` (proyecto no tiene infraestructura de testing aun)

**Bugs conocidos / deuda:**
- [ ] El UI de Forecast etiqueta valores en "uds" sin chequear si la data es CLP - ~~se arregla con S2-F~~ RESUELTO en S2-F
- [ ] No hay endpoint para editar/eliminar registros de `sales_history` (si el usuario carga data mala, hoy se borra solo via SQL directo o reset del business)
- [ ] `MEMORY.md` y CLAUDE.md no estan auto-sincronizados
