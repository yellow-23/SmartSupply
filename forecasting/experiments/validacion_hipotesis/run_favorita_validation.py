"""
Validacion completa de la hipotesis sobre el dataset de benchmarking
Store Sales - Corporacion Favorita: 33 familias, tienda 1 (una sola tienda
para que la corrida sea abordable en tiempo).

Para cada familia corre:
  - El AMS completo (cv=False, sin LSTM -- mismos parametros que produccion,
    ver forecast_service.py:290)
  - Cada modelo individual (ARIMA, Prophet, XGBoost) entrenado SOLO sobre
    train+val y medido sobre el 15% de prueba -- la misma metodologia
    honesta que ahora usa selector.py para el ganador del AMS, pero
    aplicada a los 3 modelos por separado, para poder comparar el AMS
    contra CADA modelo unico y no solo contra ARIMA.
  - Un baseline ingenuo estacional (promedio de las ultimas 4 ocurrencias
    del mismo dia de semana).

Guarda favorita_validation_results.csv de forma incremental (una fila por
familia, apenas se calcula) para no perder nada si se corta a mitad de
camino. Al final corre un test de Wilcoxon pareado: AMS vs cada modelo
individual y vs el baseline, sobre las familias con WAPE valido.

Solo lee data/store1_all_families.csv y escribe en resultados/. No toca
Supabase.
"""
import sys, time, warnings, csv
from pathlib import Path

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent
ROOT = BASE_DIR.parents[2]  # raiz del repo (forecasting/experiments/validacion_hipotesis/../../..)
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from forecasting.src.selector import AutoModelSelector, MODELS, calculate_wape

INPUT_CSV = BASE_DIR / "data" / "store1_all_families.csv"
OUTPUT_CSV = BASE_DIR / "resultados" / "favorita_validation_results.csv"
HORIZON = 15


