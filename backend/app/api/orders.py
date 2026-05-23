from fastapi import APIRouter, HTTPException
from app.models.schemas import OrderCreate, OrderResponse
from app.services.inventory_service import InventoryService

router = APIRouter()
service = InventoryService()

MOCK_ORDERS: list[dict] = []


@router.get("", response_model=list[OrderResponse])
async def list_orders(store_nbr: int = 1, status: str = None):
    """Lista las órdenes de compra generadas, con filtro opcional por estado."""
    orders = [o for o in MOCK_ORDERS if o["store_nbr"] == store_nbr]
    if status:
        orders = [o for o in orders if o["status"] == status]
    return orders


@router.post("/generate")
async def generate_automatic_orders(store_nbr: int = 1):
    """
    Revisa todos los SKUs en estado crítico (stock < punto de reorden s) y
    genera órdenes de compra automáticas usando la política (s,S).
    Este es el corazón del sistema de reabastecimiento automático.
    """
    try:
        # Obtener SKUs críticos
        critical_skus = service.get_critical_skus(store_nbr=store_nbr)
        generated_orders = []

        for sku_info in critical_skus:
            order = {
                "id": len(MOCK_ORDERS) + 1,
                "sku_id": sku_info["sku_id"],
                "store_nbr": store_nbr,
                "quantity": sku_info["order_quantity"],
                "trigger_stock": sku_info["current_stock"],
                "policy_used": "s_s",
                "status": "pending",
                "created_at": "2025-01-01T00:00:00",
                "expected_delivery": None,
            }
            MOCK_ORDERS.append(order)
            generated_orders.append(order)

        return {
            "orders_generated": len(generated_orders),
            "orders": generated_orders,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int):
    """Detalle de una orden de compra por ID."""
    order = next((o for o in MOCK_ORDERS if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail=f"Orden #{order_id} no encontrada")
    return order
