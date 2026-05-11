"""
Ingest API — SmartSupply
Endpoint para ingesta de datos via IA.
El usuario sube cualquier archivo (imagen, Excel, PDF) y Claude extrae
los registros de ventas, los normaliza y los carga a sales_history.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import SalesHistory
from app.models.schemas import IngestConfirm, IngestPreview, IngestResponse
from app.services.ingest_service import (
    SUPPORTED_EXCEL_TYPES,
    SUPPORTED_IMAGE_TYPES,
    IngestService,
)

router = APIRouter()
service = IngestService()


@router.post("/preview", response_model=IngestPreview)
async def preview_ingest(file: UploadFile = File(...)):
    """
    Paso 1: Sube un archivo y Claude extrae los datos de ventas.
    Devuelve un preview para que el usuario revise antes de confirmar la carga.

    Formatos soportados:
    - Imagenes (JPG, PNG, WEBP): fotos de cuadernos, pizarras, tickets
    - Excel / CSV: planillas de ventas
    - PDF: reportes o facturas escaneadas
    """
    content_type = file.content_type or ""
    file_bytes = await file.read()

    if content_type in SUPPORTED_IMAGE_TYPES:
        return service.preview_from_image(file_bytes, content_type)
    elif content_type in SUPPORTED_EXCEL_TYPES or file.filename.endswith((".xlsx", ".xls", ".csv")):
        return service.preview_from_excel(file_bytes, file.filename)
    elif content_type == "application/pdf" or file.filename.endswith(".pdf"):
        return service.preview_from_pdf(file_bytes)
    else:
        raise HTTPException(
            status_code=415,
            detail=f"Formato no soportado: {content_type}. Usa JPG, PNG, WEBP, Excel, CSV o PDF.",
        )


@router.post("/confirm", response_model=IngestResponse)
def confirm_ingest(body: IngestConfirm, db: Session = Depends(get_db)):
    """
    Paso 2: Confirma la carga de los registros extraidos por Claude a sales_history.
    El usuario debe haber revisado el preview primero.
    """
    if not body.records:
        raise HTTPException(status_code=400, detail="No hay registros para cargar.")

    loaded = 0
    for record in body.records:
        existing = (
            db.query(SalesHistory)
            .filter(
                SalesHistory.business_id == body.business_id,
                SalesHistory.store_nbr == body.store_nbr,
                SalesHistory.date == record.date,
                SalesHistory.family == record.family,
            )
            .first()
        )
        if existing:
            existing.sales = record.sales
            existing.onpromotion = record.onpromotion
        else:
            db.add(SalesHistory(
                business_id=body.business_id,
                store_nbr=body.store_nbr,
                date=record.date,
                family=record.family,
                sales=record.sales,
                onpromotion=record.onpromotion,
            ))
        loaded += 1

    db.commit()

    dates = [r.date for r in body.records]
    return IngestResponse(
        store_nbr=body.store_nbr,
        records_loaded=loaded,
        families=sorted(set(r.family for r in body.records)),
        date_range_start=min(dates),
        date_range_end=max(dates),
    )
