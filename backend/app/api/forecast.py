from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import SalesHistory, Store, User
from app.models.schemas import ForecastRequest, ForecastResponse
from app.services.forecast_service import (
    ForecastService,
    InsufficientDataError,
    _MIN_DAYS,
    _cache,
    _cache_lock,
)

router = APIRouter()
service = ForecastService()


def _insufficient_data_response(err: InsufficientDataError) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail={
            "code": "insufficient_data",
            "days_available": err.days_available,
            "days_required": err.days_required,
            "message": (
                f"Necesitas al menos {err.days_required} días de historial para predecir. "
                f"Llevas {err.days_available} días."
            ),
        },
    )


@router.post("/predict", response_model=ForecastResponse)
async def predict_demand(
    request: ForecastRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Genera una predicción de demanda usando el motor AMS, scoped al business del usuario."""
    try:
        return service.predict(
            db=db,
            business_id=current_user.business_id,
            sku_id=request.sku_id,
            store_nbr=request.store_nbr,
            horizon_days=request.horizon_days,
            model=request.model,
        )
    except InsufficientDataError as e:
        raise _insufficient_data_response(e)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")


@router.get("/options")
def get_forecast_options(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Familias y tiendas que el usuario actual tiene en sales_history.
    Sirve para poblar dropdowns sin asumir nombres ni números.
    """
    families = [
        r[0]
        for r in (
            db.query(SalesHistory.family)
            .filter(SalesHistory.business_id == current_user.business_id)
            .distinct()
            .order_by(SalesHistory.family)
            .all()
        )
    ]

    store_rows = (
        db.query(
            SalesHistory.store_nbr,
            func.count(func.distinct(SalesHistory.date)).label("days_available"),
        )
        .filter(SalesHistory.business_id == current_user.business_id)
        .group_by(SalesHistory.store_nbr)
        .all()
    )

    store_names = {
        s.store_nbr: s.name
        for s in db.query(Store)
        .filter(Store.business_id == current_user.business_id)
        .all()
    }

    stores = [
        {
            "store_nbr": row.store_nbr,
            "name": store_names.get(row.store_nbr) or f"Tienda {row.store_nbr}",
            "days_available": int(row.days_available),
        }
        for row in store_rows
    ]

    return {"families": families, "stores": stores, "days_required": _MIN_DAYS}


@router.delete("/cache", status_code=200)
def clear_forecast_cache(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Invalida el cache de predicciones en memoria. Útil tras reentrenar modelos."""
    with _cache_lock:
        count = len(_cache)
        _cache.clear()
    return {"cleared": count}


@router.get("/{sku_id}/export")
async def export_forecast_pdf(
    sku_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    store_nbr: int = Query(default=1, description="Número de tienda"),
    horizon_days: int = Query(default=14, ge=7, le=30, description="Días a predecir"),
    model: str = Query(default="auto", description="Modelo o 'auto' para AMS"),
    db: Session = Depends(get_db),
):
    """Genera un PDF con el resumen y las predicciones del forecast para el SKU indicado."""
    try:
        result = service.predict(
            db=db,
            business_id=current_user.business_id,
            sku_id=sku_id,
            store_nbr=store_nbr,
            horizon_days=horizon_days,
            model=model,
        )
    except InsufficientDataError as e:
        raise _insufficient_data_response(e)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")

    unit_label = "CLP" if result.sales_unit == "CLP" else "unidades"
    total = sum(p.predicted_sales for p in result.predictions)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "SmartSupply - Reporte de Prediccion de Demanda", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Negocio: {current_user.business_id}   Tienda: {result.store_nbr}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Producto (familia): {result.sku_id}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Horizonte: {result.horizon_days} dias   Generado: {result.generated_at.strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Modelo ganador: {result.model_used.upper()}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    if result.mape_validation is not None:
        pdf.cell(0, 8, f"WAPE en validacion: {result.mape_validation:.2f}%", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Total estimado del periodo: {total:,.1f} {unit_label}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Promedio diario: {total / max(len(result.predictions), 1):,.1f} {unit_label}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Prediccion por dia", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    with pdf.table(col_widths=(40, 40, 40, 40), text_align="CENTER") as table:
        header = table.row()
        for col in ("Fecha", f"Prediccion ({unit_label})", "Minimo", "Maximo"):
            header.cell(col)
        for point in result.predictions:
            row = table.row()
            row.cell(point.date.strftime("%Y-%m-%d"))
            row.cell(f"{point.predicted_sales:,.1f}")
            row.cell(f"{point.lower_bound:,.1f}" if point.lower_bound is not None else "-")
            row.cell(f"{point.upper_bound:,.1f}" if point.upper_bound is not None else "-")

    buf = BytesIO(bytes(pdf.output()))
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=forecast_{sku_id}_{result.store_nbr}.pdf"},
    )


@router.get("/models")
async def list_available_models():
    """Lista los modelos de forecasting disponibles."""
    return {
        "models": ["arima", "prophet", "xgboost", "lstm"],
        "default": "auto",
        "metric": "WAPE (Weighted Absolute Percentage Error)",
        "cv_available": True,
        "description": (
            "El modo 'auto' usa el Automated Model Selector (AMS) que elige "
            "el mejor modelo por SKU según WAPE en validación (split 70/15/15)."
        ),
    }


@router.get("/{sku_id}", response_model=ForecastResponse)
async def get_forecast_for_sku(
    sku_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    store_nbr: int = Query(default=1, description="Número de tienda"),
    horizon_days: int = Query(default=14, ge=7, le=30, description="Días a predecir"),
    model: str = Query(default="auto", description="Modelo o 'auto' para AMS"),
    db: Session = Depends(get_db),
):
    """Predicción rápida GET para el SKU indicado, scoped al business del usuario."""
    try:
        return service.predict(
            db=db,
            business_id=current_user.business_id,
            sku_id=sku_id,
            store_nbr=store_nbr,
            horizon_days=horizon_days,
            model=model,
        )
    except InsufficientDataError as e:
        raise _insufficient_data_response(e)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")
