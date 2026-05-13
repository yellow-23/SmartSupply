"""
04_feature_engineering.py
--------------------------
Crea variables de tiempo sobre train_clean.csv y las guarda en
datasets/processed/train_features.csv.

Nuevas columnas generadas (por grupo store_nbr + family):
  - lag_7, lag_14, lag_30      : ventas rezagadas
  - rolling_mean_7, _14        : medias móviles
  - is_holiday                  : flag feriados fijos chilenos
  - day_of_week, month          : variables cíclicas
"""

import pandas as pd
from pathlib import Path


# ---------------------------------------------------------------------------
# Feriados fijos de Chile (MM-DD). Los feriados móviles (Semana Santa,
# Elecciones) requieren cálculo por año; se omiten en esta versión simple.
# ---------------------------------------------------------------------------
CHILE_FIXED_HOLIDAYS_MD = {
    "01-01",  # Año Nuevo
    "05-01",  # Día del Trabajo
    "05-21",  # Glorias Navales
    "07-16",  # Virgen del Carmen
    "08-15",  # Asunción de la Virgen
    "09-18",  # Independencia Nacional
    "09-19",  # Glorias del Ejército
    "10-12",  # Encuentro de Dos Mundos
    "11-01",  # Día de Todos los Santos
    "12-08",  # Inmaculada Concepción
    "12-25",  # Navidad
}


def is_chile_holiday(date_series: pd.Series) -> pd.Series:
    """Devuelve 1 si la fecha es feriado fijo chileno, 0 en caso contrario."""
    return date_series.dt.strftime("%m-%d").isin(CHILE_FIXED_HOLIDAYS_MD).astype(int)


def add_time_features(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    """
    Agrega lags, medias móviles y flag de feriados a un DataFrame con
    columnas ``date`` y ``sales``.

    Parameters
    ----------
    df          : DataFrame con al menos 'date' y 'sales'.
    group_cols  : columnas por las que agrupar al calcular features
                  (p.ej. ['store_nbr', 'family']).  Si es None se asume
                  una sola serie temporal.

    Returns
    -------
    DataFrame enriquecido (sin filas con NaN en lags eliminadas).
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Variables cíclicas
    df["is_holiday"] = is_chile_holiday(df["date"])
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month

    lag_days = [7, 14, 30]
    roll_windows = [7, 14]

    if group_cols:
        for lag in lag_days:
            df[f"lag_{lag}"] = df.groupby(group_cols)["sales"].transform(
                lambda s: s.shift(lag)
            )
        for w in roll_windows:
            df[f"rolling_mean_{w}"] = df.groupby(group_cols)["sales"].transform(
                lambda s: s.shift(1).rolling(w).mean()
            )
    else:
        for lag in lag_days:
            df[f"lag_{lag}"] = df["sales"].shift(lag)
        for w in roll_windows:
            df[f"rolling_mean_{w}"] = df["sales"].shift(1).rolling(w).mean()

    return df


if __name__ == "__main__":
    base = Path(__file__).parents[2] / "datasets" / "processed"

    print("Leyendo train_clean.csv...")
    raw = pd.read_csv(base / "train_clean.csv", parse_dates=["date"])
    print(f"  {len(raw):,} filas cargadas")

    print("Calculando features...")
    enriched = add_time_features(raw, group_cols=["store_nbr", "family"])

    out_path = base / "train_features.csv"
    enriched.to_csv(out_path, index=False)
    print(f"Guardado: {out_path}  ({len(enriched):,} filas)")
    print(enriched[enriched["family"] == "GROCERY I"].head(10).to_string())
