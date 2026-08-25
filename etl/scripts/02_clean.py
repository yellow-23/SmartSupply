"""
ETL Step 2 — Limpieza y normalización del dataset
Lee los CSVs raw y genera archivos limpios en datasets/processed/
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parents[2] / "datasets" / "raw"
OUT_DIR  = Path(__file__).parents[2] / "datasets" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_sales(path: Path) -> pd.DataFrame:
    print("  Leyendo train.csv...")
    df = pd.read_csv(path, parse_dates=["date"])

    # Filtrar 2016-2017 para no saturar el free tier de Supabase (~500k filas)
    df = df[df["date"] >= "2016-01-01"].copy()
    print(f"  Filas tras filtro 2016-2017: {len(df):,}")

    # Eliminar duplicados
    df.drop_duplicates(subset=["date", "store_nbr", "family"], inplace=True)

    # Ventas negativas son errores de registro — reemplazar con 0
    df.loc[df["sales"] < 0, "sales"] = 0

    # Feature engineering temporal
    df.sort_values(["store_nbr", "family", "date"], inplace=True)
    grp = df.groupby(["store_nbr", "family"])["sales"]
    df["lag_7"]         = grp.shift(7)
    df["lag_14"]        = grp.shift(14)
    df["rolling_mean_7"] = grp.transform(lambda x: x.shift(1).rolling(7).mean())

    # Eliminar filas donde los lags no tienen suficiente historia
    df.dropna(subset=["lag_7", "lag_14", "rolling_mean_7"], inplace=True)

    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"]       = df["date"].dt.month

    print(f"  Filas finales train_clean: {len(df):,}")
    return df


def clean_stores(path: Path) -> pd.DataFrame:
    print("  Leyendo stores.csv...")
    df = pd.read_csv(path)
    df.drop_duplicates(subset=["store_nbr"], inplace=True)
    return df


if __name__ == "__main__":
    print("\n=== ETL Step 2: Limpieza ===\n")

    df_sales    = clean_sales(RAW_DIR / "train.csv")
    df_stores   = clean_stores(RAW_DIR / "stores.csv")

    print("\nGuardando archivos limpios...")
    df_sales.to_csv(OUT_DIR / "train_clean.csv", index=False)
    df_stores.to_csv(OUT_DIR / "stores_clean.csv", index=False)

    print(f"\n✓ train_clean.csv     → {len(df_sales):,} filas")
    print(f"✓ stores_clean.csv    → {len(df_stores):,} filas")
    print(f"\nArchivos en: {OUT_DIR}")
