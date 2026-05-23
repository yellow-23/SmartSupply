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
    XGBoost con features temporales y predicción iterativa multi-paso.
    Features: lag_7, lag_14, lag_30, rolling_mean_7, rolling_mean_14,
              day_of_week, month, year, is_holiday.

    Para horizontes largos (>14 días) la predicción iterativa puede acumular
    error y colapsar a cero. Se aplica un piso por día-de-semana basado en el
    percentil 10 del historial de entrenamiento, de modo que predicciones
    aberrantemente bajas se anclan al mínimo histórico razonable para ese día
    (sin sobreescribir cierres legítimos como domingos de negocios cerrados).
    """

    def __init__(self):
        self.model: xgb.XGBRegressor | None = None
        self._tail: list[float] = []        # últimos 60 valores para predicción
        self._last_date: pd.Timestamp | None = None
        self._dow_floor: dict[int, float] = {}  # piso percentil-10 por día de semana

    def build_features(self, series: pd.Series) -> pd.DataFrame:
        df = series.to_frame(name="y")
        df.index = pd.to_datetime(df.index)
        for lag in (7, 14, 30):
            df[f"lag_{lag}"] = df["y"].shift(lag)
        df["rolling_mean_7"] = df["y"].shift(1).rolling(7).mean()
        df["rolling_mean_14"] = df["y"].shift(1).rolling(14).mean()
        df["day_of_week"] = df.index.dayofweek
        df["month"] = df.index.month
        df["year"] = df.index.year
        df["is_holiday"] = df.index.strftime("%m-%d").isin(_CHILE_HOLIDAYS_MD).astype(int)
        return df.dropna()

    def fit(self, series: pd.Series):
        df = self.build_features(series)
        X = df.drop(columns=["y"])
        y = df["y"]
        self.model = xgb.XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
        self.model.fit(X, y)
        # Guardar los últimos 60 valores reales (mejor cobertura de lags largos)
        self._tail = list(series.values[-60:].astype(float))
        self._last_date = pd.to_datetime(series.index[-1])
        # Piso por día de semana: percentil 10 de los valores no-cero del historial.
        # Los ceros artificiales (fill_value de días sin datos) se excluyen para que
        # el piso refleje el mínimo real de actividad comercial en ese día de semana.
        # Para días que el negocio cierra genuinamente (todos sus valores ≈ 0),
        # len(nonzero) será 0 y el piso queda en 0 → comportamiento correcto.
        s_idx = pd.to_datetime(series.index)
        for dow in range(7):
            vals = series.values[s_idx.dayofweek == dow]
            nonzero_vals = vals[vals > 0]
            self._dow_floor[dow] = float(np.percentile(nonzero_vals, 10)) if len(nonzero_vals) > 0 else 0.0

    def predict(self, horizon: int) -> pd.Series:
        if self.model is None:
            raise RuntimeError("Llama a fit() antes de predict()")
        history = list(self._tail)
        preds: list[float] = []
        for i in range(1, horizon + 1):
            next_date = self._last_date + pd.Timedelta(days=i)
            n = len(history)
            row = {
                "lag_7":          history[-7],
                "lag_14":         history[-14] if n >= 14 else history[0],
                "lag_30":         history[-30] if n >= 30 else history[0],
                "rolling_mean_7":  float(np.mean(history[-7:])),
                "rolling_mean_14": float(np.mean(history[-14:])) if n >= 14 else float(np.mean(history)),
                "day_of_week":    next_date.dayofweek,
                "month":          next_date.month,
                "year":           next_date.year,
                "is_holiday":     int(next_date.strftime("%m-%d") in _CHILE_HOLIDAYS_MD),
            }
            raw = float(self.model.predict(pd.DataFrame([row]))[0])
            # Aplicar piso día-de-semana para evitar colapso iterativo a cero
            floor = self._dow_floor.get(next_date.dayofweek, 0.0)
            val = max(floor, max(0.0, raw))
            preds.append(val)
            history.append(val)
        idx = pd.date_range(start=self._last_date + pd.Timedelta(days=1), periods=horizon)
        return pd.Series(preds, index=idx)
