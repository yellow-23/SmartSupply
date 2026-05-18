"""
05_batch_ams_validation.py
--------------------------
Ejecuta el pipeline AMS sobre múltiples combinaciones SKU × Tienda
y genera un CSV comparativo con los resultados.

Uso
---
    # Modo rápido: muestra N SKUs aleatorios de todas las tiendas
    py -3.13 etl/scripts/05_batch_ams_validation.py --sample 5

    # SKUs específicos en tiendas específicas
    py -3.13 etl/scripts/05_batch_ams_validation.py \
        --skus "GROCERY I" "BEVERAGES" \
        --stores 1 2 3

    # Todas las combinaciones (54 tiendas × 33 familias = 1782 — lento)
    py -3.13 etl/scripts/05_batch_ams_validation.py --all

    # Con walk-forward CV (más robusto, más lento)
    py -3.13 etl/scripts/05_batch_ams_validation.py --sample 5 --cv

Salida
------
    forecasting/outputs/batch_results_YYYYMMDD_HHMMSS.csv
    forecasting/outputs/batch_summary.png
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from forecasting.src.ams_pipeline import run_ams_pipeline, load_sku_series  # noqa: E402


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
CSV_PATH = os.path.join(_ROOT, "datasets", "processed", "train_clean.csv")
OUTPUT_DIR = os.path.join(_ROOT, "forecasting", "outputs")
MIN_DAYS = 90  # series con menos días se omiten


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_all_combinations(csv_path: str) -> list[tuple[str, int]]:
    """Retorna todas las combinaciones (family, store_nbr) presentes en el CSV."""
    df = pd.read_csv(csv_path, usecols=["family", "store_nbr"])
    combos = df.drop_duplicates().sort_values(["family", "store_nbr"])
    return list(zip(combos["family"], combos["store_nbr"]))


def get_sample_combinations(
    csv_path: str,
    skus: list[str] | None,
    stores: list[int] | None,
    n_sample: int | None,
    rng: np.random.Generator,
) -> list[tuple[str, int]]:
    """Filtra/muestrea combinaciones según los argumentos CLI."""
    all_combos = get_all_combinations(csv_path)

    if skus:
        all_combos = [(f, s) for f, s in all_combos if f in skus]
    if stores:
        all_combos = [(f, s) for f, s in all_combos if s in stores]

    if n_sample and n_sample < len(all_combos):
        idx = rng.choice(len(all_combos), size=n_sample, replace=False)
        all_combos = [all_combos[i] for i in sorted(idx)]

    return all_combos


# ---------------------------------------------------------------------------
# Ejecución batch
# ---------------------------------------------------------------------------

def run_batch(
    combos: list[tuple[str, int]],
    cv: bool = False,
    output_dir: str = OUTPUT_DIR,
) -> pd.DataFrame:
    os.makedirs(output_dir, exist_ok=True)
    records: list[dict] = []
    total = len(combos)

    print(f"\nBatch AMS — {total} combinaciones  |  CV={'activado' if cv else 'desactivado'}")
    print("=" * 70)

    for i, (sku, store) in enumerate(combos, start=1):
        print(f"\n[{i}/{total}]  SKU: {sku:<20}  Tienda: {store}")
        t0 = time.time()

        try:
            # Verificar que la serie tenga suficientes días antes de correr
            series = load_sku_series(CSV_PATH, sku_family=sku, store_nbr=store)
            if len(series) < MIN_DAYS:
                print(f"  ⚠ Serie muy corta ({len(series)} días) — omitida")
                records.append({
                    "sku": sku, "store_nbr": store,
                    "status": "omitida_serie_corta", "n_dias": len(series),
                })
                continue

            result = run_ams_pipeline(
                csv_path=CSV_PATH,
                sku_id=sku,
                store_nbr=store,
                cv=cv,
                output_dir=output_dir,
            )
            elapsed = round(time.time() - t0, 1)
            records.append({
                "sku": result["SKU"],
                "store_nbr": result["Tienda"],
                "status": "ok",
                "n_dias": len(series),
                "modelo_elegido": result["Modelo_Elegido"],
                "wape": result["WAPE"],
                "wape_arima": result["WAPE_todos"].get("arima"),
                "wape_prophet": result["WAPE_todos"].get("prophet"),
                "wape_xgboost": result["WAPE_todos"].get("xgboost"),
                "wape_lstm": result["WAPE_todos"].get("lstm"),
                "demanda_diaria": result["Demanda_Diaria_Prom"],
                "stock_seguridad": result["Stock_Seguridad"],
                "punto_reorden": result["Punto_Reorden"],
                "eoq": result["EOQ"],
                "sugerencia_compra": result["Sugerencia_Compra"],
                "tiempo_seg": elapsed,
            })
            print(f"  ✓  {result['Modelo_Elegido']}  WAPE={result['WAPE']}%  ({elapsed}s)")

        except Exception as exc:
            elapsed = round(time.time() - t0, 1)
            print(f"  ✗  ERROR: {exc}")
            records.append({
                "sku": sku, "store_nbr": store,
                "status": f"error: {exc}", "tiempo_seg": elapsed,
            })

    df = pd.DataFrame(records)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_out = os.path.join(output_dir, f"batch_results_{ts}.csv")
    df.to_csv(csv_out, index=False)
    print(f"\nResultados guardados: {csv_out}")
    return df


# ---------------------------------------------------------------------------
# Resumen y gráfico
# ---------------------------------------------------------------------------

def print_summary(df: pd.DataFrame) -> None:
    ok = df[df["status"] == "ok"].copy()
    if ok.empty:
        print("\nNo hay resultados exitosos para resumir.")
        return

    print("\n" + "=" * 70)
    print("  RESUMEN BATCH")
    print("=" * 70)
    print(f"  Combinaciones procesadas : {len(df)}")
    print(f"  Exitosas                 : {len(ok)}")
    print(f"  Omitidas / Error         : {len(df) - len(ok)}")
    print(f"\n  WAPE promedio ganador    : {ok['wape'].mean():.2f}%")
    print(f"  WAPE mínimo              : {ok['wape'].min():.2f}%")
    print(f"  WAPE máximo              : {ok['wape'].max():.2f}%")
    print(f"\n  Distribución de modelos ganadores:")
    for model, count in ok["modelo_elegido"].value_counts().items():
        pct = count / len(ok) * 100
        print(f"    {model:<12}: {count:3d}  ({pct:.1f}%)")

    # WAPE promedio por modelo (para la hipótesis AMS vs único)
    wape_cols = ["wape_arima", "wape_prophet", "wape_xgboost", "wape_lstm"]
    print(f"\n  WAPE promedio por modelo (en todos los SKUs evaluados):")
    for col in wape_cols:
        if col in ok.columns:
            vals = ok[col].dropna()
            if not vals.empty:
                print(f"    {col.replace('wape_', ''):12}: {vals.mean():.2f}%")
    print(f"    {'AMS (ganador)':12}: {ok['wape'].mean():.2f}%")


def plot_summary(df: pd.DataFrame, output_dir: str) -> None:
    ok = df[df["status"] == "ok"].copy()
    if ok.empty:
        return

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("SmartSupply AMS — Resumen batch", fontsize=14)

    # 1. Distribución de WAPE del ganador
    axes[0].hist(ok["wape"].dropna(), bins=20, color="steelblue", edgecolor="white")
    axes[0].axvline(ok["wape"].mean(), color="red", linestyle="--",
                    label=f"Media: {ok['wape'].mean():.1f}%")
    axes[0].set_title("Distribución WAPE (modelo ganador)")
    axes[0].set_xlabel("WAPE (%)")
    axes[0].set_ylabel("Frecuencia")
    axes[0].legend(fontsize=9)

    # 2. Modelos ganadores (pie chart)
    counts = ok["modelo_elegido"].value_counts()
    axes[1].pie(counts.values, labels=counts.index, autopct="%1.0f%%",
                colors=["#4e79a7", "#f28e2b", "#76b7b2", "#e15759"])
    axes[1].set_title("Modelos seleccionados por AMS")

    # 3. WAPE promedio: AMS vs cada modelo individual
    wape_cols = {
        "ARIMA": "wape_arima",
        "Prophet": "wape_prophet",
        "XGBoost": "wape_xgboost",
        "LSTM": "wape_lstm",
        "AMS\n(ganador)": "wape",
    }
    means = {k: ok[v].dropna().mean() for k, v in wape_cols.items() if v in ok.columns}
    colors = ["#aec7e8"] * (len(means) - 1) + ["#1f77b4"]
    bars = axes[2].bar(means.keys(), means.values(), color=colors, edgecolor="white")
    for bar, val in zip(bars, means.values()):
        axes[2].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.3, f"{val:.1f}%",
                     ha="center", va="bottom", fontsize=9)
    axes[2].set_title("WAPE medio: AMS vs modelo único")
    axes[2].set_ylabel("WAPE promedio (%)")
    axes[2].set_ylim(0, max(means.values()) * 1.25)

    plt.tight_layout()
    path = os.path.join(output_dir, "batch_summary.png")
    plt.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  Gráfico guardado: {path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SmartSupply — Validación batch AMS (múltiples SKU × Tienda)"
    )
    parser.add_argument(
        "--csv", default=CSV_PATH,
        help="Ruta al CSV de ventas limpias"
    )
    parser.add_argument(
        "--skus", nargs="+", default=None,
        help="Familias/SKUs a evaluar (por defecto todas)"
    )
    parser.add_argument(
        "--stores", nargs="+", type=int, default=None,
        help="Tiendas a evaluar (por defecto todas)"
    )
    parser.add_argument(
        "--sample", type=int, default=None,
        help="Número de combinaciones aleatorias a evaluar"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Evaluar todas las combinaciones (54×33)"
    )
    parser.add_argument(
        "--cv", action="store_true",
        help="Usar walk-forward cross-validation"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Semilla para el muestreo aleatorio"
    )
    parser.add_argument(
        "--output", default=OUTPUT_DIR,
        help="Carpeta de salida para CSV y gráficos"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    rng = np.random.default_rng(args.seed)

    if args.all:
        combos = get_all_combinations(args.csv)
    else:
        combos = get_sample_combinations(
            args.csv,
            skus=args.skus,
            stores=args.stores,
            n_sample=args.sample if args.sample else (10 if not args.skus and not args.stores else None),
            rng=rng,
        )

    if not combos:
        print("No se encontraron combinaciones con los filtros indicados.")
        sys.exit(1)

    results_df = run_batch(combos, cv=args.cv, output_dir=args.output)
    print_summary(results_df)
    plot_summary(results_df, args.output)
