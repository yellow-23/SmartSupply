from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import ForecastRequest, ForecastResponse
from app.services.forecast_service import ForecastService

router = APIRouter()
service = ForecastService()


@router.post("/predict", response_model=ForecastResponse)
async def predict_demand(request: ForecastRequest):
    """
    Genera una predicción de demanda para un SKU usando el motor AMS.

    - **sku_id**: Familia de producto (ej: "GROCERY I", "BEVERAGES")
    - **store_nbr**: Número de tienda (1-54)
    - **horizon_days**: Horizonte de predicción (7, 14 o 30 días)
    - **model**: `auto` activa el Automated Model Selector (AMS) que elige
      el mejor entre ARIMA, Prophet, XGBoost y LSTM por WAPE en validación.
      También acepta un modelo específico: `arima`, `prophet`, `xgboost`, `lstm`.
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
    store_nbr: int = Query(default=1, description="Número de tienda"),
    horizon_days: int = Query(default=14, ge=7, le=30, description="Días a predecir"),
    model: str = Query(default="auto", description="Modelo o 'auto' para AMS"),
):
    """
    Predicción rápida GET para el SKU indicado.
    Equivalente a POST /predict con los mismos parámetros.
    """
    try:
        result = service.predict(
            sku_id=sku_id,
            store_nbr=store_nbr,
            horizon_days=horizon_days,
            model=model,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")
