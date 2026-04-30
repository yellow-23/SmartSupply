"""
ForecastService — SmartSupply
Capa de servicio que conecta los endpoints de la API con los módulos de forecasting.
"""

from datetime import datetime, date, timedelta
from typing import Literal, Optional

from app.models.schemas import ForecastResponse, ForecastPoint


class ForecastService:
    """
    Servicio de predicción de demanda.

    En producción, este servicio llamará al módulo forecasting/ para
    ejecutar los modelos ARIMA, Prophet, XGBoost y LSTM.

    Por ahora retorna datos de ejemplo para que la API sea funcional
    mientras el módulo de forecasting (Int.1) se implementa.
    """

    def predict(
        self,
        sku_id: str,
        store_nbr: int,
        horizon_days: int,
        model: Optional[str] = "auto",
    ) -> ForecastResponse:
        """
        Genera predicción de demanda para un SKU.

        Flujo real (a implementar):
        1. Cargar datos históricos del SKU desde la BD
        2. Si model='auto', llamar al AMS (Automated Model Selector) del módulo forecasting/
        3. El AMS evalúa ARIMA, Prophet, XGBoost, LSTM → elige el de menor MAPE en validación
        4. El modelo seleccionado genera predicciones para horizon_days
        5. Retornar predicciones con intervalos de confianza
        """
        # TODO: Reemplazar con llamada real al módulo forecasting/src/selector.py
        model_used = model if model != "auto" else self._auto_select_model(sku_id, store_nbr)

        predictions = self._generate_mock_predictions(horizon_days)

        return ForecastResponse(
            sku_id=sku_id,
            store_nbr=store_nbr,
            model_used=model_used,
            mape_validation=8.3,  # TODO: Valor real del AMS
            horizon_days=horizon_days,
            predictions=predictions,
            generated_at=datetime.now(),
        )

    def _auto_select_model(self, sku_id: str, store_nbr: int) -> str:
        """
        Automated Model Selector (AMS).
        Selecciona el modelo de menor MAPE en validación para el SKU.

        TODO: Llamar a forecasting/src/selector.py:AutoModelSelector
        """
        # Placeholder — en producción consulta los resultados de validación guardados
        return "prophet"

    def _generate_mock_predictions(self, horizon_days: int) -> list[ForecastPoint]:
        """Genera predicciones de ejemplo para desarrollo."""
        import random
        base_demand = 50.0
        predictions = []
        for i in range(horizon_days):
            pred_date = date.today() + timedelta(days=i + 1)
            noise = random.uniform(-10, 10)
            sales = max(0, base_demand + noise)
            predictions.append(ForecastPoint(
                date=pred_date,
                predicted_sales=round(sales, 2),
                lower_bound=round(sales * 0.8, 2),
                upper_bound=round(sales * 1.2, 2),
            ))
        return predictions
