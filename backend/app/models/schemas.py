"""
Pydantic schemas — SmartSupply API
Define los modelos de request/response para todos los endpoints
"""

from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardKPIs(BaseModel):
    mape_global: Optional[float] = Field(None, description="MAPE promedio de modelos activos (Sprint 3)")
    skus_en_alerta: int = Field(0, description="SKUs cuyo stock está por debajo del punto de reorden")
    ordenes_pendientes: int = Field(0, description="Órdenes con status=Pendiente (Sprint 4)")
    nivel_servicio: Optional[float] = Field(None, description="Nivel de servicio global % (Sprint 4)")


class DashboardChartPoint(BaseModel):
    date: str
    real: Optional[float] = None
    forecast: Optional[float] = None


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


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    family: Optional[str] = None
    unit_cost: Optional[float] = None
    lead_time_days: Optional[int] = None
    min_order_qty: Optional[int] = None


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
    model_config = {"protected_namespaces": ()}

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


# ─── Negocios (multi-tenancy) ──────────────────────────────────────────────────

class BusinessCreate(BaseModel):
    name: str = Field(..., example="Distribuidora Santa Elena")
    rut: Optional[str] = Field(None, example="76.123.456-7")
    city: Optional[str] = Field(None, example="Santiago")
    type: Optional[Literal["retail", "distributor", "wholesale", "demo"]] = "distributor"


class BusinessResponse(BaseModel):
    id: int
    name: str
    rut: Optional[str] = None
    city: Optional[str] = None
    type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Sales / Datos históricos ──────────────────────────────────────────────────

class StoreResponse(BaseModel):
    store_nbr: int
    city: Optional[str] = None
    state: Optional[str] = None
    type: Optional[str] = None
    cluster: Optional[int] = None

    class Config:
        from_attributes = True


class SalesPoint(BaseModel):
    date: date
    sales: float
    onpromotion: int

    class Config:
        from_attributes = True


class SalesSummaryItem(BaseModel):
    family: str
    total_sales: float
    avg_daily_sales: float
    days_on_promotion: int


# ─── Ingesta IA ────────────────────────────────────────────────────────────────

class IngestRecord(BaseModel):
    date: date
    family: str
    sales: float
    onpromotion: int = 0


class IngestPreview(BaseModel):
    """Lo que Claude extrajo del archivo antes de confirmar la carga."""
    store_name: str
    records_found: int
    date_range_start: Optional[date]
    date_range_end: Optional[date]
    families_detected: list[str]
    records: list[IngestRecord]
    warnings: list[str] = []


class IngestConfirm(BaseModel):
    business_id: int
    store_nbr: int
    records: list[IngestRecord]


class IngestResponse(BaseModel):
    store_nbr: int
    records_loaded: int
    families: list[str]
    date_range_start: date
    date_range_end: date
