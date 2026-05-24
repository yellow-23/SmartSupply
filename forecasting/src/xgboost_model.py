import numpy as np
import pandas as pd
import xgboost as xgb


# Feriados fijos chilenos como conjunto MM-DD
_CHILE_HOLIDAYS_MD: set[str] = {
    "01-01", "05-01", "05-21", "07-16", "08-15",
    "09-18", "09-19", "10-12", "11-01", "12-08", "12-25",
}


class XGBoostModel:
    """
    Direct multi-step XGBoost (estrategia DIRMO) con lags adaptativos.

    Entrena un XGBRegressor independiente por cada paso k del horizonte.
    Cada modelo predice y[t+k] directamente desde features en t — sin usar
    predicciones propias como lags (sin error acumulado en horizontes largos).

    Lags adaptativos según tamaño de la serie (``_compute_adaptive_params``):
      - Permite entrenar todos los k necesarios incluso en series cortas.
      - Serie larga (≥200 días de train): usa lag_7…90, k hasta 90.
      - Serie corta (~100 días de train): usa lag_7…30, k hasta ~49.
      El criterio: max_lag + max_k + 20 ≤ n_train garantiza ≥20 muestras
      de entrenamiento para el k más largo.

    Features por modelo:
      Fuente:   lag_L para cada L en lags_efectivos
      Rolling:  rm_7, rm_14, rm_30  (shift+1 para evitar leakage)
      Src date: src_dow, src_month
      Tgt date: tgt_dow, tgt_month, tgt_year, tgt_is_holiday

    Hiperparámetros tuneados para series diarias de retail CLP:
      n_estimators=500, lr=0.04, max_depth=5, min_child_weight=3,
      subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.5
    """

    MAX_HORIZON = 90  # k máximo absoluto (se recorta adaptativamente)

    def __init__(self):
        self.models: dict[int, xgb.XGBRegressor] = {}
        self._last_date: pd.Timestamp | None = None
        self._tail_vals: list[float] = []
        self._dow_floor: dict[int, float] = {}
        self._effective_lags: list[int] = []  # lags usados (depende de n)
        self._effective_max_k: int = self.MAX_HORIZON  # k máximo entrenado

    @staticmethod
    def _compute_adaptive_params(n: int) -> tuple[list[int], int]:
        """
        Elige lags y max_k dados n días de entrenamiento.

        Regla: max_lag + max_k ≤ n - 20  (≥20 muestras para el k más largo).
        Reparte el presupuesto en mitades: mitad para lags, mitad para horizonte.
        """
        budget = max(0, n - 20)
        max_lag = min(90, max(14, budget // 2))
        max_k   = min(90, max(7,  budget - max_lag))
        lags    = [l for l in (7, 14, 30, 60, 90) if l <= max_lag]
        return lags or [7], max_k

    @staticmethod
    def _make_xgb() -> xgb.XGBRegressor:
        return xgb.XGBRegressor(
            n_estimators=500,
            learning_rate=0.04,
            max_depth=5,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.5,
            random_state=42,
            verbosity=0,
        )

    def _build_feature_matrix(
        self, series: pd.Series, k: int
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """
        Construye (X, y) vectorizado para el modelo del paso k.
        Fila i: features en t=i  →  objetivo = series[i+k].

        Consistencia con inferencia:
          lag_L = shift(L)                      → vals[i-L]
          rm_L  = shift(1).rolling(L).mean()    → mean(vals[i-L], …, vals[i-1])
        """
        df = series.to_frame(name="y")
        df.index = pd.to_datetime(df.index)

        for lag in self._effective_lags:
            df[f"lag_{lag}"] = df["y"].shift(lag)

        # shift(1) antes del rolling evita filtración del valor actual.
        # rm_30 siempre válido: max_lag ≥ 30 cuando n ≥ 80 (garantizado por
        # la restricción n ≥ 91 del AMS).
        df["rm_7"]  = df["y"].shift(1).rolling(7).mean()
        df["rm_14"] = df["y"].shift(1).rolling(14).mean()
        df["rm_30"] = df["y"].shift(1).rolling(30).mean()

        df["src_dow"]   = df.index.dayofweek
        df["src_month"] = df.index.month

        # Fecha objetivo — información calendario pura, sin leakage
        tgt_dates = df.index + pd.Timedelta(days=k)
        df["tgt_dow"]        = tgt_dates.dayofweek
        df["tgt_month"]      = tgt_dates.month
        df["tgt_year"]       = tgt_dates.year
        df["tgt_is_holiday"] = (
            tgt_dates.strftime("%m-%d").isin(_CHILE_HOLIDAYS_MD).astype(int)
        )

        df["target"] = df["y"].shift(-k)
        df = df.dropna()

        X = df.drop(columns=["y", "target"])
        return X, df["target"].values

    def fit(self, series: pd.Series):
        series = series.astype(float)
        idx = pd.to_datetime(series.index)
        vals = series.values
        n = len(vals)

        self._last_date = idx[-1]

        # Parámetros adaptativos según longitud de la serie
        self._effective_lags, self._effective_max_k = self._compute_adaptive_params(n)
        min_history = max(self._effective_lags)  # lag máximo → historia mínima

        # Guardar min_history+1 valores: lag_L en inferencia = tail_vals[-(L+1)]
        self._tail_vals = list(vals[-(min_history + 1):].astype(float))

        # Piso día-de-semana: p10 de valores no-cero (excluye zeros de fill_value
        # de días sin actividad que distorsionarían el percentil hacia 0)
        for dow in range(7):
            dow_vals = vals[idx.dayofweek == dow]
            nonzero = dow_vals[dow_vals > 0]
            self._dow_floor[dow] = (
                float(np.percentile(nonzero, 10)) if len(nonzero) > 0 else 0.0
            )

        # Entrenar un modelo independiente por cada paso k
        for k in range(1, self._effective_max_k + 1):
            X, y = self._build_feature_matrix(series, k)
            if len(X) < 20:
                continue
            m = self._make_xgb()
            m.fit(X, y)
            self.models[k] = m

    def predict(self, horizon: int) -> pd.Series:
        if not self.models:
            raise RuntimeError("Llama a fit() antes de predict()")

        tv = self._tail_vals  # len = min_history + 1
        preds: list[float] = []

        for k in range(1, horizon + 1):
            tgt_date = self._last_date + pd.Timedelta(days=k)

            # lag_L = vals[n-1-L] = tv[-(L+1)]
            # rm_L  = mean(vals[n-1-L], …, vals[n-2]) = mean(tv[-(L+1):-1])
            row: dict = {}
            for lag in self._effective_lags:
                row[f"lag_{lag}"] = tv[-(lag + 1)] if len(tv) > lag else tv[0]

            n_tv = len(tv)
            row["rm_7"]  = float(np.mean(tv[-8:-1]))  if n_tv >= 8  else float(np.mean(tv))
            row["rm_14"] = float(np.mean(tv[-15:-1])) if n_tv >= 15 else float(np.mean(tv))
            row["rm_30"] = float(np.mean(tv[-31:-1])) if n_tv >= 31 else float(np.mean(tv))

            row["src_dow"]        = self._last_date.dayofweek
            row["src_month"]      = self._last_date.month
            row["tgt_dow"]        = tgt_date.dayofweek
            row["tgt_month"]      = tgt_date.month
            row["tgt_year"]       = tgt_date.year
            row["tgt_is_holiday"] = int(tgt_date.strftime("%m-%d") in _CHILE_HOLIDAYS_MD)

            model = self.models.get(k)
            if model is None:
                model = self.models[min(self.models, key=lambda x: abs(x - k))]

            raw = float(model.predict(pd.DataFrame([row]))[0])
            floor = self._dow_floor.get(tgt_date.dayofweek, 0.0)
            preds.append(max(floor, max(0.0, raw)))

        idx = pd.date_range(
            start=self._last_date + pd.Timedelta(days=1), periods=horizon
        )
        return pd.Series(preds, index=idx)
