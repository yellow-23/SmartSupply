from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import assert_business_owner, get_current_user
from app.services.rut import normalize_rut
from app.database import get_db
from app.models.orm import Business, Store, User, UserBusiness
from app.models.schemas import BusinessCreate, BusinessResponse, BusinessUpdate, StoreCreate, StoreResponse, StoreUpdate


def _with_role(biz: Business, role: str | None) -> BusinessResponse:
    out = BusinessResponse.model_validate(biz)
    out.my_role = role
    return out

router = APIRouter()


def _clean(v: str | None) -> str | None:
    return (v or "").strip() or None


def _checked_rut(db: Session, rut: str | None, exclude_id: int | None = None) -> str | None:
    """Valida el DV, lo deja en formato canonico y verifica que ningun otro negocio lo use."""
    try:
        rut = normalize_rut(rut)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if rut:
        q = db.query(Business).filter(Business.rut == rut)
        if exclude_id is not None:
            q = q.filter(Business.id != exclude_id)
        if q.first():
            raise HTTPException(status_code=409, detail=f"Ya existe un negocio con RUT {rut}")
    return rut


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
    """Lista los negocios a los que el usuario pertenece, con su rol en cada uno."""
    rows = (
        db.query(Business, UserBusiness.role)
        .join(UserBusiness, UserBusiness.business_id == Business.id)
        .filter(UserBusiness.user_id == current_user.id)
        .order_by(Business.id)
        .all()
    )
    return [_with_role(biz, role) for biz, role in rows]


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(
    business_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail=f"Negocio {business_id} no encontrado")
    membership = db.query(UserBusiness).filter(
        UserBusiness.user_id == current_user.id, UserBusiness.business_id == business_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No tienes acceso a este negocio")
    return _with_role(biz, membership.role)


@router.post("", response_model=BusinessResponse, status_code=201)
def create_business(
    body: BusinessCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Crea un negocio y agrega al usuario como owner en user_businesses."""
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="El nombre del negocio no puede estar vacío")
    rut = _checked_rut(db, body.rut)
    biz = Business(
        name=name, rut=rut, city=_clean(body.city), address=_clean(body.address),
        phone=_clean(body.phone), email=_clean(body.email), type=body.type,
        owner_user_id=current_user.id,
    )
    db.add(biz)
    db.flush()
    db.add(UserBusiness(user_id=current_user.id, business_id=biz.id, role="owner"))
    # Igual que el autoprovision: todo negocio nace con una ubicacion para poder recibir cargas.
    db.add(Store(business_id=biz.id, store_nbr=1, name="Tienda Principal", city=_clean(body.city)))
    db.commit()
    db.refresh(biz)
    return _with_role(biz, "owner")


@router.patch("/{business_id}", response_model=BusinessResponse)
def update_business(
    business_id: int,
    body: BusinessUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Edita los datos del negocio (solo el dueño). Campos vacios se borran; los no enviados no cambian."""
    assert_business_owner(db, current_user, business_id)
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail=f"Negocio {business_id} no encontrado")
    fields = body.model_dump(exclude_unset=True)
    if "name" in fields:
        if not _clean(body.name):
            raise HTTPException(status_code=422, detail="El nombre del negocio no puede estar vacío")
        biz.name = _clean(body.name)
    if "rut" in fields:
        biz.rut = _checked_rut(db, body.rut, exclude_id=business_id)
    for f in ("city", "address", "phone", "email"):
        if f in fields:
            setattr(biz, f, _clean(fields[f]))
    if body.type:
        biz.type = body.type
    db.commit()
    db.refresh(biz)
    role = db.query(UserBusiness.role).filter(
        UserBusiness.user_id == current_user.id, UserBusiness.business_id == business_id,
    ).scalar()
    return _with_role(biz, role)


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


@router.post("/{business_id}/stores", response_model=StoreResponse, status_code=201)
def create_business_store(
    business_id: int,
    body: StoreCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Agrega una ubicacion (sucursal) al negocio con el siguiente store_nbr libre."""
    assert_business_owner(db, current_user, business_id)
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="El nombre de la ubicación no puede estar vacío")
    next_nbr = (db.query(func.max(Store.store_nbr)).filter(Store.business_id == business_id).scalar() or 0) + 1
    store = Store(business_id=business_id, store_nbr=next_nbr, name=name, city=body.city)
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.patch("/{business_id}/stores/{store_nbr}", response_model=StoreResponse)
def update_business_store(
    business_id: int,
    store_nbr: int,
    body: StoreUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Renombra una ubicacion o cambia su ciudad (solo el dueño)."""
    assert_business_owner(db, current_user, business_id)
    store = db.query(Store).filter(Store.business_id == business_id, Store.store_nbr == store_nbr).first()
    if not store:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    fields = body.model_dump(exclude_unset=True)
    if "name" in fields:
        if not _clean(body.name):
            raise HTTPException(status_code=422, detail="El nombre de la ubicación no puede estar vacío")
        store.name = _clean(body.name)
    if "city" in fields:
        store.city = _clean(body.city)
    db.commit()
    db.refresh(store)
    return store
