import logging

import pandas as pd
from prophet import Prophet


# ---------------------------------------------------------------------------
# Feriados fijos chilenos para Prophet
# ---------------------------------------------------------------------------
def _chile_holidays() -> pd.DataFrame:
    rows = []
    for year in range(2012, 2031):
        for md, name in [
            ("01-01", "Año Nuevo"),
            ("05-01", "Día del Trabajo"),
            ("05-21", "Glorias Navales"),
            ("07-16", "Virgen del Carmen"),
            ("08-15", "Asunción de la Virgen"),
            ("09-18", "Independencia Nacional"),
            ("09-19", "Glorias del Ejército"),
            ("10-12", "Encuentro de Dos Mundos"),
            ("11-01", "Todos los Santos"),
            ("12-08", "Inmaculada Concepción"),
            ("12-25", "Navidad"),
        ]:
            rows.append({"ds": pd.Timestamp(f"{year}-{md}"), "holiday": name})
    return pd.DataFrame(rows)


class ProphetModel:
    """
    Modelo Prophet con feriados fijos chilenos incorporados.
    """

    def __init__(self):
        self.model = None
        self._last_date: pd.Timestamp | None = None

    def fit(self, series: pd.Series):
        df = series.reset_index()
        df.columns = ["ds", "y"]
        df["ds"] = pd.to_datetime(df["ds"])
        self._last_date = df["ds"].max()
        logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
        # Activar estacionalidad anual solo con >=2 ciclos completos (~730 días).
        # Con menos data Prophet sobre-ajusta y genera predicciones absurdas.
        n_days = (df["ds"].max() - df["ds"].min()).days
        yearly = n_days >= 730
        weekly = n_days >= 14
        self.model = Prophet(
            holidays=_chile_holidays(),
            yearly_seasonality=yearly,
            weekly_seasonality=weekly,
            daily_seasonality=False,
            interval_width=0.95,
        )
        self.model.fit(df)

    def predict(self, horizon: int) -> pd.Series:
        if self.model is None:
            raise RuntimeError("Llama a fit() antes de predict()")
        future = self.model.make_future_dataframe(periods=horizon)
        forecast_df = self.model.predict(future)
        result = forecast_df.tail(horizon).set_index("ds")["yhat"]
        result.index = pd.to_datetime(result.index)
        return result.clip(lower=0)
