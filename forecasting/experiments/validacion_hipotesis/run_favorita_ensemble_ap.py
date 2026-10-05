"""
Escala el piloto de ensamble ARIMA+Prophet (pilot_ensemble_ap.py) a las 33
familias completas de la tienda 1. El piloto de 6 familias mostro que
promediar SOLO ARIMA+Prophet (sin XGBoost, que arrastraba el promedio para
abajo) casi empata al mejor individual, y en 2/6 familias le gano.

No vuelve a entrenar XGBoost: su WAPE de test ya esta calculado en
favorita_validation_results.csv (misma metodologia train_val->test), asi
que se reutiliza para la comparacion "mejor individual (de los 3)". Solo se
entrenan ARIMA y Prophet, que es lo unico nuevo.

Igual que el resto de las corridas: guarda incremental (resume si se corta)
y no toca Supabase ni el repo.
"""
import sys, time, warnings, csv
from pathlib import Path

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent
ROOT = BASE_DIR.parents[2]  # raiz del repo
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from forecasting.src.selector import MODELS, calculate_wape

INPUT_CSV = BASE_DIR / "data" / "store1_all_families.csv"
PREV_RESULTS_CSV = BASE_DIR / "resultados" / "favorita_validation_results.csv"  # trae xgboost_wape_test y baseline
OUTPUT_CSV = BASE_DIR / "resultados" / "favorita_ensemble_ap_results.csv"


def fit_predict(model_cls, train_series: pd.Series, horizon: int):
    m = model_cls()
    m.fit(train_series)
    return m.predict(horizon)


