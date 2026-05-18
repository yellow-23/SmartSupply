import warnings
from itertools import product

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX


class ARIMAModel:
    """
    ARIMA con selección automática de orden (p, d, q) por AIC.
    Búsqueda en p∈[0,2], d∈[0,1], q∈[0,2].
    """

    def __init__(self):
        self.fitted_model = None
        self.order = None

    def _select_order(self, series: pd.Series) -> tuple[int, int, int]:
        """Retorna el (p, d, q) con menor AIC."""
        best_aic = np.inf
        best_order = (1, 1, 1)
        for p, d, q in product(range(3), range(2), range(3)):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    res = SARIMAX(
                        series,
                        order=(p, d, q),
                        enforce_stationarity=False,
                        enforce_invertibility=False,
                    ).fit(disp=False)
                if res.aic < best_aic:
                    best_aic = res.aic
                    best_order = (p, d, q)
            except Exception:
                continue
        return best_order

    def fit(self, series: pd.Series):
        self.order = self._select_order(series)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.fitted_model = SARIMAX(
                series,
                order=self.order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)

    def predict(self, horizon: int) -> pd.Series:
        if self.fitted_model is None:
            raise RuntimeError("Llama a fit() antes de predict()")
        forecast = self.fitted_model.forecast(steps=horizon)
        return forecast.clip(lower=0)
