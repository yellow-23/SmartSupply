"""
SmartSupply — API REST principal
FastAPI backend para la plataforma de predicción de demanda y reabastecimiento
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, forecast, inventory, products, orders, sales, ingest, ingests, businesses, dashboard
from app.api.auth import get_current_user

app = FastAPI(
    title="SmartSupply API",
    description="API REST para predicción de demanda y reabastecimiento automático de distribuidoras",
    version="0.1.0",
)

# CORS — permitir requests desde el frontend en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_auth = [Depends(get_current_user)]

# Registrar routers
app.include_router(auth.router,       prefix="/api/auth",       tags=["Autenticación"])
app.include_router(forecast.router,   prefix="/api/forecast",   tags=["Forecasting"],        dependencies=_auth)
app.include_router(inventory.router,  prefix="/api/inventory",  tags=["Inventario"],         dependencies=_auth)
app.include_router(products.router,   prefix="/api/products",   tags=["Productos / SKUs"],   dependencies=_auth)
app.include_router(orders.router,     prefix="/api/orders",     tags=["Órdenes de compra"],  dependencies=_auth)
app.include_router(sales.router,      prefix="/api/sales",      tags=["Datos históricos"],   dependencies=_auth)
app.include_router(ingest.router,     prefix="/api/ingest",     tags=["Ingesta IA"],         dependencies=_auth)
app.include_router(ingests.router,    prefix="/api/ingests",    tags=["Cargas"],             dependencies=_auth)
app.include_router(businesses.router, prefix="/api/businesses", tags=["Negocios"],           dependencies=_auth)
app.include_router(dashboard.router,  prefix="/api/dashboard",  tags=["Dashboard"],          dependencies=_auth)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "SmartSupply API", "version": "0.1.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
