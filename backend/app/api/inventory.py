from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from app.api.auth import get_current_user
from app.models.orm import User
from app.models.schemas import InventoryStatus, InventoryMetrics
from app.services.inventory_service import InventoryService

router = APIRouter()
service = InventoryService()


def _urgency(current_stock: float, reorder_point_s: float) -> str:
    if reorder_point_s <= 0:
        return "normal"
    ratio = current_stock / reorder_point_s
    if ratio < 0.3:
        return "critical"
    if ratio < 0.7:
        return "high"
    return "normal"


@router.get("/alerts")
async def get_stock_alerts(
    store_nbr: int = 1,
    limit: int = 50,
    sort_by: str = "urgency",
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """
    Retorna los SKUs cuyo stock actual está por debajo del punto de reorden (s).
    Soporta paginación con `limit` y ordenamiento con `sort_by=urgency`.
    """
    try:
        raw_alerts = service.get_critical_skus(store_nbr=store_nbr)

        _urgency_rank = {"critical": 0, "high": 1, "normal": 2}
        alerts = [
            {**a, "urgency": _urgency(a["current_stock"], a["reorder_point_s"])}
            for a in raw_alerts
        ]

        if sort_by == "urgency":
            alerts.sort(key=lambda x: _urgency_rank.get(x["urgency"], 2))

        return {"store_nbr": store_nbr, "alerts": alerts[:limit], "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sku_id}", response_model=InventoryStatus)
async def get_inventory_status(sku_id: str, store_nbr: int = 1):
    """
    Retorna el estado actual del inventario para un SKU.
    Incluye stock actual, punto de reorden (s), nivel de reposición (S) y EOQ.
    """
    try:
        return service.get_status(sku_id=sku_id, store_nbr=store_nbr)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{sku_id}/metrics", response_model=InventoryMetrics)
async def get_inventory_metrics(
    sku_id: str,
    store_nbr: int = 1,
    period_days: int = 30,
):
    """
    Retorna las métricas de desempeño de la política de inventario para un SKU
    en los últimos `period_days` días:
    - Capital inmovilizado (CLP)
    - Tasa de quiebre de stock (%)
    - Rotación de inventario
    - Nivel de servicio (%)
    - Costo total de inventario (CLP)
    """
    try:
        return service.get_metrics(sku_id=sku_id, store_nbr=store_nbr, period_days=period_days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