class SeasonalNaiveModel:
    """Baseline ingenuo: predice el promedio de las ultimas 4 ocurrencias
    del mismo dia de semana vistas en el set con que se entreno."""

    def __init__(self):
        self._dow_mean: dict[int, float] = {}
        self._last_date = None

    def fit(self, series: pd.Series, **kwargs):
        s = series.copy()
        s.index = pd.to_datetime(s.index)
        dow = s.index.dayofweek
        overall_mean = float(s.mean())
        for d in range(7):
            vals = s[dow == d]
            self._dow_mean[d] = float(vals.tail(4).mean()) if len(vals) else overall_mean
        self._last_date = s.index[-1]

    def predict(self, horizon: int) -> pd.Series:
        idx = pd.date_range(self._last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
        vals = [self._dow_mean.get(d.dayofweek, 0.0) for d in idx]
        return pd.Series(vals, index=idx)


def test_wape_for_model(model_cls, train_val: pd.Series, test: pd.Series) -> float:
    """Entrena model_cls SOLO con train_val (nunca vio test) y mide el WAPE
    sobre test. Misma logica que usa selector.py para medir el ganador,
    aplicada aca a un modelo cualquiera."""
    try:
        m = model_cls()
        fit_kwargs = {"epochs": 50} if model_cls.__name__.lower().startswith("lstm") else {}
        m.fit(train_val, **fit_kwargs)
        pred = m.predict(len(test))
        return calculate_wape(test.values, pred.values[: len(test)])
    except Exception as exc:
        print(f"      ERROR ({model_cls.__name__}): {exc}")
        return np.nan


def main():
    df = pd.read_csv(INPUT_CSV, parse_dates=["date"])
    families = sorted(df["family"].unique())

    fieldnames = [
        "family", "n_days", "pct_zero",
        "ams_winner", "ams_wape_selection", "ams_wape_test",
        "arima_wape_test", "prophet_wape_test", "xgboost_wape_test",
        "baseline_wape_test", "elapsed_s",
    ]

    # Reanudar: si ya hay un CSV de salida (de una corrida anterior, completa
    # o cortada a mitad de camino), saltar las familias ya calculadas en vez
    # de sobreescribir todo de nuevo.
    done_families: set[str] = set()
    if OUTPUT_CSV.exists():
        prev = pd.read_csv(OUTPUT_CSV)
        done_families = set(prev["family"].tolist())
        print(f"Reanudando: {len(done_families)} familias ya calculadas en {OUTPUT_CSV.name}, se saltan.")
        out_f = open(OUTPUT_CSV, "a", newline="", encoding="utf-8")
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    else:
        out_f = open(OUTPUT_CSV, "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        out_f.flush()

    pending = [f for f in families if f not in done_families]
    print(f"{len(families)} familias en total, {len(pending)} pendientes (tienda 1, dataset Favorita)\n")

    t_start = time.time()
    for i, family in enumerate(pending, 1):
        sub = df[df["family"] == family][["date", "sales"]].sort_values("date")
        series = pd.Series(sub["sales"].values, index=sub["date"]).asfreq("D", fill_value=0.0)
        n = len(series)
        pct_zero = float((series == 0).mean())

        print(f"[{i:2d}/{len(pending)}] {family:<28} ({n}d, {pct_zero*100:4.1f}% ceros) ...", end=" ", flush=True)
        t0 = time.time()

        # ── AMS completo (mismos parametros que produccion) ──────────────
        ams = AutoModelSelector(horizon=HORIZON, cv=False, include_lstm=False)
        result = ams.select(series, sku_id=family)

        # ── Cada modelo individual, medido igual de honesto (train+val -> test) ──
        val_end = int(n * 0.85)
        train_val = series.iloc[:val_end]
        test = series.iloc[val_end:]

        arima_wape = test_wape_for_model(MODELS["arima"], train_val, test)
        prophet_wape = test_wape_for_model(MODELS["prophet"], train_val, test)
        xgboost_wape = test_wape_for_model(MODELS["xgboost"], train_val, test)
        baseline_wape = test_wape_for_model(SeasonalNaiveModel, train_val, test)

        elapsed = time.time() - t0
        row = {
            "family": family,
            "n_days": n,
            "pct_zero": round(pct_zero, 4),
            "ams_winner": result["model"],
            "ams_wape_selection": result["wape_selection"],
            "ams_wape_test": result["wape_test"] if result["wape_test"] is not None else result["wape"],
            "arima_wape_test": None if np.isnan(arima_wape) else round(float(arima_wape), 2),
            "prophet_wape_test": None if np.isnan(prophet_wape) else round(float(prophet_wape), 2),
            "xgboost_wape_test": None if np.isnan(xgboost_wape) else round(float(xgboost_wape), 2),
            "baseline_wape_test": None if np.isnan(baseline_wape) else round(float(baseline_wape), 2),
            "elapsed_s": round(elapsed, 1),
        }
        writer.writerow(row)
        out_f.flush()

        total_elapsed = time.time() - t_start
        eta = total_elapsed / i * (len(pending) - i)
        print(f"ganador={result['model']:<8} wape_test={row['ams_wape_test']}%  "
              f"({elapsed:.0f}s, ETA {eta/60:.0f}min)")

    out_f.close()
    print(f"\nTotal: {(time.time()-t_start)/60:.1f} min. Resultados en {OUTPUT_CSV}")

    # ── Resumen + test estadistico ────────────────────────────────────────
    res = pd.read_csv(OUTPUT_CSV)
    valid = res.dropna(subset=["ams_wape_test", "arima_wape_test", "prophet_wape_test",
                                "xgboost_wape_test", "baseline_wape_test"])
    print(f"\n{'='*70}")
    print(f"RESUMEN ({len(valid)}/{len(res)} familias con WAPE valido en los 5 metodos)")
    print(f"{'='*70}")

    cols = {
        "AMS (seleccion automatica)": "ams_wape_test",
        "ARIMA (unico)": "arima_wape_test",
        "Prophet (unico)": "prophet_wape_test",
        "XGBoost (unico)": "xgboost_wape_test",
        "Baseline ingenuo (dow)": "baseline_wape_test",
    }
    print(f"\n{'Metodo':<28} {'WAPE medio':>12} {'WAPE mediana':>14}")
    print(f"{'-'*28} {'-'*12} {'-'*14}")
    for label, col in cols.items():
        print(f"{label:<28} {valid[col].mean():>11.2f}% {valid[col].median():>13.2f}%")

    print(f"\nDistribucion de modelos ganadores del AMS:")
    print(valid["ams_winner"].value_counts().to_string())

    wins = (valid["ams_wape_test"] <= valid[["arima_wape_test", "prophet_wape_test", "xgboost_wape_test"]].min(axis=1))
    print(f"\nAMS iguala o mejora al mejor modelo unico en {wins.sum()}/{len(valid)} familias ({wins.mean()*100:.0f}%)")

    print(f"\n{'='*70}")
    print("TEST DE WILCOXON (pareado, AMS vs cada alternativa)")
    print(f"{'='*70}")
    for label, col in cols.items():
        if col == "ams_wape_test":
            continue
        try:
            stat, p = wilcoxon(valid["ams_wape_test"], valid[col])
            sig = "SI (p<0.05)" if p < 0.05 else "no"
            print(f"  AMS vs {label:<26} p-value={p:.4f}  significativo: {sig}")
        except Exception as exc:
            print(f"  AMS vs {label:<26} ERROR: {exc}")


if __name__ == "__main__":
    main()
