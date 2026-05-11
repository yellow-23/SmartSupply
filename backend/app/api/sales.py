from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import SalesHistory, Store
from app.models.schemas import SalesPoint, SalesSummaryItem, StoreResponse

router = APIRouter()


@router.get("/date-range")
def get_date_range(
    business_id: int = Query(..., description="ID del negocio"),
    db: Session = Depends(get_db),
):
    """
    Retorna el rango de fechas disponible para un negocio.
    Usar antes de llamar a /history o /summary para saber que fechas tiene el negocio.
    """
    row = db.query(
        func.min(SalesHistory.date).label("start"),
        func.max(SalesHistory.date).label("end"),
    ).filter(SalesHistory.business_id == business_id).first()

    if not row.start:
        raise HTTPException(status_code=404, detail=f"No hay datos para el negocio {business_id}")

    return {"business_id": business_id, "start": row.start, "end": row.end}


@router.get("/stores", response_model=list[StoreResponse])
def list_stores(
    business_id: int = Query(..., description="ID del negocio"),
    db: Session = Depends(get_db),
):
    """Lista las tiendas registradas de un negocio."""
    return db.query(Store).filter(Store.business_id == business_id).order_by(Store.store_nbr).all()


@router.get("/stores/{store_nbr}", response_model=StoreResponse)
def get_store(
    store_nbr: int,
    business_id: int = Query(...),
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(
        Store.store_nbr == store_nbr,
        Store.business_id == business_id,
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail=f"Tienda {store_nbr} no encontrada")
    return store


@router.get("/families")
def list_families(
    business_id: int = Query(..., description="ID del negocio"),
    db: Session = Depends(get_db),
):
    """Lista las categorias de productos que tiene un negocio en su historial."""
    rows = (
        db.query(SalesHistory.family)
        .filter(SalesHistory.business_id == business_id)
        .distinct()
        .order_by(SalesHistory.family)
        .all()
    )
    return [r.family for r in rows]


@router.get("/history", response_model=list[SalesPoint])
def get_sales_history(
    business_id: int = Query(..., description="ID del negocio"),
    family: str = Query(..., description="Categoria de producto"),
    store_nbr: Optional[int] = Query(default=None, description="Numero de tienda (opcional)"),
    start: Optional[date] = Query(default=None, description="Fecha inicio (default: inicio del negocio)"),
    end: Optional[date] = Query(default=None, description="Fecha fin (default: ultimo dato disponible)"),
    db: Session = Depends(get_db),
):
    """
    Historial de ventas diarias para una categoria.
    Si no se especifica start/end usa todo el rango disponible del negocio.
    """
    q = db.query(SalesHistory.date, SalesHistory.sales, SalesHistory.onpromotion).filter(
        SalesHistory.business_id == business_id,
        SalesHistory.family == family,
    )
    if store_nbr is not None:
        q = q.filter(SalesHistory.store_nbr == store_nbr)
    if start:
        q = q.filter(SalesHistory.date >= start)
    if end:
        q = q.filter(SalesHistory.date <= end)

    rows = q.order_by(SalesHistory.date).all()
    return [SalesPoint(date=r.date, sales=r.sales, onpromotion=r.onpromotion) for r in rows]


@router.get("/summary", response_model=list[SalesSummaryItem])
def get_sales_summary(
    business_id: int = Query(..., description="ID del negocio"),
    store_nbr: Optional[int] = Query(default=None, description="Numero de tienda (opcional)"),
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Resumen de ventas agregado por categoria para un negocio.
    Util para el widget de top productos del dashboard.
    """
    q = db.query(
        SalesHistory.family,
        func.sum(SalesHistory.sales).label("total_sales"),
        func.avg(SalesHistory.sales).label("avg_daily_sales"),
        func.sum(SalesHistory.onpromotion).label("days_on_promotion"),
    ).filter(SalesHistory.business_id == business_id)

    if store_nbr is not None:
        q = q.filter(SalesHistory.store_nbr == store_nbr)
    if start:
        q = q.filter(SalesHistory.date >= start)
    if end:
        q = q.filter(SalesHistory.date <= end)

    rows = q.group_by(SalesHistory.family).order_by(func.sum(SalesHistory.sales).desc()).all()

    return [
        SalesSummaryItem(
            family=r.family,
            total_sales=round(r.total_sales, 2),
            avg_daily_sales=round(r.avg_daily_sales, 2),
            days_on_promotion=int(r.days_on_promotion or 0),
        )
        for r in rows
    ]
