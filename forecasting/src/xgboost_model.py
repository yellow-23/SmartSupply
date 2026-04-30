import pandas as pd
import xgboost as xgb


class XGBoostModel:
    def __init__(self):
        self.model = None

    def build_features(self, series: pd.Series) -> pd.DataFrame:
        # TODO: crear features temporales (día semana, mes, lag_7, lag_14, rolling_mean)
        pass

    def fit(self, series: pd.Series):
        # TODO: entrenar con features construidos por build_features
        pass

    def predict(self, horizon: int) -> pd.Series:
        # TODO: predicción iterativa para los próximos `horizon` días
        pass
