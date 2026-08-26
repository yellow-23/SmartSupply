from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import SalesHistory, Store, User, UserBusiness
from app.models.schemas import (
    SalesPoint,
    SalesRecordResponse,
    SalesRecordUpdate,
    SalesSummaryItem,
    StoreResponse,
)
from app.services.forecast_service import invalidate_business_cache

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


def _assert_record_owner(db: Session, record: SalesHistory, user: User):
    has_access = db.query(UserBusiness).filter(
        UserBusiness.user_id == user.id,
        UserBusiness.business_id == record.business_id,
    ).first()
    if not has_access:
        raise HTTPException(status_code=403, detail="Este registro no te pertenece")


@router.patch("/record/{record_id}", response_model=SalesRecordResponse)
def update_record(
    record_id: int,
    body: SalesRecordUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Edita una fila de sales_history (venta, fecha, familia, promo)."""
    rec = db.query(SalesHistory).filter(SalesHistory.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Registro {record_id} no encontrado")
    _assert_record_owner(db, rec, current_user)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rec, field, value)
    db.commit()
    invalidate_business_cache(rec.business_id)
    db.refresh(rec)
    return rec


@router.delete("/record/{record_id}", status_code=204)
def delete_record(
    record_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Elimina una fila individual de sales_history."""
    rec = db.query(SalesHistory).filter(SalesHistory.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Registro {record_id} no encontrado")
    _assert_record_owner(db, rec, current_user)
    business_id = rec.business_id
    db.delete(rec)
    db.commit()
    invalidate_business_cache(business_id)
