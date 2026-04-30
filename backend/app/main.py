"""
SmartSupply — API REST principal
FastAPI backend para la plataforma de predicción de demanda y reabastecimiento
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import forecast, inventory, products, orders

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

# Registrar routers
app.include_router(forecast.router,   prefix="/api/forecast",   tags=["Forecasting"])
app.include_router(inventory.router,  prefix="/api/inventory",  tags=["Inventario"])
app.include_router(products.router,   prefix="/api/products",   tags=["Productos / SKUs"])
app.include_router(orders.router,     prefix="/api/orders",     tags=["Órdenes de compra"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "SmartSupply API", "version": "0.1.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
