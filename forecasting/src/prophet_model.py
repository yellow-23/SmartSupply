import pandas as pd
from prophet import Prophet


class ProphetModel:
    def __init__(self):
        self.model = None

    def fit(self, series: pd.Series):
        # TODO: preparar dataframe con columnas ds/y e incluir feriados chilenos
        pass

    def predict(self, horizon: int) -> pd.Series:
        # TODO: retornar predicciones para los próximos `horizon` días
        pass
