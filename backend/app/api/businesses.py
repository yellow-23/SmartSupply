from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import Business
from app.models.schemas import BusinessCreate, BusinessResponse

router = APIRouter()


@router.get("/", response_model=list[BusinessResponse])
def list_businesses(db: Session = Depends(get_db)):
    """Lista todos los negocios registrados en el sistema."""
    return db.query(Business).order_by(Business.id).all()


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(business_id: int, db: Session = Depends(get_db)):
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail=f"Negocio {business_id} no encontrado")
    return biz


@router.post("/", response_model=BusinessResponse, status_code=201)
def create_business(body: BusinessCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo negocio (distribuidora, tienda, etc.).
    Cada negocio obtiene un business_id unico para aislar sus datos.
    """
    if body.rut:
        existing = db.query(Business).filter(Business.rut == body.rut).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Ya existe un negocio con RUT {body.rut}")

    biz = Business(name=body.name, rut=body.rut, city=body.city, type=body.type)
    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz
