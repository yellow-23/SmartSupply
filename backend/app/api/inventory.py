from fastapi import APIRouter, HTTPException
from app.models.schemas import InventoryStatus, InventoryMetrics
from app.services.inventory_service import InventoryService

router = APIRouter()
service = InventoryService()


@router.get("/alerts")
async def get_stock_alerts(store_nbr: int = 1):
    """
    Retorna todos los SKUs cuyo stock actual está por debajo del punto de reorden (s).
    Estos son candidatos para generar una orden de compra automática.
    """
    try:
        alerts = service.get_critical_skus(store_nbr=store_nbr)
        return {"store_nbr": store_nbr, "alerts": alerts, "count": len(alerts)}
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
