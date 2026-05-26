"""
Gestion de cargas (ingest_log): listar, ver detalle, revertir y eliminar.
Cada carga agrupa las filas de sales_history que se insertaron juntas.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import Business, IngestLog, SalesHistory, User, UserBusiness
from app.models.schemas import IngestLogResponse, SalesRecordResponse

router = APIRouter()


def _assert_owner(db: Session, business_id: int, user: User):
    if not db.query(Business).filter(Business.id == business_id).first():
        raise HTTPException(status_code=404, detail=f"Negocio {business_id} no encontrado")
    if not db.query(UserBusiness).filter(
        UserBusiness.user_id == user.id,
        UserBusiness.business_id == business_id,
    ).first():
        raise HTTPException(status_code=403, detail="No tienes acceso a este negocio")


@router.get("", response_model=list[IngestLogResponse])
def list_ingests(
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int = Query(...),
    store_nbr: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Lista las cargas de un negocio (opcionalmente filtradas por ubicacion)."""
    _assert_owner(db, business_id, current_user)
    q = db.query(IngestLog).filter(IngestLog.business_id == business_id)
    if store_nbr is not None:
        q = q.filter(IngestLog.store_nbr == store_nbr)
    logs = q.order_by(IngestLog.created_at.desc()).all()

    names = {u.id: u.name for u in db.query(User).all()}
    out = []
    for log in logs:
        item = IngestLogResponse.model_validate(log)
        item.uploader_name = names.get(log.user_id)
        out.append(item)
    return out


@router.get("/{ingest_id}", response_model=list[SalesRecordResponse])
def get_ingest_records(
    ingest_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Devuelve las filas de sales_history que vinieron de esta carga."""
    log = db.query(IngestLog).filter(IngestLog.id == ingest_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"Carga {ingest_id} no encontrada")
    _assert_owner(db, log.business_id, current_user)
    return (
        db.query(SalesHistory)
        .filter(SalesHistory.ingest_id == ingest_id)
        .order_by(SalesHistory.date, SalesHistory.family)
        .all()
    )


@router.post("/{ingest_id}/revert", response_model=IngestLogResponse)
def revert_ingest(
    ingest_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Marca la carga como 'reverted'. Las filas quedan pero salen del calculo."""
    log = db.query(IngestLog).filter(IngestLog.id == ingest_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"Carga {ingest_id} no encontrada")
    _assert_owner(db, log.business_id, current_user)
    log.status = "reverted"
    db.commit()
    db.refresh(log)
    item = IngestLogResponse.model_validate(log)
    item.uploader_name = (db.query(User).filter(User.id == log.user_id).first() or User()).name
    return item


@router.delete("/{ingest_id}", status_code=204)
def delete_ingest(
    ingest_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Elimina la carga y todas sus filas de sales_history (hard delete)."""
    log = db.query(IngestLog).filter(IngestLog.id == ingest_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"Carga {ingest_id} no encontrada")
    _assert_owner(db, log.business_id, current_user)
    db.query(SalesHistory).filter(SalesHistory.ingest_id == ingest_id).delete()
    db.delete(log)
    db.commit()
