# SmartSupply

Proyecto de título de Ingeniería Civil Informática, Universidad Andrés Bello, 2026.

**Desarrollo de una plataforma SaaS con el propósito de pronóstico de demanda y reposición automatizada dirigida a negocios emergentes.**

SmartSupply recibe las ventas de un negocio en el formato que las tenga (foto, Excel, CSV o PDF), predice la demanda de cada producto eligiendo automáticamente el mejor modelo y propone las órdenes de compra necesarias para no quedarse sin stock.

- Aplicación: https://app.smart-supply.cl
- API: https://smartsupply-e6g8.onrender.com (documentación en `/docs`)

**Hipótesis.** La selección automática de modelo por SKU (AMS) empata la precisión (WAPE) y el capital inmovilizado del mejor estimador individual sin saber de antemano cuál es, y con eso reduce el riesgo de aplicar un modelo inadecuado a todo el catálogo. De forma complementaria se evalúa si un ensamble simple supera a la selección de un solo modelo.

---

## Qué hace

| Módulo | Descripción |
|---|---|
| Ingesta con IA | Extrae ventas, catálogo y stock desde imágenes, Excel, CSV y PDF. Lee libros de Excel con varias hojas, valida la calidad de los datos antes de cargar y deja cada carga registrada para poder revertirla. |
| Predicción de demanda | El AMS entrena ARIMA, Prophet y XGBoost por producto y elige el de menor WAPE. También proyecta la venta total de la tienda a 14 o 30 días. |
| Inventario | Calcula EOQ, punto de reorden `s` y nivel objetivo `S` por producto, y alerta cuando el stock baja del punto de reorden. |
| Órdenes de compra | Genera una orden por proveedor con los productos críticos. Permite crear órdenes manuales, editarlas, seguir su estado, buscarlas y descargarlas en PDF o Excel. |
| Stocky | Asistente conversacional que consulta y actualiza productos, stock y órdenes del negocio. |
| Multi-negocio | Un usuario puede tener varios negocios, cada uno con varias ubicaciones. Los datos se aíslan por negocio. |
| Notificaciones | Correo diario de stock bajo y resumen semanal para el dueño de cada negocio. |
| Administración | Panel para el administrador de la plataforma: usuarios, roles y negocios. |

---

## Cómo funciona el AMS

1. La serie de ventas de un producto se divide en orden cronológico: 70% entrenamiento, 15% validación y 15% prueba.
2. Se entrenan ARIMA, Prophet y XGBoost con el tramo de entrenamiento.
3. Gana el modelo con menor WAPE en validación.
4. El WAPE que se informa se mide en el tramo de prueba, que no participó en la elección.
5. El ganador se reentrena con toda la serie para generar la predicción.

| Modelo | Configuración |
|---|---|
| ARIMA | Componente estacional semanal cuando hay 21 días o más. La diferenciación se decide con un test ADF y el resto de los parámetros por AIC. |
| Prophet | Tendencia, estacionalidad semanal y feriados chilenos. La estacionalidad anual se activa con 2 años o más de datos. |
| XGBoost | Un modelo por cada día del horizonte, con rezagos, promedios móviles, calendario y feriados. |
| LSTM | Implementado en PyTorch. No participa en la selección automática. |

---

## Estructura del repositorio

```
SmartSupply/
├── backend/
│   ├── app/
│   │   ├── api/         # 13 routers: auth, forecast, inventory, products, orders, sales,
│   │   │                #   ingest, ingests, businesses, dashboard, stocky, admin, notify
│   │   ├── models/      # ORM (SQLAlchemy) y esquemas (Pydantic)
│   │   └── services/    # Predicción, inventario, ingesta, validador, Stocky,
│   │                    #   notificaciones, exportación y validación de RUT
│   ├── scripts/         # Migraciones SQL
│   └── tests/           # Pruebas con pytest
│
├── forecasting/src/     # ARIMA, Prophet, XGBoost, LSTM y el selector AMS
├── inventory/src/       # EOQ, política (s, S), generador de órdenes y simulador
├── etl/scripts/         # Limpieza y carga del dataset de referencia, validación del AMS por lotes
│
├── frontend/src/
│   ├── features/        # admin, auth, business, dashboard, datos, forecast,
│   │                    #   ingest, inventory, orders, products, stocky
│   └── shared/          # Cliente de API, layout y componentes comunes
│
├── landing/             # Página de presentación del producto
├── datasets/
│   ├── processed/       # Datos de referencia (tienda 1 de Favorita)
│   ├── prueba_s7/       # Libro de prueba completo: catálogo, ventas y stock
│   └── test_ingest/     # Archivos de ejemplo para probar la ingesta
│
├── docs/                # Documento de tesis, diagramas, guion del video y plantillas de correo
└── .github/workflows/   # Tarea programada de notificaciones
```

