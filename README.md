# SmartSupply — Plataforma de Predicción de Demanda y Reabastecimiento Automático

> **Universidad Andrés Bello · Ingeniería Civil en Informática · Proyecto de Tesis 2025**

Sistema que entrena modelos de forecasting por SKU (ARIMA, Prophet, XGBoost, LSTM), selecciona automáticamente el mejor modelo por producto y genera políticas de reabastecimiento óptimas (EOQ y política (s,S)) con restricciones reales de proveedor.

**Hipótesis:** *"La selección automática de modelo de forecasting por SKU reduce el error de predicción (MAPE) y el capital inmovilizado en inventario vs. un modelo único aplicado a todos los productos."*

---

## Estructura del repositorio

```
SmartSupply/
├── forecasting/        # Int.1 — Modelos de predicción de demanda
│   ├── data/           # Dataset Kaggle (NO subir al repo → .gitignore)
│   ├── notebooks/      # Análisis EDA + entrenamiento de modelos
│   ├── models/         # Modelos serializados (.pkl, .pt)
│   └── src/            # Código fuente de modelos y selector automático
│
├── inventory/          # Int.2 — Modelos de inventario
│   ├── notebooks/      # EOQ y política (s,S) exploración
│   └── src/            # EOQ, (s,S), generador de órdenes, simulador
│
├── backend/            # Int.3 — API REST (FastAPI)
│   └── app/
│       ├── api/        # Endpoints: forecast, inventory, products, orders
│       ├── models/     # Pydantic schemas
│       └── services/   # Lógica de negocio
│
├── etl/                # Int.3 — Pipeline ETL
│   └── scripts/        # Descarga → limpieza → carga a base de datos
│
├── frontend/           # Int.3 — Dashboard web (React)
│   └── src/
│       ├── components/ # Componentes reutilizables
│       ├── pages/      # Páginas de la app
│       └── api/        # Llamadas al backend
│
└── docs/               # Documentos de tesis
```

---

## Integrantes y responsabilidades

| Rol | Módulo | Tareas principales |
|-----|--------|--------------------|
| **Int. 1** | Forecasting | ARIMA, Prophet, XGBoost, LSTM + selector automático (AMS) |
| **Int. 2** | Inventario | EOQ clásico, política (s,S), simulador, métricas de inventario |
| **Int. 3** | Backend/ETL/UI | FastAPI, pipeline ETL, PostgreSQL, dashboard React |

---

## Setup del entorno

### Requisitos previos
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (o cuenta Supabase)
- Git

### Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Completar con tus credenciales
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`
Documentación automática: `http://localhost:8000/docs`

### Forecasting

```bash
cd forecasting
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Inventario

```bash
cd inventory
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

### ETL (cargar dataset)

```bash
cd etl
# Asegurarse de tener el .env con las credenciales de BD
python scripts/01_download_kaggle.py   # Descomprime el dataset
python scripts/02_clean.py             # Limpieza y normalización
python scripts/03_load_supabase.py     # Carga a PostgreSQL/Supabase
```

---

## Dataset

**Store Sales — Time Series Forecasting** (Kaggle)
- Fuente: Corporación Favorita (Ecuador), datos públicos
- Período: 2013-01-01 → 2017-08-15
- 3.000.888 registros · 54 tiendas · 33 familias de productos
- Archivos: `datasets/store-sales-time-series-forecasting.zip`
- Los CSV descomprimidos van en `forecasting/data/` (ignorados por .gitignore)

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Forecasting | Python, statsmodels (ARIMA), Prophet, XGBoost, TensorFlow/Keras (LSTM) |
| Inventario | Python, NumPy, SciPy |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Base de datos | PostgreSQL / Supabase |
| ETL | Python, Pandas |
| Frontend | React, Vite, Recharts |
| Deploy | GCP / Render |

---

## Convenciones de ramas y commits

Ver [`CONVENTIONS.md`](./CONVENTIONS.md) para la guía completa.

```
main          → rama principal, siempre estable
feat/xxx      → nuevas funcionalidades
fix/xxx       → correcciones de bugs
docs/xxx      → cambios solo de documentación
```

---

*Documento preparado para presentación — Mayo 2025*
