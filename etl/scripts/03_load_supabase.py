"""
ETL Step 3 — Carga a Supabase via REST API
Lee los CSVs limpios y los sube con upsert en lotes.
No requiere DATABASE_URL ni password — usa SUPABASE_URL y SUPABASE_KEY.
"""

import os
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parents[2] / "backend" / ".env")

PROCESSED_DIR = Path(__file__).parents[2] / "datasets" / "processed"
BATCH_SIZE = 500

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)


def load_table(table: str, df: pd.DataFrame, on_conflict: str):
    total = len(df)
    batches = range(0, total, BATCH_SIZE)
    print(f"  Cargando {total:,} filas en '{table}' ({len(list(batches))} lotes)...")

    for i, start in enumerate(range(0, total, BATCH_SIZE)):
        batch = df.iloc[start : start + BATCH_SIZE]
        records = batch.where(pd.notnull(batch), None).to_dict(orient="records")
        supabase.table(table).upsert(records, on_conflict=on_conflict).execute()

        if (i + 1) % 10 == 0:
            print(f"    {start + BATCH_SIZE:,} / {total:,}")
        time.sleep(0.05)  # respetar rate limit del free tier

    print(f"  ✓ '{table}' cargada")


if __name__ == "__main__":
    print("\n=== ETL Step 3: Carga a Supabase ===\n")

    # 1. stores (sin dependencias)
    df_stores = pd.read_csv(PROCESSED_DIR / "stores_clean.csv")
    load_table("stores", df_stores, on_conflict="store_nbr")

    # 2. oil_prices
    df_oil = pd.read_csv(PROCESSED_DIR / "oil_clean.csv", parse_dates=["date"])
    df_oil["date"] = df_oil["date"].dt.strftime("%Y-%m-%d")
    load_table("oil_prices", df_oil, on_conflict="date")

    # 3. holidays
    df_hol = pd.read_csv(PROCESSED_DIR / "holidays_clean.csv", parse_dates=["date"])
    df_hol["date"] = df_hol["date"].dt.strftime("%Y-%m-%d")
    df_hol = df_hol.drop(columns=["id"], errors="ignore")
    load_table("holidays", df_hol, on_conflict="date,locale,locale_name")

    # 4. sales_history (depende de stores — cargar al final)
    # STORE_FILTER=None carga todo; asigna un numero para cargar solo esa tienda
    STORE_FILTER = None
    df_sales = pd.read_csv(PROCESSED_DIR / "train_clean.csv", parse_dates=["date"])
    if STORE_FILTER is not None:
        df_sales = df_sales[df_sales["store_nbr"] == STORE_FILTER]
        print(f"  (Modo prueba: solo tienda {STORE_FILTER} — {len(df_sales):,} filas)")
    df_sales["date"] = df_sales["date"].dt.strftime("%Y-%m-%d")
    df_sales["onpromotion"] = df_sales["onpromotion"].fillna(0).astype(int)
    load_table("sales_history", df_sales, on_conflict="id")

    print("\n✓ Carga completa")
