"""
Pydantic schemas — SmartSupply API
Define los modelos de request/response para todos los endpoints
"""

from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


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

class ProductCreate(BaseModel):
    business_id: int
    store_nbr: int
    family: str
    unit_cost: Optional[float] = None
    order_cost: float = 5000.0
    holding_rate: float = 0.25
    lead_time_days: int = 7
    moq: Optional[float] = None


class ProductResponse(BaseModel):
    id: int
    business_id: int
    store_nbr: int
    family: str
    unit_cost: Optional[float]
    order_cost: float
    holding_rate: float
    lead_time_days: int
    moq: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    unit_cost: Optional[float] = None
    order_cost: Optional[float] = None
    holding_rate: Optional[float] = None
    lead_time_days: Optional[int] = None
    moq: Optional[float] = None


class ProductPage(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    pages: int
    total_families: int


class StockLevelCreate(BaseModel):
    business_id: int
    store_nbr: int
    family: str
    quantity: float


class StockLevelResponse(BaseModel):
    id: int
    business_id: int
    store_nbr: int
    family: str
    quantity: float

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderResponse(BaseModel):
    id: int
    business_id: int
    store_nbr: int
    family: str
    quantity: float
    trigger_stock: Optional[float]
    reorder_point_s: Optional[float]
    order_up_to_S: Optional[float]
    policy_used: str
    status: str
    created_at: datetime
    expected_delivery: Optional[date]
    received_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


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
    sales_unit: Literal["CLP", "units"] = "units"


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
    owner_user_id: Optional[int] = None
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
    revenue: Optional[float] = None


class QualityIssue(BaseModel):
    """Problema detectado por el validador de ingesta."""
    severity: Literal["error", "warning", "info"]
    code: str = Field(..., description="Codigo identificador del problema (ej: FUTURE_DATES, MIXED_GRANULARITY)")
    family: Optional[str] = Field(None, description="Familia afectada, si aplica")
    message: str


class StockRecord(BaseModel):
    family: str
    quantity: float


class ProductRecord(BaseModel):
    family: str
    unit_cost: Optional[float] = None
    order_cost: Optional[float] = None
    lead_time_days: Optional[int] = None
    moq: Optional[float] = None


class IngestPreview(BaseModel):
    """Lo que Claude extrajo del archivo antes de confirmar la carga."""
    store_name: str
    records_found: int
    date_range_start: Optional[date]
    date_range_end: Optional[date]
    families_detected: list[str]
    records: list[IngestRecord]
    warnings: list[str] = []
    quality_issues: list[QualityIssue] = []
    sales_unit_detected: Optional[Literal["CLP", "units"]] = None
    data_type: str = "sales"  # "sales" | "stock" | "products" | "unknown"
    clarification_needed: bool = False
    clarification_message: Optional[str] = None
    stock_records: list[StockRecord] = []
    product_records: list[ProductRecord] = []


class IngestConfirm(BaseModel):
    business_id: int
    store_nbr: int
    records: list[IngestRecord]
    sales_unit: Literal["CLP", "units"] = "units"
    filename: str = "carga sin nombre"
    file_type: Literal["image", "excel", "pdf", "historic"] = "excel"
    data_type: str = "sales"
    stock_records: list[StockRecord] = []
    product_records: list[ProductRecord] = []


class IngestResponse(BaseModel):
    store_nbr: int
    records_loaded: int
    families: list[str]
    date_range_start: date
    date_range_end: date


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class IngestChatRequest(BaseModel):
    messages: list[ChatMessage]
    preview_summary: str
    business_name: str = ""


class IngestChatResponse(BaseModel):
    reply: str
    trigger_confirm: bool = False


# ─── Cargas (ingest_log) ────────────────────────────────────────────────────────

class IngestLogResponse(BaseModel):
    id: int
    business_id: int
    store_nbr: int
    user_id: int
    uploader_name: Optional[str] = None
    filename: str
    file_type: str
    records_loaded: int
    sales_unit: str
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    families: Optional[list[str]] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SalesRecordResponse(BaseModel):
    id: int
    date: date
    family: str
    sales: float
    onpromotion: int
    sales_unit: str
    ingest_id: Optional[int] = None

    class Config:
        from_attributes = True


class SalesRecordUpdate(BaseModel):
    date: Optional[date] = None
    family: Optional[str] = None
    sales: Optional[float] = Field(None, ge=0)
    onpromotion: Optional[int] = Field(None, ge=0)
