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
    """

    def __init__(self):
        self.model: xgb.XGBRegressor | None = None
        self._tail: list[float] = []        # últimos 30 valores para predicción
        self._last_date: pd.Timestamp | None = None

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
        self._tail = list(series.values[-30:].astype(float))
        self._last_date = pd.to_datetime(series.index[-1])

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
            val = max(0.0, float(self.model.predict(pd.DataFrame([row]))[0]))
            preds.append(val)
            history.append(val)
        idx = pd.date_range(start=self._last_date + pd.Timedelta(days=1), periods=horizon)
        return pd.Series(preds, index=idx)
