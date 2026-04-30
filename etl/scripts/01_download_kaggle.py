"""
ETL Step 1 — Descomprimir el dataset de Kaggle
Descomprime datasets/store-sales-time-series-forecasting.zip → forecasting/data/
"""

import zipfile
from pathlib import Path

ZIP_PATH = Path(__file__).parents[2] / "datasets" / "store-sales-time-series-forecasting.zip"
OUTPUT_DIR = Path(__file__).parents[2] / "forecasting" / "data"


def extract_dataset():
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"No se encontró el zip en {ZIP_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Extrayendo {ZIP_PATH} → {OUTPUT_DIR} ...")
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(OUTPUT_DIR)

    print("Archivos extraídos:")
    for f in OUTPUT_DIR.iterdir():
        print(f"  {f.name}  ({f.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    extract_dataset()
