from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import SalesHistory, User
from app.models.schemas import DashboardChartPoint, DashboardKPIs

router = APIRouter()


@router.get("/kpis", response_model=DashboardKPIs)
def get_kpis(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """KPIs del business del usuario. mape_global y nivel_servicio se llenan cuando Int.1 e Int.2 expongan sus métricas."""
    return DashboardKPIs(
        mape_global=None,
        skus_en_alerta=0,
        ordenes_pendientes=0,
        nivel_servicio=None,
    )


@router.get("/chart-data", response_model=list[DashboardChartPoint])
def get_chart_data(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Ventas reales agregadas por día (últimas 4 semanas), scoped al business del usuario."""
    max_date = (
        db.query(func.max(SalesHistory.date))
        .filter(SalesHistory.business_id == current_user.business_id)
        .scalar()
    )
    if not max_date:
        return []

    start_date = max_date - timedelta(days=27)

    rows = (
        db.query(SalesHistory.date, func.sum(SalesHistory.sales).label("real"))
        .filter(SalesHistory.business_id == current_user.business_id)
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
