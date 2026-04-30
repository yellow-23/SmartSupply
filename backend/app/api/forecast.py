from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.schemas import ForecastRequest, ForecastResponse
from app.services.forecast_service import ForecastService

router = APIRouter()
service = ForecastService()


@router.post("/predict", response_model=ForecastResponse)
async def predict_demand(request: ForecastRequest):
    """
    Genera una predicción de demanda para un SKU específico.

    - **sku_id**: Identificador del producto
    - **store_nbr**: Número de tienda
    - **horizon_days**: Horizonte de predicción (7, 14 o 30 días)
    - **model**: Modelo a usar. 'auto' activa el Automated Model Selector (AMS)
    """
    try:
        result = service.predict(
            sku_id=request.sku_id,
            store_nbr=request.store_nbr,
            horizon_days=request.horizon_days,
            model=request.model,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")


@router.get("/models")
async def list_available_models():
    """Lista los modelos de forecasting disponibles y sus métricas globales."""
    return {
        "models": ["arima", "prophet", "xgboost", "lstm"],
        "default": "auto",
        "description": "El modo 'auto' usa el Automated Model Selector (AMS) que elige el mejor modelo por SKU según MAPE en validación.",
    }


@router.get("/{sku_id}", response_model=ForecastResponse)
async def get_forecast_for_sku(
    sku_id: str,
    store_nbr: int = 1,
    horizon_days: int = 14,
):
    """
    Predicción rápida usando el modelo auto-seleccionado para el SKU.
    Equivalente a POST /predict con model='auto'.
    """
    try:
        result = service.predict(
            sku_id=sku_id,
            store_nbr=store_nbr,
            horizon_days=horizon_days,
            model="auto",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
