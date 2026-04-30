"""
ETL Step 3 — Carga a PostgreSQL / Supabase
Lee el CSV limpio y lo inserta en la base de datos.
Requiere .env con DATABASE_URL configurado.
"""

import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / "backend" / ".env")

DATA_PATH = Path(__file__).parents[2] / "forecasting" / "data" / "train_clean.csv"
DATABASE_URL = os.getenv("DATABASE_URL")


def load_to_db(df: pd.DataFrame):
    # TODO: implementar carga con SQLAlchemy
    # - Crear engine con DATABASE_URL
    # - Insertar en tabla `sales_history` (store_nbr, family, date, sales, onpromotion)
    # - Manejar conflictos con ON CONFLICT DO NOTHING para re-runs seguros
    pass


if __name__ == "__main__":
    if not DATABASE_URL:
        raise EnvironmentError("DATABASE_URL no está definida. Verificar backend/.env")

    print(f"Cargando {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    print(f"  {len(df):,} filas a cargar")

    print(f"Conectando a la base de datos...")
    load_to_db(df)
    print("✅ Carga completada")
