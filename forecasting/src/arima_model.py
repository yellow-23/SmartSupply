import warnings
from itertools import product

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX


class ARIMAModel:
    """
    SARIMA con selección automática por AIC.
    Búsqueda no-estacional: p∈[0,2], d∈[0,1], q∈[0,2].
    Búsqueda estacional (s=7) cuando hay >=21 días: P∈[0,1], D∈[0,1], Q∈[0,1].

    La serie se normaliza por su media antes de ajustar para mejorar la
    convergencia numérica con datos de gran magnitud (p.ej. ventas en CLP).
    La predicción se reescala automáticamente al regresar.
    """

    SEASONAL_PERIOD = 7
    SEASONAL_MIN_OBS = 21  # al menos 3 ciclos para fittear componente semanal

    def __init__(self):
        self.fitted_model = None
        self.order = None
        self.seasonal_order = None
        self._scale: float = 1.0  # factor de normalización (media de la serie)

    def _select_order(self, series: pd.Series) -> tuple:
        """Retorna ((p,d,q), (P,D,Q,s)) con menor AIC."""
        best_aic = np.inf
        best_order = (1, 1, 1)
        best_seasonal = (0, 0, 0, 0)

        use_seasonal = len(series) >= self.SEASONAL_MIN_OBS
        seasonal_grid = (
            list(product(range(2), range(2), range(2)))
            if use_seasonal else [(0, 0, 0)]
        )

        for p, d, q in product(range(3), range(2), range(3)):
            for P, D, Q in seasonal_grid:
                s_order = (P, D, Q, self.SEASONAL_PERIOD) if (P or D or Q) else (0, 0, 0, 0)
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        res = SARIMAX(
                            series,
                            order=(p, d, q),
                            seasonal_order=s_order,
                            enforce_stationarity=False,
                            enforce_invertibility=False,
                        ).fit(disp=False, maxiter=50)
                    if res.aic < best_aic:
                        best_aic = res.aic
                        best_order = (p, d, q)
                        best_seasonal = s_order
                except Exception:
                    continue
        return best_order, best_seasonal

    def fit(self, series: pd.Series):
        # Normalizar por la media para estabilidad numérica con series de gran escala
        mean = float(series.mean())
        self._scale = mean if mean > 0 else 1.0
        scaled = series / self._scale

        self.order, self.seasonal_order = self._select_order(scaled)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.fitted_model = SARIMAX(
                scaled,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False, maxiter=200)

    def predict(self, horizon: int) -> pd.Series:
        if self.fitted_model is None:
            raise RuntimeError("Llama a fit() antes de predict()")
        forecast = self.fitted_model.forecast(steps=horizon)
        return (forecast * self._scale).clip(lower=0)
