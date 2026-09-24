from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import assert_business_access, assert_business_owner, get_current_user
from app.database import get_db
from app.models.orm import IngestLog, SalesHistory, Store, User, UserBusiness
from app.models.schemas import (
    SalesPoint,
    SalesRecordResponse,
    SalesRecordUpdate,
    SalesSummaryItem,
    StoreResponse,
)
import pandas as pd

from app.services.forecast_service import _BENCHMARK_BUSINESS_ID, _CSV_PATH, invalidate_business_cache

router = APIRouter()


def _effective_sales(
    db: Session,
    business_id: int,
    family: Optional[str] = None,
    store_nbr: Optional[int] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
):
    """Filas vigentes de sales_history: solo cargas activas y, si dos cargas cubren el mismo
    (tienda, familia, dia), gana la mas reciente (mayor ingest_id). Misma regla que forecast_service."""
    q = (
        db.query(SalesHistory)
        .join(IngestLog, IngestLog.id == SalesHistory.ingest_id)
        .filter(SalesHistory.business_id == business_id, IngestLog.status == "active")
    )
    if family is not None:
        q = q.filter(SalesHistory.family == family)
    if store_nbr is not None:
        q = q.filter(SalesHistory.store_nbr == store_nbr)
    if start:
        q = q.filter(SalesHistory.date >= start)
    if end:
        q = q.filter(SalesHistory.date <= end)
    return (
        q.distinct(SalesHistory.store_nbr, SalesHistory.family, SalesHistory.date)
        .order_by(SalesHistory.store_nbr, SalesHistory.family, SalesHistory.date, SalesHistory.ingest_id.desc())
        .subquery()
    )


@router.get("/date-range")
def get_date_range(
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int = Query(..., description="ID del negocio"),
    db: Session = Depends(get_db),
):
    """
    Retorna el rango de fechas disponible para un negocio (solo cargas activas).
    Usar antes de llamar a /history o /summary para saber que fechas tiene el negocio.
    """
    assert_business_access(db, current_user, business_id)
    eff = _effective_sales(db, business_id)
    row = db.query(func.min(eff.c.date).label("start"), func.max(eff.c.date).label("end")).first()

    if not row.start:
        raise HTTPException(status_code=404, detail=f"No hay datos para el negocio {business_id}")

    return {"business_id": business_id, "start": row.start, "end": row.end}


@router.get("/stores", response_model=list[StoreResponse])
def list_stores(
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int = Query(..., description="ID del negocio"),
    db: Session = Depends(get_db),
):
    """Lista las tiendas registradas de un negocio."""
    assert_business_access(db, current_user, business_id)
    return db.query(Store).filter(Store.business_id == business_id).order_by(Store.store_nbr).all()


@router.get("/stores/{store_nbr}", response_model=StoreResponse)
def get_store(
    store_nbr: int,
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int = Query(...),
    db: Session = Depends(get_db),
):
    assert_business_access(db, current_user, business_id)
    store = db.query(Store).filter(
        Store.store_nbr == store_nbr,
        Store.business_id == business_id,
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail=f"Tienda {store_nbr} no encontrada")
    return store


@router.get("/families")
def list_families(
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int = Query(..., description="ID del negocio"),
    db: Session = Depends(get_db),
):
    """Lista las categorias de productos que tiene un negocio en su historial (cargas activas)."""
    assert_business_access(db, current_user, business_id)
    eff = _effective_sales(db, business_id)
    rows = db.query(eff.c.family).distinct().order_by(eff.c.family).all()
    return [r.family for r in rows]


@router.get("/history", response_model=list[SalesPoint])
def get_sales_history(
    current_user: Annotated[User, Depends(get_current_user)],
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
    business_id=1 lee el dataset de referencia Favorita (CU-27).
    """
    if business_id == _BENCHMARK_BUSINESS_ID:
        df = pd.read_csv(_CSV_PATH, parse_dates=["date"])
        df = df[(df["family"] == family) & (df["store_nbr"] == (store_nbr or 1))]
        if start:
            df = df[df["date"].dt.date >= start]
        if end:
            df = df[df["date"].dt.date <= end]
        return [SalesPoint(date=r.date.date(), sales=r.sales, onpromotion=0) for r in df.itertuples()]
    assert_business_access(db, current_user, business_id)
    eff = _effective_sales(db, business_id, family, store_nbr, start, end)
    rows = db.query(eff.c.date, eff.c.sales, eff.c.onpromotion).order_by(eff.c.date).all()
    return [SalesPoint(date=r.date, sales=r.sales, onpromotion=r.onpromotion) for r in rows]


@router.get("/summary", response_model=list[SalesSummaryItem])
def get_sales_summary(
    current_user: Annotated[User, Depends(get_current_user)],
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
    assert_business_access(db, current_user, business_id)
    eff = _effective_sales(db, business_id, None, store_nbr, start, end)
    total = func.sum(eff.c.sales)
    rows = (
        db.query(
            eff.c.family,
            total.label("total_sales"),
            func.avg(eff.c.sales).label("avg_daily_sales"),
            func.sum(eff.c.onpromotion).label("days_on_promotion"),
        )
        .group_by(eff.c.family)
        .order_by(total.desc())
        .all()
    )

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
    assert_business_owner(db, current_user, rec.business_id)
    business_id = rec.business_id
    db.delete(rec)
    db.commit()
    invalidate_business_cache(business_id)
