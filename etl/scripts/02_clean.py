"""
ETL Step 2 — Limpieza y normalización del dataset
Lee forecasting/data/train.csv y genera un CSV limpio listo para cargar a la BD.
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parents[2] / "forecasting" / "data"
OUTPUT_PATH = DATA_DIR / "train_clean.csv"


def load_raw() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "train.csv", parse_dates=["date"])


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # TODO: implementar limpieza
    # - Eliminar duplicados
    # - Manejar valores negativos en sales (errores de registro)
    # - Rellenar fechas faltantes por SKU con demanda cero (forward-fill o cero)
    # - Normalizar nombres de familia de productos
    # - Agregar columnas de features temporales (day_of_week, month, is_holiday)
    return df


def save(df: pd.DataFrame):
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Dataset limpio guardado en {OUTPUT_PATH} ({len(df):,} filas)")


if __name__ == "__main__":
    print("Cargando dataset raw...")
    df = load_raw()
    print(f"  {len(df):,} filas cargadas")

    print("Limpiando...")
    df_clean = clean(df)

    save(df_clean)
