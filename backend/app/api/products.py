from math import ceil
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import Product, User
from app.models.schemas import (
    ProductCreate,
    ProductPage,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter()


@router.get("", response_model=ProductPage)
def list_products(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    business_id: Optional[int] = None,
    store_nbr: Optional[int] = None,
    family: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    effective_business_id = business_id or current_user.business_id
    q = db.query(Product).filter(Product.business_id == effective_business_id)
    if store_nbr is not None:
        q = q.filter(Product.store_nbr == store_nbr)
    if family:
        q = q.filter(Product.family == family)

    total = q.count()
    total_families = (
        db.query(sqlfunc.count(sqlfunc.distinct(Product.family)))
        .filter(Product.business_id == effective_business_id)
        .scalar()
        or 0
    )

    items = q.order_by(Product.family).offset((page - 1) * limit).limit(limit).all()
    return ProductPage(
        items=items,
        total=total,
        page=page,
        pages=max(1, ceil(total / limit)),
        total_families=total_families,
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    payload: ProductCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    exists = db.query(Product).filter(
        Product.business_id == payload.business_id,
        Product.store_nbr == payload.store_nbr,
        Product.family == payload.family,
    ).first()
    if exists:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe configuración para '{payload.family}' en tienda {payload.store_nbr}",
        )
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(product)
    db.commit()
