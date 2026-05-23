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
    SupplierUpdate,
)

router = APIRouter()


@router.get("", response_model=ProductPage)
def list_products(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    family: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    q = db.query(Product).filter(Product.business_id == current_user.business_id)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Product.sku_id.ilike(like)) | (Product.name.ilike(like))
        )
    if family:
        q = q.filter(Product.family == family)
    if is_active is not None:
        q = q.filter(Product.is_active.is_(is_active))

    total = q.count()
    total_active = db.query(Product).filter(
        Product.business_id == current_user.business_id,
        Product.is_active.is_(True),
    ).count()
    total_inactive = db.query(Product).filter(
        Product.business_id == current_user.business_id,
        Product.is_active.is_(False),
    ).count()
    total_families = db.query(sqlfunc.count(sqlfunc.distinct(Product.family))).filter(
        Product.business_id == current_user.business_id
    ).scalar() or 0

    items = q.order_by(Product.sku_id).offset((page - 1) * limit).limit(limit).all()
    return ProductPage(
        items=items,
        total=total,
        page=page,
        pages=max(1, ceil(total / limit)),
        total_active=total_active,
        total_inactive=total_inactive,
        total_families=total_families,
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id,
    ).first()
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
        Product.sku_id == payload.sku_id,
        Product.store_nbr == payload.store_nbr,
        Product.business_id == current_user.business_id,
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"SKU '{payload.sku_id}' ya existe en tienda {payload.store_nbr}")
    product = Product(**payload.model_dump(), business_id=current_user.business_id)
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
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=200)
def deactivate_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Soft delete — marca el producto como inactivo."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product.is_active = False
    db.commit()
    return {"ok": True, "product_id": product_id}


@router.patch("/{product_id}/supplier", response_model=ProductResponse)
def update_supplier(
    product_id: int,
    payload: SupplierUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product
