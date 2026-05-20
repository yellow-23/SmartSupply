from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import SalesHistory, User
from app.models.schemas import DashboardChartPoint, DashboardKPIs
from app.services.inventory_service import InventoryService

router = APIRouter()

_inventory_svc = InventoryService()


@router.get("/kpis", response_model=DashboardKPIs)
def get_kpis(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):

    skus_en_alerta = len(_inventory_svc.get_critical_skus(store_nbr=1))

    return DashboardKPIs(
        mape_global=None,
        skus_en_alerta=skus_en_alerta,
        ordenes_pendientes=0,
        nivel_servicio=None,
    )


@router.get("/chart-data", response_model=list[DashboardChartPoint])
def get_chart_data(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Retorna ventas reales agregadas por día para las últimas 4 semanas de datos
    disponibles en sales_history. La serie 'forecast' se poblará en Sprint 3.
    """
    max_date = db.query(func.max(SalesHistory.date)).scalar()
    if not max_date:
        return []

    start_date = max_date - timedelta(days=27)

    rows = (
        db.query(SalesHistory.date, func.sum(SalesHistory.sales).label("real"))
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
