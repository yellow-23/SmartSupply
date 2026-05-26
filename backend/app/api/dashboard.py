from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import IngestLog, PurchaseOrder, SalesHistory, StockLevel, User
from app.models.schemas import DashboardChartPoint, DashboardKPIs
from app.services.forecast_service import get_business_wapes

router = APIRouter()


@router.get("/kpis", response_model=DashboardKPIs)
def get_kpis(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    bid = current_user.business_id

    # Familias activas del negocio (con al menos un ingest activo)
    families = [
        row[0]
        for row in db.query(SalesHistory.family)
        .join(IngestLog, IngestLog.id == SalesHistory.ingest_id)
        .filter(
            SalesHistory.business_id == bid,
            IngestLog.status == "active",
        )
        .distinct()
        .all()
    ]
    total_families = len(families)

    # SKUs cuyo stock_level es 0 o no existe (necesitan reabastecimiento)
    stock_map = {
        sl.family: float(sl.quantity or 0)
        for sl in db.query(StockLevel).filter(StockLevel.business_id == bid).all()
    }
    skus_en_alerta = sum(
        1 for f in families if stock_map.get(f, 0.0) == 0.0
    )

    # Órdenes pendientes
    ordenes_pendientes = (
        db.query(func.count(PurchaseOrder.id))
        .filter(
            PurchaseOrder.business_id == bid,
            PurchaseOrder.status == "pending",
        )
        .scalar()
        or 0
    )

    # Nivel de servicio: % de familias con stock > 0
    if total_families > 0:
        familias_con_stock = sum(1 for f in families if stock_map.get(f, 0.0) > 0.0)
        nivel_servicio = round(familias_con_stock / total_families * 100, 1)
    else:
        nivel_servicio = None

    # MAPE global: promedio de WAPEs calculados durante forecasts del usuario
    wapes = get_business_wapes(bid)
    mape_global = round(sum(wapes) / len(wapes), 2) if wapes else None

    return DashboardKPIs(
        mape_global=mape_global,
        skus_en_alerta=skus_en_alerta,
        ordenes_pendientes=ordenes_pendientes,
        nivel_servicio=nivel_servicio,
    )


@router.get("/chart-data", response_model=list[DashboardChartPoint])
def get_chart_data(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Ventas reales agregadas por día (últimas 4 semanas), scoped al business del usuario."""
    bid = current_user.business_id

    max_date = (
        db.query(func.max(SalesHistory.date))
        .filter(SalesHistory.business_id == bid)
        .scalar()
    )
    if not max_date:
        return []

    start_date = max_date - timedelta(days=27)

    rows = (
        db.query(SalesHistory.date, func.sum(SalesHistory.sales).label("real"))
        .filter(SalesHistory.business_id == bid)
        .filter(SalesHistory.date >= start_date)
        .group_by(SalesHistory.date)
        .order_by(SalesHistory.date)
        .all()
    )

    return [
        DashboardChartPoint(
            date=row.date.strftime("%d %b"),
            real=round(row.real, 1),
            forecast=None,
        )
        for row in rows
    ]
