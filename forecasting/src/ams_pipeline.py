"""
ams_pipeline.py
---------------
Orquestador principal del pipeline AMS de SmartSupply.

Flujo:
    1. ETL / Preparación de serie temporal para el SKU solicitado.
    2. AMS  — entrena ARIMA, Prophet, XGBoost y LSTM; evalúa WAPE en
              validación y reentrena el ganador sobre train+val.
    3. Inventario — calcula Stock de Seguridad, Punto de Reorden (s) y EOQ.
    4. Gráfico — "Real vs Predicho" del mejor modelo (guarda PNG).
    5. Devuelve diccionario final con el resumen del SKU.

Uso rápido
----------
    from forecasting.src.ams_pipeline import run_ams_pipeline

    resultado = run_ams_pipeline(
        csv_path="datasets/processed/train_clean.csv",
        sku_id="GROCERY I",
        store_nbr=1,
    )
    print(resultado)

CLI
---
    python -m forecasting.src.ams_pipeline \\
        --csv datasets/processed/train_clean.csv \\
        --sku "GROCERY I" \\
        --store 1
"""

from __future__ import annotations

import argparse
import os
import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Asegurar que el workspace root esté en sys.path cuando se corre como script
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from forecasting.src.selector import AutoModelSelector  # noqa: E402
from inventory.src.eoq import EOQModel                  # noqa: E402
from inventory.src.s_s_policy import SsPolicyModel      # noqa: E402

# ---------------------------------------------------------------------------
# Parámetros de coste por defecto (ajustables por SKU en producción)
# ---------------------------------------------------------------------------
DEFAULT_ORDER_COST = 50_000    # CLP por pedido
DEFAULT_HOLDING_COST = 1_200   # CLP por unidad almacenada al año
DEFAULT_LEAD_TIME = 7          # días de entrega del proveedor


# ---------------------------------------------------------------------------
# Helpers de ETL
# ---------------------------------------------------------------------------

