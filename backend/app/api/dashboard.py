from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, tuple_
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, resolve_business_id
from app.database import get_db
from app.models.orm import IngestLog, PurchaseOrder, SalesHistory, StockLevel, User
from app.models.schemas import DashboardChartData, DashboardChartPoint, DashboardKPIs, StoreForecast
from app.services.forecast_service import (
    ForecastService, InsufficientDataError, get_business_cached_forecasts, get_business_wapes, load_store_total_series,
)

router = APIRouter()


@router.get("/kpis", response_model=DashboardKPIs)
def get_kpis(
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    bid = resolve_business_id(db, current_user, business_id)

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


@router.get("/chart-data", response_model=DashboardChartData)
def get_chart_data(
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int | None = Query(default=None),
    family: str | None = Query(default=None, description="Ver solo esta familia (debe tener forecast cacheado)"),
    db: Session = Depends(get_db),
):
    """Ventas reales agregadas por día (últimas 4 semanas), scoped al business del usuario."""
    bid = resolve_business_id(db, current_user, business_id)

    max_date = (
        db.query(func.max(SalesHistory.date))
        .filter(SalesHistory.business_id == bid)
        .scalar()
    )
    if not max_date:
        return DashboardChartData(points=[], forecast_skus=[], total_skus=0)

    start_date = max_date - timedelta(days=27)
    total_skus = (
        db.query(SalesHistory.family, SalesHistory.store_nbr)
        .filter(SalesHistory.business_id == bid, SalesHistory.date >= start_date)
        .distinct()
        .count()
    )

    all_cached = get_business_cached_forecasts(bid)
    cached_forecasts = [c for c in all_cached if not family or c.sku_id == family]

    q = (
        db.query(SalesHistory.date, func.sum(SalesHistory.sales).label("real"))
        .filter(SalesHistory.business_id == bid)
        .filter(SalesHistory.date >= start_date)
    )
    if cached_forecasts:
        # La linea real debe sumar los mismos SKUs que la prediccion, si no no son comparables
        q = q.filter(tuple_(SalesHistory.family, SalesHistory.store_nbr).in_(
            [(c.sku_id, c.store_nbr) for c in cached_forecasts]
        ))
    rows = q.group_by(SalesHistory.date).order_by(SalesHistory.date).all()

    points = [
        DashboardChartPoint(
            date=row.date.strftime("%d %b"),
            real=round(row.real, 1),
            forecast=None,
        )
        for row in rows
    ]

    # Suma la prediccion cacheada por dia entre los SKUs para los que el usuario
    # ya corrio un forecast (pagina Forecast). Si no hay ninguno, no se agrega nada.
    forecast_by_date: dict = {}
    for cached in cached_forecasts:
        for point in cached.predictions:
            if point.date > max_date:
                forecast_by_date[point.date] = forecast_by_date.get(point.date, 0.0) + point.predicted_sales

    if forecast_by_date and points:
        points[-1].forecast = points[-1].real  # conecta la linea punteada con el historico

    for d in sorted(forecast_by_date):
        points.append(DashboardChartPoint(
            date=d.strftime("%d %b"),
            real=None,
            forecast=round(forecast_by_date[d], 1),
        ))

    return DashboardChartData(
        points=points,
        forecast_skus=sorted({c.sku_id for c in all_cached}),
        total_skus=total_skus,
    )


@router.get("/store-forecast", response_model=StoreForecast)
def get_store_forecast(
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int | None = Query(default=None),
    store_nbr: int = Query(default=1),
    horizon_days: int = Query(default=14, ge=7, le=30),
    db: Session = Depends(get_db),
):
    """Proyeccion de la venta total de la ubicacion (todos los productos, en CLP si hay monto).
    La primera vez entrena el AMS (segundos); despues sale del cache hasta que cambien las ventas."""
    bid = resolve_business_id(db, current_user, business_id)
    try:
        result = ForecastService().predict_store_total(db, bid, store_nbr, horizon_days)
        series, _unit = load_store_total_series(db, bid, store_nbr)
    except InsufficientDataError as e:
        raise HTTPException(
            status_code=422,
            detail={"code": "insufficient_data", "days_available": e.days_available, "days_required": e.days_required,
                    "message": f"Se necesitan al menos {e.days_required} días de ventas para proyectar la tienda."},
        )

    points = [DashboardChartPoint(date=d.strftime("%Y-%m-%d"), real=round(float(v), 2)) for d, v in series.iloc[-28:].items()]
    if points:
        points[-1].forecast = points[-1].real  # une la linea proyectada con la real
    points += [DashboardChartPoint(date=p.date.isoformat(), forecast=p.predicted_sales) for p in result.predictions]
    return StoreForecast(
        store_nbr=store_nbr, unit=result.sales_unit, model_used=result.model_used, wape=result.mape_validation,
        horizon_days=horizon_days, generated_at=result.generated_at, points=points,
    )
