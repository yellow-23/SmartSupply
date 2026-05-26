"""
Ingest API — SmartSupply
Endpoint para ingesta de datos via IA.
El usuario sube cualquier archivo (imagen, Excel, PDF) y Claude extrae
los registros de ventas, los normaliza y los carga a sales_history.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import Business, Product, SalesHistory, StockLevel, User, IngestLog
from app.models.schemas import IngestConfirm, IngestPreview, IngestResponse, IngestChatRequest, IngestChatResponse
from app.services.ingest_service import (
    SUPPORTED_EXCEL_TYPES,
    SUPPORTED_IMAGE_TYPES,
    IngestService,
)
from app.services.ingest_validator import filter_loadable_records

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
def confirm_ingest(
    body: IngestConfirm,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Paso 2: confirma la carga. Crea un ingest_log y agrega las filas con ese
    ingest_id SIN sobrescribir cargas previas (cada carga queda separada).
    """
    data_type = body.data_type or "sales"

    # ── Stock snapshot ──────────────────────────────────────────────────────────
    if data_type == "stock":
        if not body.stock_records:
            raise HTTPException(status_code=400, detail="No hay registros de stock para cargar.")
        for rec in body.stock_records:
            existing = db.query(StockLevel).filter(
                StockLevel.business_id == body.business_id,
                StockLevel.store_nbr == body.store_nbr,
                StockLevel.family == rec.family,
            ).first()
            if existing:
                existing.quantity = rec.quantity
            else:
                db.add(StockLevel(
                    business_id=body.business_id,
                    store_nbr=body.store_nbr,
                    family=rec.family,
                    quantity=rec.quantity,
                ))
        db.commit()
        families = sorted(set(r.family for r in body.stock_records))
        from datetime import date as date_type
        today = date_type.today()
        return IngestResponse(
            store_nbr=body.store_nbr,
            records_loaded=len(body.stock_records),
            families=families,
            date_range_start=today,
            date_range_end=today,
        )

    # ── Products catalog ────────────────────────────────────────────────────────
    if data_type == "products":
        if not body.product_records:
            raise HTTPException(status_code=400, detail="No hay registros de productos para cargar.")
        for rec in body.product_records:
            existing = db.query(Product).filter(
                Product.business_id == body.business_id,
                Product.store_nbr == body.store_nbr,
                Product.family == rec.family,
            ).first()
            if existing:
                if rec.unit_cost is not None:
                    existing.unit_cost = rec.unit_cost
                if rec.order_cost is not None:
                    existing.order_cost = rec.order_cost
                if rec.lead_time_days is not None:
                    existing.lead_time_days = rec.lead_time_days
                if rec.moq is not None:
                    existing.moq = rec.moq
            else:
                kwargs: dict = {
                    "business_id": body.business_id,
                    "store_nbr": body.store_nbr,
                    "family": rec.family,
                }
                if rec.unit_cost is not None:
                    kwargs["unit_cost"] = rec.unit_cost
                if rec.order_cost is not None:
                    kwargs["order_cost"] = rec.order_cost
                if rec.lead_time_days is not None:
                    kwargs["lead_time_days"] = rec.lead_time_days
                if rec.moq is not None:
                    kwargs["moq"] = rec.moq
                db.add(Product(**kwargs))
        db.commit()
        families = sorted(set(r.family for r in body.product_records))
        from datetime import date as date_type
        today = date_type.today()
        return IngestResponse(
            store_nbr=body.store_nbr,
            records_loaded=len(body.product_records),
            families=families,
            date_range_start=today,
            date_range_end=today,
        )

    # ── Sales (default) ─────────────────────────────────────────────────────────
    if not body.records:
        raise HTTPException(status_code=400, detail="No hay registros para cargar.")

    loadable = filter_loadable_records(body.records)
    if not loadable:
        raise HTTPException(
            status_code=400,
            detail="Ningun registro es cargable (fechas futuras o ventas en cero).",
        )

    dates = [r.date for r in loadable]
    families = sorted(set(r.family for r in loadable))

    log = IngestLog(
        business_id=body.business_id,
        store_nbr=body.store_nbr,
        user_id=current_user.id,
        filename=body.filename,
        file_type=body.file_type,
        records_loaded=len(loadable),
        sales_unit=body.sales_unit,
        date_range_start=min(dates),
        date_range_end=max(dates),
        families=families,
        status="active",
    )
    db.add(log)
    db.flush()  # asigna log.id sin cerrar la transaccion

    for record in loadable:
        db.add(SalesHistory(
            business_id=body.business_id,
            store_nbr=body.store_nbr,
            date=record.date,
            family=record.family,
            sales=record.sales,
            onpromotion=record.onpromotion,
            sales_unit=body.sales_unit,
            ingest_id=log.id,
        ))

    for family in families:
        exists = db.query(Product).filter(
            Product.business_id == body.business_id,
            Product.family == family,
            Product.store_nbr == body.store_nbr,
        ).first()
        if not exists:
            db.add(Product(
                business_id=body.business_id,
                family=family,
                store_nbr=body.store_nbr,
            ))

    db.commit()

    return IngestResponse(
        store_nbr=body.store_nbr,
        records_loaded=len(loadable),
        families=families,
        date_range_start=min(dates),
        date_range_end=max(dates),
    )


@router.post("/chat", response_model=IngestChatResponse)
def ingest_chat(
    body: IngestChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Stocky — asistente de ingesta. Aclara dudas sobre los datos extraídos."""
    biz = db.query(Business).filter(Business.id == current_user.business_id).first()
    business_name = biz.name if biz else ""

    existing = (
        db.query(IngestLog)
        .filter(IngestLog.business_id == current_user.business_id, IngestLog.status == "active")
        .order_by(IngestLog.created_at.desc())
        .limit(10)
        .all()
    )
    loads_summary = "; ".join(
        f"ubicacion {l.store_nbr}: {', '.join(l.families or [])} ({l.date_range_start} a {l.date_range_end})"
        for l in existing
    ) or "ninguna carga previa"

    reply, trigger_confirm = service.chat(body.messages, body.preview_summary, business_name, loads_summary)
    return IngestChatResponse(reply=reply, trigger_confirm=trigger_confirm)
