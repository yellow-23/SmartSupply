import pandas as pd
from forecasting.src.arima_model import ARIMAModel
from forecasting.src.prophet_model import ProphetModel
from forecasting.src.xgboost_model import XGBoostModel
from forecasting.src.lstm_model import LSTMModel


MODELS = {
    "arima": ARIMAModel,
    "prophet": ProphetModel,
    "xgboost": XGBoostModel,
    "lstm": LSTMModel,
}


def calculate_mape(actual: pd.Series, predicted: pd.Series) -> float:
    # TODO: implementar MAPE ignorando períodos con demanda cero
    pass


class AutoModelSelector:
    """
    Automated Model Selector (AMS).
    Evalúa los 4 modelos sobre cada SKU con walk-forward validation
    y selecciona el de menor MAPE en el conjunto de validación.
    """

    def select(self, series: pd.Series) -> tuple[str, object]:
        """
        Retorna (nombre_modelo, modelo_entrenado) con menor MAPE.
        TODO: implementar validación caminante (70/15/15 train/val/test)
        """
        pass
