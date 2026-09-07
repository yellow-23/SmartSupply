from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.auth import require_admin
from app.database import get_db
from app.models.orm import (
    Business, IngestLog, Product, PurchaseOrder, SalesHistory, StockLevel, Store, User, UserBusiness,
)

router = APIRouter()


class AdminUserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    business_id: int | None
    business_name: str


class AdminBusinessOut(BaseModel):
    id: int
    name: str
    type: str | None
    onboarding_completed: bool
    user_count: int
    sales_rows: int


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    role: str | None = None


@router.get("/users", response_model=list[AdminUserOut])
def list_users(db: Session = Depends(get_db)):
    rows = db.query(User, Business.name).outerjoin(Business, Business.id == User.business_id).order_by(User.id).all()
    return [
        AdminUserOut(
            id=u.id, name=u.name, email=u.email, role=u.role, is_active=u.is_active,
            business_id=u.business_id, business_name=biz_name or "",
        )
        for u, biz_name in rows
    ]


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(user_id: int, body: AdminUserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.role is not None:
        if body.role not in ("platform_admin", "business_admin", "analyst"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rol invalido")
        user.role = body.role
    db.commit()
    db.refresh(user)
    biz = db.query(Business).filter(Business.id == user.business_id).first()
    return AdminUserOut(
        id=user.id, name=user.name, email=user.email, role=user.role, is_active=user.is_active,
        business_id=user.business_id, business_name=biz.name if biz else "",
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, current_user: Annotated[User, Depends(require_admin)], db: Session = Depends(get_db)):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes eliminar tu propia cuenta")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    db.query(UserBusiness).filter(UserBusiness.user_id == user_id).delete()
    db.delete(user)
    db.commit()


@router.get("/businesses", response_model=list[AdminBusinessOut])
def list_businesses(db: Session = Depends(get_db)):
    user_counts = dict(db.query(User.business_id, func.count(User.id)).group_by(User.business_id).all())
    sales_counts = dict(
        db.query(SalesHistory.business_id, func.count(SalesHistory.id)).group_by(SalesHistory.business_id).all()
    )
    businesses = db.query(Business).order_by(Business.id).all()
    return [
        AdminBusinessOut(
            id=b.id, name=b.name, type=b.type, onboarding_completed=b.onboarding_completed,
            user_count=user_counts.get(b.id, 0), sales_rows=sales_counts.get(b.id, 0),
        )
        for b in businesses
    ]


@router.delete("/businesses/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business(business_id: int, current_user: Annotated[User, Depends(require_admin)], db: Session = Depends(get_db)):
    if business_id == current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes eliminar tu propio negocio")
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")

    db.query(PurchaseOrder).filter(PurchaseOrder.business_id == business_id).delete()
    db.query(StockLevel).filter(StockLevel.business_id == business_id).delete()
    db.query(Product).filter(Product.business_id == business_id).delete()
    db.query(IngestLog).filter(IngestLog.business_id == business_id).delete()
    db.query(SalesHistory).filter(SalesHistory.business_id == business_id).delete()
    db.query(UserBusiness).filter(UserBusiness.business_id == business_id).delete(synchronize_session=False)
    db.query(Store).filter(Store.business_id == business_id).delete()
    # Los usuarios cuyo negocio "hogar" era este quedan sin negocio en vez de ser eliminados.
    db.query(User).filter(User.business_id == business_id).update(
        {User.business_id: None}, synchronize_session=False
    )
    db.delete(business)
    db.commit()