def load_sku_series(
    csv_path: str,
    sku_family: str,
    store_nbr: int | None = None,
) -> pd.Series:
    """
    Carga el CSV limpio de ventas y devuelve una serie diaria para el SKU.

    Parámetros
    ----------
    csv_path   : ruta al CSV (debe tener columnas date, family, sales,
                 y opcionalmente store_nbr).
    sku_family : familia de producto (p.ej. "GROCERY I").
    store_nbr  : número de tienda; si es None agrega todas las tiendas.

    Retorna
    -------
    pd.Series con índice DatetimeIndex diario y valores de ventas ≥ 0.
    """
    df = pd.read_csv(csv_path, parse_dates=["date"])

    if "family" in df.columns:
        df = df[df["family"] == sku_family]
    if store_nbr is not None and "store_nbr" in df.columns:
        df = df[df["store_nbr"] == store_nbr]

    if df.empty:
        raise ValueError(
            f"No hay datos para SKU='{sku_family}', store_nbr={store_nbr}."
        )

    daily = df.groupby("date")["sales"].sum().sort_index()
    daily = daily.asfreq("D", fill_value=0.0)
    return daily.clip(lower=0)


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def run_ams_pipeline(
    csv_path: str | None = None,
    sku_id: str = "GROCERY I",
    store_nbr: int | None = 1,
    horizon: int = 30,
    order_cost: float = DEFAULT_ORDER_COST,
    holding_cost: float = DEFAULT_HOLDING_COST,
    lead_time: int = DEFAULT_LEAD_TIME,
    output_dir: str = ".",
    cv: bool = False,
    series: pd.Series | None = None,
    save_plot: bool = True,
) -> dict:
    """
    Pipeline completo: ETL → AMS → Inventario → Gráfico.

    Si ``series`` se entrega, se usa directamente y se omite la carga de ``csv_path``.
    Esto permite ejecutar el AMS sobre datos del usuario (Supabase) sin tocar el CSV.

    Retorna
    -------
    dict con claves:
        SKU, Tienda, Modelo_Elegido, WAPE, WAPE_todos,
        Demanda_Diaria_Prom, Stock_Seguridad, Punto_Reorden,
        EOQ, Sugerencia_Compra, Prediccion_30d
    """
    sep = "=" * 62
    print(f"\n{sep}")
    print(f"  SmartSupply AMS — SKU: {sku_id} | Tienda: {store_nbr}")
    print(sep)

    # ── 1. ETL ─────────────────────────────────────────────────────────────
    print("\n[1/3] Cargando y preparando datos...")
    if series is None:
        if csv_path is None:
            raise ValueError("Debes entregar csv_path o series.")
        series = load_sku_series(csv_path, sku_family=sku_id, store_nbr=store_nbr)
    print(
        f"      Serie: {len(series):,} días  "
        f"({series.index[0].date()} → {series.index[-1].date()})"
    )

    if len(series) < 30:
        raise ValueError(
            "La serie tiene menos de 30 observaciones. "
            "Se necesitan al menos 30 días para entrenar los modelos."
        )

    # ── 2. AMS ─────────────────────────────────────────────────────────────
    cv_label = "walk-forward CV" if cv else "split único 70/15/15"
    print(f"\n[2/3] Ejecutando AMS  (ARIMA · Prophet · XGBoost · LSTM) — {cv_label}...")
    ams = AutoModelSelector(horizon=horizon, cv=cv)
    result = ams.select(series, sku_id=sku_id)

    wapes_display = result['wapes_cv'] if cv and result['wapes_cv'] else result['wapes_all']
    print(f"\n      WAPE por modelo : {wapes_display}")
    print(
        f"      Modelo ganador  : {result['model'].upper()}"
        f"  (WAPE = {result['wape']} %)"
    )

    # ── 3. Inventario ───────────────────────────────────────────────────────
    print("\n[3/3] Calculando parámetros de inventario...")
    forecast_series: pd.Series = result["final_pred"]
    forecast_arr = forecast_series.values.astype(float)

    daily_demand = float(np.mean(forecast_arr))
    daily_std = float(series.iloc[-90:].std())
    annual_demand = daily_demand * 365

    eoq_model = EOQModel(annual_demand, order_cost, holding_cost)
    q_star = eoq_model.optimal_quantity()
    ss = eoq_model.safety_stock(daily_std, lead_time)
    rop = eoq_model.reorder_point(daily_demand, lead_time, daily_std)

    # Política (s, S) para cross-check
    ss_policy = SsPolicyModel(lead_time, holding_cost, order_cost)
    s_val = ss_policy.calculate_s(forecast_arr)
    S_val = ss_policy.calculate_S(s_val, q_star)

    purchase_suggestion = float(forecast_arr.sum())  # unidades próximos 30 d

    print(f"      Demanda diaria prom.   : {daily_demand:.1f} uds/día")
    print(f"      Stock de seguridad (SS): {ss:.0f} uds")
    print(f"      Punto de reorden   (s) : {rop:.0f} uds")
    print(f"      Nivel reposi.      (S) : {S_val:.0f} uds")
    print(f"      EOQ                (Q*): {q_star:.0f} uds")
    print(f"      Sugerencia de compra   : {purchase_suggestion:.0f} uds (próx. {horizon} días)")

    # ── 4. Gráfico ──────────────────────────────────────────────────────────
    plot_path = _plot_forecast(result, sku_id, store_nbr, output_dir) if save_plot else None

    # ── 5. Resultado ────────────────────────────────────────────────────────
    output: dict = {
        "SKU": sku_id,
        "Tienda": store_nbr,
        "Modelo_Elegido": result["model"].upper(),
        "WAPE": result["wape"],
        "WAPE_todos": result["wapes_all"],
        "Demanda_Diaria_Prom": round(daily_demand, 2),
        "Stock_Seguridad": round(ss, 0),
        "Punto_Reorden": round(rop, 0),
        "EOQ": round(q_star, 0),
        "Sugerencia_Compra": round(purchase_suggestion, 0),
        "Prediccion_30d": {
            str(k.date()): round(float(v), 2)
            for k, v in forecast_series.items()
        },
        "final_pred": forecast_series,   # pd.Series — disponible para forecast_service
        "Grafico": plot_path,
    }

    print(f"\n{sep}")
    print("  RESULTADO FINAL")
    print(sep)
    _verbose_skip = {"WAPE_todos", "Prediccion_30d", "Grafico"}
    for k, v in output.items():
        if k not in _verbose_skip:
            print(f"  {k:<28}: {v}")

    return output


