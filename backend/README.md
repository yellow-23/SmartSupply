# Backend — SmartSupply API (FastAPI)

API REST para la plataforma de predicción de demanda y reabastecimiento automático.

## Setup rápido

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Completar con credenciales reales
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs (Swagger): http://localhost:8000/docs
- Docs (ReDoc): http://localhost:8000/redoc

## Endpoints disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/api/forecast/predict` | Predicción con parámetros |
| GET | `/api/forecast/{sku_id}` | Predicción rápida (modelo auto) |
| GET | `/api/inventory/alerts` | SKUs en estado crítico |
| GET | `/api/inventory/{sku_id}` | Estado del inventario |
| GET | `/api/inventory/{sku_id}/metrics` | Métricas de desempeño |
| GET | `/api/products/` | Lista de SKUs |
| POST | `/api/orders/generate` | Generar órdenes automáticas |

## Estructura

```
backend/
├── app/
│   ├── main.py              ← Punto de entrada FastAPI
│   ├── api/
│   │   ├── forecast.py      ← Endpoints de predicción
│   │   ├── inventory.py     ← Endpoints de inventario
│   │   ├── products.py      ← CRUD de productos/SKUs
│   │   └── orders.py        ← Órdenes de compra automáticas
│   ├── models/
│   │   └── schemas.py       ← Pydantic schemas (request/response)
│   └── services/
│       ├── forecast_service.py   ← Puente con módulo forecasting/
│       └── inventory_service.py  ← Puente con módulo inventory/
├── requirements.txt
└── .env.example
```

## TODO (próximas implementaciones)

- [ ] Conectar servicios con PostgreSQL via SQLAlchemy
- [ ] Integrar `forecast_service.py` con `forecasting/src/selector.py` (Int.1)
- [ ] Integrar `inventory_service.py` con `inventory/src/s_s_policy.py` (Int.2)
- [ ] Agregar autenticación JWT
- [ ] Tests con pytest
