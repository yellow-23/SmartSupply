"""
ForecastService — SmartSupply
Capa de servicio que conecta los endpoints de la API con el motor AMS.
"""

import os
import sys
from datetime import datetime, date
from typing import Literal, Optional

from app.models.schemas import ForecastResponse, ForecastPoint

# Agregar el root del repo al path para importar el módulo forecasting/
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROOT = os.path.dirname(_BACKEND_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# CSV de ventas limpias (relativo al root del repo)
_CSV_PATH = os.path.join(_ROOT, "datasets", "processed", "train_clean.csv")


class ForecastService:
    """
    Servicio de predicción de demanda.
    Llama al motor AMS (forecasting/src/ams_pipeline.py) para cada request.
    """

    def predict(
        self,
        sku_id: str,
        store_nbr: int,
        horizon_days: int,
        model: Optional[str] = "auto",
    ) -> ForecastResponse:
        """
        Genera predicción de demanda para un SKU usando el motor AMS.

        Si model='auto' o 'ams', ejecuta el Automated Model Selector.
        Si model es un nombre específico (arima|prophet|xgboost|lstm),
        fuerza ese modelo saltando la selección automática.
        """
        from forecasting.src.ams_pipeline import run_ams_pipeline, load_sku_series
        from forecasting.src.selector import AutoModelSelector, MODELS, calculate_wape
        import numpy as np

        forced_model = None if model in ("auto", None) else model

        if forced_model:
            # Modo modelo forzado: entrena solo el modelo solicitado
            series = load_sku_series(_CSV_PATH, sku_family=sku_id, store_nbr=store_nbr)
            if len(series) < 90:
                raise ValueError(
                    f"Serie demasiado corta para '{sku_id}' tienda {store_nbr} "
                    f"({len(series)} días, mínimo 90)."
                )
            n = len(series)
            train_end = int(n * 0.70)
            val_end = int(n * 0.85)
            train = series.iloc[:train_end]
            val = series.iloc[train_end:val_end]
            train_val = series.iloc[:val_end]

            ModelClass = MODELS.get(forced_model)
            if ModelClass is None:
                raise ValueError(f"Modelo desconocido: '{forced_model}'. Opciones: {list(MODELS)}")

            fit_kwargs = {"epochs": 50} if forced_model == "lstm" else {}
            m = ModelClass()
            m.fit(train, **fit_kwargs)
            val_pred = m.predict(len(val))
            wape_val = calculate_wape(val.values, val_pred.values[:len(val)])

            # Reentrenar sobre train+val y predecir
            m2 = ModelClass()
            m2.fit(train_val, **fit_kwargs)
            final_pred = m2.predict(horizon_days)

            model_used = forced_model
            wape_used = round(float(wape_val), 2) if np.isfinite(wape_val) else None
            pred_series = final_pred

        else:
            # Modo AMS completo
            result = run_ams_pipeline(
                csv_path=_CSV_PATH,
                sku_id=sku_id,
                store_nbr=store_nbr,
                horizon=horizon_days,
                output_dir=os.path.join(_ROOT, "forecasting", "outputs"),
            )
            model_used = result["Modelo_Elegido"].lower()
            wape_used = result["WAPE"]
            pred_series = result["final_pred"] if "final_pred" in result else None

            # Reconstruir serie de predicción desde el dict si es necesario
            if pred_series is None:
                import pandas as pd
                dates = list(result["Prediccion_30d"].keys())
                vals = list(result["Prediccion_30d"].values())
                pred_series = pd.Series(vals, index=pd.to_datetime(dates))

        # Construir lista de ForecastPoint
        predictions = [
            ForecastPoint(
                date=idx.date() if hasattr(idx, "date") else idx,
                predicted_sales=round(float(val), 2),
            )
            for idx, val in pred_series.items()
        ]

        return ForecastResponse(
            sku_id=sku_id,
            store_nbr=store_nbr,
            model_used=model_used,
            mape_validation=wape_used,
            horizon_days=horizon_days,
            predictions=predictions,
            generated_at=datetime.now(),
        )
