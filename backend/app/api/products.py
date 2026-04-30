from fastapi import APIRouter, HTTPException
from app.models.schemas import ProductCreate, ProductResponse

router = APIRouter()

# TODO: Conectar con base de datos PostgreSQL via SQLAlchemy
# Por ahora retorna datos de ejemplo para desarrollo

MOCK_PRODUCTS = {
    "GROCERY-001": {
        "id": 1, "sku_id": "GROCERY-001", "name": "Arroz 1kg", "family": "GROCERY I",
        "store_nbr": 1, "unit_cost": 850.0, "lead_time_days": 3, "min_order_qty": 10,
        "created_at": "2025-01-01T00:00:00",
    },
    "BEVERAGES-001": {
        "id": 2, "sku_id": "BEVERAGES-001", "name": "Jugo Naranja 1L", "family": "BEVERAGES",
        "store_nbr": 1, "unit_cost": 1200.0, "lead_time_days": 2, "min_order_qty": 6,
        "created_at": "2025-01-01T00:00:00",
    },
}


@router.get("/", response_model=list[ProductResponse])
async def list_products(store_nbr: int = 1, family: str = None):
    """Lista todos los SKUs, con filtro opcional por tienda y familia."""
    products = list(MOCK_PRODUCTS.values())
    if store_nbr:
        products = [p for p in products if p["store_nbr"] == store_nbr]
    if family:
        products = [p for p in products if p["family"] == family]
    return products


@router.get("/{sku_id}", response_model=ProductResponse)
async def get_product(sku_id: str):
    """Detalle de un SKU por su ID."""
    if sku_id not in MOCK_PRODUCTS:
        raise HTTPException(status_code=404, detail=f"SKU '{sku_id}' no encontrado")
    return MOCK_PRODUCTS[sku_id]


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate):
    """Registra un nuevo SKU en el sistema."""
    if product.sku_id in MOCK_PRODUCTS:
        raise HTTPException(status_code=409, detail=f"SKU '{product.sku_id}' ya existe")
    # TODO: Insertar en base de datos
    new_product = {**product.model_dump(), "id": len(MOCK_PRODUCTS) + 1, "created_at": "2025-01-01T00:00:00"}
    MOCK_PRODUCTS[product.sku_id] = new_product
    return new_product