def main():
    df = pd.read_csv(INPUT_CSV, parse_dates=["date"])
    families = sorted(df["family"].unique())

    fieldnames = [
        "family", "n_days", "pct_zero",
        "arima_wape_test", "prophet_wape_test",
        "ensemble_simple_wape_test", "ensemble_weighted_wape_test",
        "elapsed_s",
    ]

    done_families: set[str] = set()
    if OUTPUT_CSV.exists():
        prev = pd.read_csv(OUTPUT_CSV)
        done_families = set(prev["family"].tolist())
        print(f"Reanudando: {len(done_families)} familias ya calculadas, se saltan.")
        out_f = open(OUTPUT_CSV, "a", newline="", encoding="utf-8")
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    else:
        out_f = open(OUTPUT_CSV, "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        out_f.flush()

    pending = [f for f in families if f not in done_families]
    print(f"{len(families)} familias en total, {len(pending)} pendientes\n")

    t_start = time.time()
    for i, family in enumerate(pending, 1):
        sub = df[df["family"] == family][["date", "sales"]].sort_values("date")
        series = pd.Series(sub["sales"].values, index=sub["date"]).asfreq("D", fill_value=0.0)
        n = len(series)
        pct_zero = float((series == 0).mean())

        val_start = int(n * 0.70)
        val_end = int(n * 0.85)
        train = series.iloc[:val_start]
        val = series.iloc[val_start:val_end]
        train_val = series.iloc[:val_end]
        test = series.iloc[val_end:]

        print(f"[{i:2d}/{len(pending)}] {family:<28} ({n}d, {pct_zero*100:4.1f}% ceros) ...", end=" ", flush=True)
        t0 = time.time()

        val_wapes, test_preds, test_wapes = {}, {}, {}
        for name, cls in [("arima", MODELS["arima"]), ("prophet", MODELS["prophet"])]:
            try:
                pred_val = fit_predict(cls, train, len(val))
                val_wapes[name] = calculate_wape(val.values, pred_val.values[: len(val)])
            except Exception as exc:
                print(f"\n      ERROR val {name}: {exc}")
                val_wapes[name] = np.nan
            try:
                pred_test = fit_predict(cls, train_val, len(test))
                test_preds[name] = pred_test.values[: len(test)]
                test_wapes[name] = calculate_wape(test.values, test_preds[name])
            except Exception as exc:
                print(f"\n      ERROR test {name}: {exc}")
                test_preds[name] = None
                test_wapes[name] = np.nan

        ens_simple = np.nan
        if test_preds.get("arima") is not None and test_preds.get("prophet") is not None:
            stacked = np.mean(np.vstack([test_preds["arima"], test_preds["prophet"]]), axis=0)
            ens_simple = calculate_wape(test.values, stacked)

        ens_weighted = np.nan
        w_arima, w_prophet = val_wapes.get("arima"), val_wapes.get("prophet")
        if (test_preds.get("arima") is not None and test_preds.get("prophet") is not None
                and np.isfinite(w_arima) and np.isfinite(w_prophet) and w_arima > 0 and w_prophet > 0):
            wa, wp = 1.0 / w_arima, 1.0 / w_prophet
            wsum = wa + wp
            stacked_w = test_preds["arima"] * (wa / wsum) + test_preds["prophet"] * (wp / wsum)
            ens_weighted = calculate_wape(test.values, stacked_w)

        elapsed = time.time() - t0
        row = {
            "family": family,
            "n_days": n,
            "pct_zero": round(pct_zero, 4),
            "arima_wape_test": None if np.isnan(test_wapes.get("arima", np.nan)) else round(float(test_wapes["arima"]), 2),
            "prophet_wape_test": None if np.isnan(test_wapes.get("prophet", np.nan)) else round(float(test_wapes["prophet"]), 2),
            "ensemble_simple_wape_test": None if np.isnan(ens_simple) else round(float(ens_simple), 2),
            "ensemble_weighted_wape_test": None if np.isnan(ens_weighted) else round(float(ens_weighted), 2),
            "elapsed_s": round(elapsed, 1),
        }
        writer.writerow(row)
        out_f.flush()

        total_elapsed = time.time() - t_start
        eta = total_elapsed / i * (len(pending) - i)
        print(f"ensamble={row['ensemble_simple_wape_test']}%  ({elapsed:.0f}s, ETA {eta/60:.0f}min)")

    out_f.close()
    print(f"\nTotal: {(time.time()-t_start)/60:.1f} min. Resultados en {OUTPUT_CSV}")

    # ── Fusion con lo que ya teniamos (xgboost, baseline, ams) y resumen ──
    ens = pd.read_csv(OUTPUT_CSV)
    prev = pd.read_csv(PREV_RESULTS_CSV)
    m = ens.merge(prev[["family", "xgboost_wape_test", "baseline_wape_test", "ams_wape_test"]], on="family")

    single_cols = ["arima_wape_test", "prophet_wape_test", "xgboost_wape_test"]
    m["best_single_wape_test"] = m[single_cols].min(axis=1)

    # El resumen se imprime dos veces: con las 32 familias validas, y sin BOOKS
    # (92,5% de dias sin ventas: el WAPE se vuelve inestable). La tesis reporta
    # la version sin BOOKS (N=31).
    for excluir in ([], ["BOOKS"]):
        valid = m[~m["family"].isin(excluir)].dropna(
            subset=["ensemble_simple_wape_test", "best_single_wape_test", "ams_wape_test", "baseline_wape_test"])
        etiqueta = "sin " + ", ".join(excluir) if excluir else "todas las familias"
        print(f"\n{'='*70}\nRESUMEN {etiqueta} ({len(valid)}/{len(m)} familias validas)\n{'='*70}")
        print(f"\n{'Metodo':<32} {'WAPE medio':>12} {'WAPE mediana':>14}")
        print(f"{'-'*32} {'-'*12} {'-'*14}")
        for label, col in [
            ("Ensamble ARIMA+Prophet (simple)", "ensemble_simple_wape_test"),
            ("Ensamble ARIMA+Prophet (ponderado)", "ensemble_weighted_wape_test"),
            ("Mejor individual (de los 3)", "best_single_wape_test"),
            ("AMS (split unico)", "ams_wape_test"),
            ("Baseline ingenuo (dow)", "baseline_wape_test"),
        ]:
            print(f"{label:<32} {valid[col].mean():>11.2f}% {valid[col].median():>13.2f}%")

        wins = (valid["ensemble_simple_wape_test"] <= valid["best_single_wape_test"])
        print(f"\nEnsamble A+P iguala/mejora al mejor individual en {wins.sum()}/{len(valid)} familias ({wins.mean()*100:.0f}%)")

        print(f"\nTEST DE WILCOXON (pareado, ensamble A+P vs cada alternativa)")
        for label, col in [
            ("mejor individual", "best_single_wape_test"),
            ("ARIMA (fijo)", "arima_wape_test"),
            ("Prophet (fijo)", "prophet_wape_test"),
            ("XGBoost (fijo)", "xgboost_wape_test"),
            ("AMS (split unico)", "ams_wape_test"),
            ("baseline ingenuo", "baseline_wape_test"),
        ]:
            try:
                stat, p = wilcoxon(valid["ensemble_simple_wape_test"], valid[col])
                sig = "SI (p<0.05)" if p < 0.05 else "no"
                print(f"  Ensamble A+P vs {label:<20} p-value={p:.4f}  significativo: {sig}")
            except Exception as exc:
                print(f"  Ensamble A+P vs {label:<20} ERROR: {exc}")

    m.to_csv(BASE_DIR / "resultados" / "favorita_ensemble_ap_consolidado.csv", index=False)
    print(f"\nConsolidado guardado en favorita_ensemble_ap_consolidado.csv")


if __name__ == "__main__":
    main()