# ---------------------------------------------------------------------------
# Gráfico
# ---------------------------------------------------------------------------

def _plot_forecast(
    result: dict,
    sku_id: str,
    store_nbr: int | None,
    output_dir: str,
) -> str:
    """Genera y guarda el gráfico 'Real vs Predicho' del modelo ganador."""
    train: pd.Series = result["train"]
    val: pd.Series = result["val"]
    test: pd.Series = result["test"]
    final_pred: pd.Series = result["final_pred"]
    model_name = result["model"].upper()
    wape = result["wape"]

    # Histórico: últimos 120 días para no sobrecargar el eje X
    history = pd.concat([train, val, test]).iloc[-120:]

    fig, ax = plt.subplots(figsize=(14, 5))

    # Serie real
    ax.plot(
        history.index, history.values,
        color="steelblue", linewidth=1.3, label="Real",
    )

    # Separador train/val/test
    ax.axvline(train.index[-1], color="gray", linestyle=":", alpha=0.6, linewidth=1)
    ax.axvline(val.index[-1],   color="gray", linestyle=":", alpha=0.6, linewidth=1)

    # Predicción 30 días
    ax.plot(
        final_pred.index, final_pred.values,
        color="tomato", linewidth=2, linestyle="--",
        label=f"Predicho — {model_name}  (WAPE {wape}%)",
    )
    ax.fill_between(final_pred.index, 0, final_pred.values, color="tomato", alpha=0.12)

    # Comparación en validación (modelo ganador)
    val_pred = result["val_preds"].get(result["model"])
    if val_pred is not None:
        overlap_idx = val.index[:len(val_pred)]
        ax.plot(
            overlap_idx, val_pred.values[: len(overlap_idx)],
            color="orange", linewidth=1.2, linestyle="--", alpha=0.7,
            label=f"Val predicho — {model_name}",
        )

    ax.set_title(
        f"SmartSupply AMS — SKU: {sku_id}  |  Tienda: {store_nbr}  |  Modelo: {model_name}",
        fontsize=13,
    )
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Ventas (unidades)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=30)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    safe_sku = sku_id.replace(" ", "_").replace("/", "-")
    filename = os.path.join(output_dir, f"ams_{safe_sku}_{store_nbr}.png")
    plt.savefig(filename, dpi=150)
    plt.close(fig)
    print(f"\n      Gráfico guardado: {filename}")
    return filename


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SmartSupply AMS Pipeline — selección automática de modelos de forecasting"
    )
    parser.add_argument(
        "--csv", default="datasets/processed/train_clean.csv",
        help="Ruta al CSV de ventas limpias"
    )
    parser.add_argument("--sku",   default="GROCERY I", help="Familia/SKU a modelar")
    parser.add_argument("--store", type=int, default=1,  help="Número de tienda")
    parser.add_argument("--horizon", type=int, default=30, help="Días a predecir")
    parser.add_argument(
        "--output", default="forecasting/outputs",
        help="Carpeta donde guardar el gráfico PNG"
    )
    parser.add_argument(
        "--cv", action="store_true",
        help="Usar walk-forward cross-validation (3 folds) en lugar del split único"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    resultado = run_ams_pipeline(
        csv_path=args.csv,
        sku_id=args.sku,
        store_nbr=args.store,
        horizon=args.horizon,
        output_dir=args.output,
        cv=args.cv,
    )
