from datetime import date, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import PurchaseOrder, User
from app.models.schemas import PurchaseOrderResponse
from app.services.inventory_service import InventoryService

router = APIRouter()
service = InventoryService()

_VALID_STATUSES = {"pending", "confirmed", "in_transit", "received", "cancelled"}
_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"in_transit", "cancelled"},
    "in_transit": {"received", "cancelled"},
    "received": set(),
    "cancelled": set(),
}


@router.get("", response_model=list[PurchaseOrderResponse])
async def list_orders(
    business_id: int,
    store_nbr: int = 1,
    status: Optional[str] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    """Lista las órdenes de compra del negocio, con filtro opcional por estado."""
    q = db.query(PurchaseOrder).filter(
        PurchaseOrder.business_id == business_id,
        PurchaseOrder.store_nbr == store_nbr,
    )
    if status:
        q = q.filter(PurchaseOrder.status == status)
    return q.order_by(PurchaseOrder.created_at.desc()).all()


@router.post("/generate", response_model=list[PurchaseOrderResponse])
async def generate_automatic_orders(
    business_id: int,
    store_nbr: int = 1,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    """
    Revisa todos los SKUs en estado crítico (stock <= s) y genera órdenes
    automáticas con la política (s,S). Devuelve las órdenes creadas.
    """
    try:
        critical_skus = service.get_critical_skus(db=db, business_id=business_id, store_nbr=store_nbr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    created = []
    for sku in critical_skus:
        if sku.get("needs_cost_setup"):
            # Sin unit_cost configurado el calculo de cantidad no es confiable -- no se genera
            # orden automatica para este SKU hasta que se cargue el costo (ver /inventory/alerts).
            continue

        # Retrieve lead_time for expected_delivery
        from app.services.inventory_service import _get_product_params
        params = _get_product_params(db, business_id, store_nbr, sku["family"])
        lead_time = params["lead_time_days"]

        order = PurchaseOrder(
            business_id=business_id,
            store_nbr=store_nbr,
            family=sku["family"],
            quantity=sku["order_quantity"],
            trigger_stock=sku["current_stock"],
            reorder_point_s=sku["reorder_point_s"],
            order_up_to_S=sku["order_up_to_S"],
            policy_used="s_s",
            status="pending",
            expected_delivery=date.today() + timedelta(days=lead_time),
        )
        db.add(order)
        created.append(order)

    db.commit()
    for o in created:
        db.refresh(o)

    return created


@router.patch("/{order_id}/status", response_model=PurchaseOrderResponse)
async def update_order_status(
    order_id: int,
    new_status: str,
    business_id: int,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    """
    Cambia el estado de una orden. Transiciones válidas:
    pending -> confirmed | cancelled
    confirmed -> in_transit | cancelled
    in_transit -> received | cancelled
    """
    if new_status not in _VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Estado inválido: {new_status}")

    order = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == order_id,
        PurchaseOrder.business_id == business_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Orden #{order_id} no encontrada")

    allowed = _TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede pasar de '{order.status}' a '{new_status}'",
        )

    order.status = new_status
    if new_status == "received":
        from datetime import datetime
        order.received_at = datetime.now()

    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}", response_model=PurchaseOrderResponse)
async def get_order(
    order_id: int,
    business_id: int,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    """Detalle de una orden de compra por ID."""
    order = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == order_id,
        PurchaseOrder.business_id == business_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Orden #{order_id} no encontrada")
    return order
