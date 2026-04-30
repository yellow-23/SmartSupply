"""
Pydantic schemas — SmartSupply API
Define los modelos de request/response para todos los endpoints
"""

from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ─── Productos / SKUs ──────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    sku_id: str = Field(..., example="GROCERY-001", description="Identificador único del SKU")
    name: str = Field(..., example="Arroz 1kg")
    family: str = Field(..., example="GROCERY I")
    store_nbr: int = Field(..., example=1)
    unit_cost: float = Field(..., example=850.0, description="Costo unitario de adquisición (CLP)")
    lead_time_days: int = Field(default=3, description="Lead time del proveedor en días")
    min_order_qty: int = Field(default=1, description="Mínimo de compra (MOQ) del proveedor")

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Forecasting ───────────────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    sku_id: str = Field(..., example="GROCERY-001")
    store_nbr: int = Field(..., example=1)
    horizon_days: Literal[7, 14, 30] = Field(default=14, description="Horizonte de predicción en días")
    model: Optional[Literal["arima", "prophet", "xgboost", "lstm", "auto"]] = Field(
        default="auto",
        description="Modelo a usar. 'auto' activa el selector automático (AMS)"
    )

class ForecastPoint(BaseModel):
    date: date
    predicted_sales: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

class ForecastResponse(BaseModel):
    sku_id: str
    store_nbr: int
    model_used: str
    mape_validation: Optional[float] = Field(None, description="MAPE del modelo en validación (%)")
    horizon_days: int
    predictions: list[ForecastPoint]
    generated_at: datetime


# ─── Inventario ────────────────────────────────────────────────────────────────

class InventoryStatus(BaseModel):
    sku_id: str
    store_nbr: int
    current_stock: float
    reorder_point_s: float = Field(..., description="Punto de reorden (s) de la política (s,S)")
    order_up_to_S: float = Field(..., description="Nivel de reposición (S) de la política (s,S)")
    eoq: float = Field(..., description="Cantidad óptima EOQ")
    policy: Literal["eoq", "s_s"] = Field(default="s_s")
    needs_reorder: bool
    days_until_stockout: Optional[float] = None
    updated_at: datetime

class InventoryMetrics(BaseModel):
    sku_id: str
    store_nbr: int
    period_start: date
    period_end: date
    capital_inmovilizado: float = Field(..., description="Capital inmovilizado promedio (CLP)")
    stockout_rate: float = Field(..., description="Tasa de quiebre de stock (%)")
    inventory_turnover: float = Field(..., description="Rotación de inventario")
    service_level: float = Field(..., description="Nivel de servicio (%)")
    total_inventory_cost: float = Field(..., description="Costo total de inventario (CLP)")


# ─── Órdenes de compra ─────────────────────────────────────────────────────────

class OrderBase(BaseModel):
    sku_id: str
    store_nbr: int
    quantity: float = Field(..., description="Cantidad a ordenar (unidades)")
    trigger_stock: float = Field(..., description="Stock en el momento de generar la orden")
    policy_used: Literal["eoq", "s_s"]

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: int
    status: Literal["pending", "confirmed", "received", "cancelled"] = "pending"
    created_at: datetime
    expected_delivery: Optional[date] = None

    class Config:
        from_attributes = True
