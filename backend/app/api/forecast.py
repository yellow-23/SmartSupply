from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, resolve_business_id
from app.database import get_db
from app.models.orm import Business, Product, SalesHistory, Store, User
from app.models.schemas import ForecastRequest, ForecastResponse
from app.services.forecast_export import forecast_file
from app.services.forecast_service import (
    ForecastService,
    InsufficientDataError,
    _BENCHMARK_BUSINESS_ID,
    _CSV_PATH,
    _MIN_DAYS,
    _cache,
    _cache_lock,
    get_forecast_accuracy,
)

router = APIRouter()
service = ForecastService()


def export_names(db: Session, business_id: int, store_nbr: int) -> tuple[str, str]:
    """(nombre del negocio, nombre de la ubicacion) para el encabezado de los archivos exportados."""
    if business_id == _BENCHMARK_BUSINESS_ID:
        return "Dataset de referencia (Favorita)", f"Tienda {store_nbr}"
    biz = db.query(Business).filter(Business.id == business_id).first()
    store = db.query(Store).filter(Store.business_id == business_id, Store.store_nbr == store_nbr).first()
    label = (store.name if store and store.name else f"Ubicación {store_nbr}") + (f" - {store.city}" if store and store.city else "")
    return (biz.name if biz else str(business_id)), label


def _resolve(db: Session, user: User, business_id: int | None) -> int:
    """business_id=1 es el dataset de referencia Favorita (CU-27): de solo lectura, abierto a todo usuario."""
    if business_id == _BENCHMARK_BUSINESS_ID:
        return business_id
    return resolve_business_id(db, user, business_id)


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
def predict_demand(
    request: ForecastRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int | None = Query(default=None, description="Negocio activo; 1 = dataset de referencia"),
    db: Session = Depends(get_db),
):
    """Genera una predicción de demanda usando el motor AMS, scoped al negocio activo."""
    bid = _resolve(db, current_user, business_id)
    try:
        return service.predict(
            db=db,
            business_id=bid,
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
    business_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Familias y tiendas que el negocio tiene en sales_history.
    Sirve para poblar dropdowns sin asumir nombres ni números.
    """
    bid = _resolve(db, current_user, business_id)
    if bid == _BENCHMARK_BUSINESS_ID:
        df = pd.read_csv(_CSV_PATH, usecols=["date", "family"])
        return {
            "families": sorted(df["family"].unique().tolist()),
            "categories": {},
            "stores": [{"store_nbr": 1, "name": "Favorita - Tienda 1", "days_available": int(df["date"].nunique())}],
            "days_required": _MIN_DAYS,
        }
    families = [
        r[0]
        for r in (
            db.query(SalesHistory.family)
            .filter(SalesHistory.business_id == bid)
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
        .filter(SalesHistory.business_id == bid)
        .group_by(SalesHistory.store_nbr)
        .all()
    )

    store_names = {
        s.store_nbr: s.name
        for s in db.query(Store)
        .filter(Store.business_id == bid)
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

    categories = {
        f: c for f, c in db.query(Product.family, Product.category)
        .filter(Product.business_id == bid, Product.category.isnot(None))
    }
    return {"families": families, "categories": categories, "stores": stores, "days_required": _MIN_DAYS}


@router.get("/accuracy")
def get_accuracy(
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int = Query(...),
    store_nbr: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Compara predicciones ya guardadas contra la venta real, por familia.
    Solo incluye fechas donde ya llego el dato real (no proyecciones a futuro)."""
    resolve_business_id(db, current_user, business_id)
    return get_forecast_accuracy(db, business_id, store_nbr)


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
def export_forecast_pdf(
    sku_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    store_nbr: int = Query(default=1, description="Número de tienda"),
    horizon_days: int = Query(default=14, ge=7, le=30, description="Días a predecir"),
    model: str = Query(default="auto", description="Modelo o 'auto' para AMS"),
    business_id: int | None = Query(default=None, description="Negocio activo; 1 = dataset de referencia"),
    db: Session = Depends(get_db),
):
    """Genera un PDF con la prediccion ya calculada (desde cache, sin re-entrenar)."""
    bid = _resolve(db, current_user, business_id)
    result = service.get_cached(bid, sku_id, store_nbr, horizon_days, model)
    if result is None:
        raise HTTPException(
            status_code=409,
            detail="No hay una predicción vigente para exportar. Genera la predicción primero.",
        )

    return forecast_file(result, sku_id, *export_names(db, bid, result.store_nbr), "pdf")


@router.post("/export")
def export_forecast(
    body: ForecastResponse,
    current_user: Annotated[User, Depends(get_current_user)],
    format: Literal["pdf", "xlsx"] = Query(default="pdf"),
    business_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Descarga la prediccion que el usuario esta viendo (la manda el navegador), sin depender del cache de 1 hora."""
    bid = _resolve(db, current_user, business_id)
    if not body.predictions:
        raise HTTPException(status_code=422, detail="La predicción no tiene días para exportar.")
    return forecast_file(body, body.sku_id, *export_names(db, bid, body.store_nbr), format)


@router.get("/models")
def list_available_models():
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
def get_forecast_for_sku(
    sku_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    store_nbr: int = Query(default=1, description="Número de tienda"),
    horizon_days: int = Query(default=14, ge=7, le=30, description="Días a predecir"),
    model: str = Query(default="auto", description="Modelo o 'auto' para AMS"),
    business_id: int | None = Query(default=None, description="Negocio activo; 1 = dataset de referencia"),
    db: Session = Depends(get_db),
):
    """Predicción rápida GET para el SKU indicado, scoped al negocio activo."""
    bid = _resolve(db, current_user, business_id)
    try:
        return service.predict(
            db=db,
            business_id=bid,
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
