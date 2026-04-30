import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX


class ARIMAModel:
    def __init__(self):
        self.model = None

    def fit(self, series: pd.Series):
        # TODO: implementar auto_arima para encontrar los mejores parámetros (p,d,q)
        pass

    def predict(self, horizon: int) -> pd.Series:
        # TODO: retornar predicciones para los próximos `horizon` días
        pass
