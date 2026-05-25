from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import Business, Store, User
from app.models.schemas import BusinessCreate, BusinessResponse, StoreResponse

router = APIRouter()


def _can_access(biz: Business, user: User) -> bool:
    """Un usuario accede a un negocio si lo creo (owner) o si es su negocio asignado.
    Esto cubre negocios compartidos por varios usuarios (ej: la demo del equipo)."""
    return biz.owner_user_id in (None, user.id) or biz.id == user.business_id


@router.get("", response_model=list[BusinessResponse])
def list_businesses(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Lista los negocios del usuario: los que creo + su negocio asignado."""
    return (
        db.query(Business)
        .filter(
            (Business.owner_user_id == current_user.id)
            | (Business.id == current_user.business_id)
        )
        .order_by(Business.id)
        .all()
    )


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(
    business_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail=f"Negocio {business_id} no encontrado")
    if not _can_access(biz, current_user):
        raise HTTPException(status_code=403, detail="Este negocio no te pertenece")
    return biz


@router.post("", response_model=BusinessResponse, status_code=201)
def create_business(
    body: BusinessCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Crea un negocio y lo asocia al usuario actual como owner."""
    if body.rut:
        existing = db.query(Business).filter(Business.rut == body.rut).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Ya existe un negocio con RUT {body.rut}")

    biz = Business(
        name=body.name, rut=body.rut, city=body.city, type=body.type,
        owner_user_id=current_user.id,
    )
    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz


@router.get("/{business_id}/stores", response_model=list[StoreResponse])
def list_business_stores(
    business_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Ubicaciones (tiendas) de un negocio."""
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail=f"Negocio {business_id} no encontrado")
    if not _can_access(biz, current_user):
        raise HTTPException(status_code=403, detail="Este negocio no te pertenece")
    return (
        db.query(Store)
        .filter(Store.business_id == business_id)
        .order_by(Store.store_nbr)
        .all()
    )
