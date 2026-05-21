from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import Product, User
from app.models.schemas import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()


@router.get("/", response_model=list[ProductResponse])
def list_products(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    store_nbr: Optional[int] = Query(default=None),
    family: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
):
    q = db.query(Product).filter(Product.business_id == current_user.business_id)
    if store_nbr is not None:
        q = q.filter(Product.store_nbr == store_nbr)
    if family:
        q = q.filter(Product.family == family)
    if search:
        term = f"%{search}%"
        q = q.filter(Product.name.ilike(term) | Product.sku_id.ilike(term))
    return q.order_by(Product.family, Product.name).all()


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


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    exists = db.query(Product).filter(
        Product.sku_id == body.sku_id,
        Product.store_nbr == body.store_nbr,
        Product.business_id == current_user.business_id,
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"SKU '{body.sku_id}' ya existe en tienda {body.store_nbr}")

    product = Product(**body.model_dump(), business_id=current_user.business_id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    body: ProductUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
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
    db.delete(product)
    db.commit()
