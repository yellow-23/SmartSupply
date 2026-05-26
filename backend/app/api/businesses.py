from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import Business, Store, User, UserBusiness
from app.models.schemas import BusinessCreate, BusinessResponse, StoreResponse

router = APIRouter()


def _can_access(db: Session, business_id: int, user: User) -> bool:
    return db.query(UserBusiness).filter(
        UserBusiness.user_id == user.id,
        UserBusiness.business_id == business_id,
    ).first() is not None


@router.get("", response_model=list[BusinessResponse])
def list_businesses(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Lista los negocios a los que el usuario pertenece."""
    return (
        db.query(Business)
        .join(UserBusiness, UserBusiness.business_id == Business.id)
        .filter(UserBusiness.user_id == current_user.id)
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
    if not _can_access(db, business_id, current_user):
        raise HTTPException(status_code=403, detail="No tienes acceso a este negocio")
    return biz


@router.post("", response_model=BusinessResponse, status_code=201)
def create_business(
    body: BusinessCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Crea un negocio y agrega al usuario como owner en user_businesses."""
    if body.rut:
        existing = db.query(Business).filter(Business.rut == body.rut).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Ya existe un negocio con RUT {body.rut}")

    biz = Business(
        name=body.name, rut=body.rut, city=body.city, type=body.type,
        owner_user_id=current_user.id,
    )
    db.add(biz)
    db.flush()
    db.add(UserBusiness(user_id=current_user.id, business_id=biz.id, role="owner"))
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
    if not _can_access(db, business_id, current_user):
        raise HTTPException(status_code=403, detail="No tienes acceso a este negocio")
    return (
        db.query(Store)
        .filter(Store.business_id == business_id)
        .order_by(Store.store_nbr)
        .all()
    )