---

## Arquitectura y despliegue

| Capa | Tecnología | Dónde corre |
|---|---|---|
| Frontend | React, Vite, Tailwind, TanStack Query, Zustand, Recharts | Cloudflare Pages |
| Backend | FastAPI, SQLAlchemy 2, Pydantic 2, Python 3.11 | Render |
| Base de datos | PostgreSQL | Supabase |
| Autenticación | Supabase Auth: correo y contraseña, y Google | Supabase |
| IA | Claude (Anthropic) para la ingesta y para Stocky | API de Anthropic |
| Predicción | statsmodels, Prophet, XGBoost, PyTorch | Dentro del backend |
| Correos | Resend | Tarea programada en GitHub Actions |
| Exportación | openpyxl (Excel) y fpdf2 (PDF) | Dentro del backend |

Cada push a `main` despliega el backend en Render y el frontend en Cloudflare Pages. Hay un solo ambiente, el de producción; el desarrollo se hace en local.

---

## Instalación local

Requisitos: Python 3.11, Node 18 o superior y un proyecto en Supabase.

### Backend

```bash
bash setup.sh                 # crea el entorno virtual e instala dependencias (en Windows: setup.ps1)
source venv/bin/activate
cd backend
uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000` y su documentación en `http://localhost:8000/docs`.

Variables en `backend/.env`:

```
DATABASE_URL=postgresql://...        # conexión a Supabase (pooler, puerto 6543)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=...                     # clave anónima
ANTHROPIC_API_KEY=...
CRON_SECRET=...                      # solo para probar /api/notify
RESEND_API_KEY=...                   # opcional; sin ella los correos no se envían
RESEND_FROM_EMAIL=...                # opcional
```

### Base de datos

Los scripts de migración están en `backend/scripts/` (`migrate_*.sql`) y se aplican en el editor SQL de Supabase. Los más recientes son `migrate_s7_oc_lines_category.sql` (familias, proveedores y líneas de órdenes), `migrate_s8_business_contact.sql` (datos de contacto del negocio) y `migrate_s9_store_forecasts.sql` (proyección de la tienda).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Queda en `http://localhost:5173`. Variables en `frontend/.env`:

```
VITE_API_URL=http://localhost:8000/api
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=...
```

### Pruebas

```bash
cd backend
PYTHONPATH=. python -m pytest tests/
```

### Probar el flujo completo

1. Crear un negocio de prueba en **Mi negocio**.
2. En **Subir ventas**, cargar `datasets/prueba_s7/SmartSupply_libro_prueba.xlsx`. La hoja de instrucciones del libro explica qué se debe ver en cada pantalla.
3. Revisar **Inventario**, generar órdenes en **Órdenes** y correr una predicción en **Predecir demanda**.

---

## Dataset de referencia

**Store Sales, Corporación Favorita** (Kaggle): 3.000.888 filas, 54 tiendas y 33 familias de productos, del 1 de enero de 2013 al 15 de agosto de 2017. Se usa para validar la hipótesis del AMS. No reemplaza a la ingesta: cada negocio carga sus propios datos.

En el repositorio se incluye la tienda 1 ya procesada (`datasets/processed/benchmark_store1.csv`), que la aplicación ofrece como "dataset de referencia" en la vista de predicción.

---

## Integrantes

| Integrante | Módulo | Responsabilidad |
|---|---|---|
| Ignacio Duarte | `forecasting/` | ARIMA, Prophet, XGBoost, LSTM y AMS |
| Matías Muñoz | `inventory/` | EOQ, política (s, S) y simulador |
| Cristóbal Flores | `backend/`, `etl/`, `frontend/` | API, ETL, interfaz web, ingesta con IA y Stocky |

Profesor guía: Paulo Quinsacara Jofré.

---

## Ramas y commits

Ver [`CONVENTIONS.md`](./CONVENTIONS.md).
