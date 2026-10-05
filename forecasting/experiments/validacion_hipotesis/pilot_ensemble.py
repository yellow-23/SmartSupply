"""
Piloto rapido (6 familias, no las 33) para probar si PROMEDIAR las
predicciones de ARIMA+Prophet+XGBoost (ensamble) le gana a elegir uno solo
(seleccion), dado que en la corrida completa el "ganador" cambiaba de
familia en el 55% de los casos segun el criterio de seleccion usado -- señal
de que los modelos estan empatados y la seleccion agrega ruido, no señal.

Elegi 6 familias que ya corrimos antes, cubriendo perfiles distintos:
  - GROCERY I, BREAD/BAKERY, DAIRY: modelos muy parejos en val (buen caso
    para ensamble, si la teoria es correcta deberia ayudar mas aca)
  - CELEBRATION, MAGAZINES: donde el ganador cambio fuerte entre split y cv
    (el WAPE del "ganador" salto de 76.57% a 49.40% en MAGAZINES)
  - SEAFOOD: control, ya lo corrimos 2 veces antes

Mide, sobre el MISMO test set honesto (15% final, nunca visto), el WAPE de:
  - cada modelo individual (ya los tenemos, se recalculan igual para
    verificar reproducibilidad)
  - el ensamble (promedio simple de las 3 predicciones)
  - el ensamble ponderado por el inverso del WAPE de val (mas peso al que
    viene validando mejor)

No toca Supabase ni el repo.
"""
import sys, time, warnings
from pathlib import Path

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent
ROOT = BASE_DIR.parents[2]  # raiz del repo
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from forecasting.src.selector import MODELS, calculate_wape

INPUT_CSV = BASE_DIR / "data" / "store1_all_families.csv"
PILOT_FAMILIES = ["GROCERY I", "BREAD/BAKERY", "DAIRY", "CELEBRATION", "MAGAZINES", "SEAFOOD"]


def fit_predict(model_cls, train_val: pd.Series, horizon: int):
    m = model_cls()
    m.fit(train_val)
    return m.predict(horizon)


def main():
    df = pd.read_csv(INPUT_CSV, parse_dates=["date"])
    rows = []

    for family in PILOT_FAMILIES:
        sub = df[df["family"] == family][["date", "sales"]].sort_values("date")
        series = pd.Series(sub["sales"].values, index=sub["date"]).asfreq("D", fill_value=0.0)
        n = len(series)
        val_end = int(n * 0.85)
        val_start = int(n * 0.70)
        train = series.iloc[:val_start]
        val = series.iloc[val_start:val_end]
        train_val = series.iloc[:val_end]
        test = series.iloc[val_end:]

        print(f"\n{family} ({n}d)...")
        t0 = time.time()

        # WAPE de val por modelo (entrenando solo con train), para ponderar el ensamble
        val_wapes = {}
        for name, cls in [("arima", MODELS["arima"]), ("prophet", MODELS["prophet"]), ("xgboost", MODELS["xgboost"])]:
            try:
                pred_val = fit_predict(cls, train, len(val))
                val_wapes[name] = calculate_wape(val.values, pred_val.values[: len(val)])
            except Exception as exc:
                print(f"  ERROR val {name}: {exc}")
                val_wapes[name] = np.nan

        # Predicciones sobre TEST, entrenando con train_val (nunca vio test) -- igual
        # de honesto que el resto de las corridas
        test_preds = {}
        test_wapes = {}
        for name, cls in [("arima", MODELS["arima"]), ("prophet", MODELS["prophet"]), ("xgboost", MODELS["xgboost"])]:
            try:
                pred_test = fit_predict(cls, train_val, len(test))
                test_preds[name] = pred_test.values[: len(test)]
                test_wapes[name] = calculate_wape(test.values, test_preds[name])
            except Exception as exc:
                print(f"  ERROR test {name}: {exc}")
                test_preds[name] = None
                test_wapes[name] = np.nan

        valid = {k: v for k, v in test_preds.items() if v is not None}

        # Ensamble simple: promedio de las 3 predicciones de test
        ens_simple_wape = np.nan
        if len(valid) >= 2:
            stacked = np.mean(np.vstack(list(valid.values())), axis=0)
            ens_simple_wape = calculate_wape(test.values, stacked)

        # Ensamble ponderado por 1/wape_val (mas peso al que mejor valido)
        ens_weighted_wape = np.nan
        weights = {k: (1.0 / v) for k, v in val_wapes.items() if k in valid and np.isfinite(v) and v > 0}
        if len(weights) >= 2:
            wsum = sum(weights.values())
            stacked_w = sum(test_preds[k] * (w / wsum) for k, w in weights.items())
            ens_weighted_wape = calculate_wape(test.values, stacked_w)

        best_single = min(test_wapes, key=lambda k: test_wapes[k] if np.isfinite(test_wapes[k]) else np.inf)

        elapsed = time.time() - t0
        rows.append({
            "family": family,
            "arima_wape_test": round(test_wapes["arima"], 2) if np.isfinite(test_wapes["arima"]) else None,
            "prophet_wape_test": round(test_wapes["prophet"], 2) if np.isfinite(test_wapes["prophet"]) else None,
            "xgboost_wape_test": round(test_wapes["xgboost"], 2) if np.isfinite(test_wapes["xgboost"]) else None,
            "best_single_model": best_single,
            "best_single_wape_test": round(test_wapes[best_single], 2) if np.isfinite(test_wapes[best_single]) else None,
            "ensemble_simple_wape_test": round(ens_simple_wape, 2) if np.isfinite(ens_simple_wape) else None,
            "ensemble_weighted_wape_test": round(ens_weighted_wape, 2) if np.isfinite(ens_weighted_wape) else None,
        })
        print(f"  arima={test_wapes['arima']:.2f}%  prophet={test_wapes['prophet']:.2f}%  xgboost={test_wapes['xgboost']:.2f}%")
        print(f"  MEJOR INDIVIDUAL: {best_single} ({test_wapes[best_single]:.2f}%)")
        print(f"  ENSAMBLE simple: {ens_simple_wape:.2f}%   ENSAMBLE ponderado: {ens_weighted_wape:.2f}%   ({elapsed:.0f}s)")

    res = pd.DataFrame(rows)
    out = BASE_DIR / "resultados" / "pilot_ensemble_results.csv"
    res.to_csv(out, index=False)

    print(f"\n{'='*70}\nRESUMEN PILOTO ({len(res)} familias)\n{'='*70}")
    print(f"WAPE medio mejor individual:      {res['best_single_wape_test'].mean():.2f}%")
    print(f"WAPE medio ensamble simple:        {res['ensemble_simple_wape_test'].mean():.2f}%")
    print(f"WAPE medio ensamble ponderado:     {res['ensemble_weighted_wape_test'].mean():.2f}%")
    beats = (res["ensemble_simple_wape_test"] <= res["best_single_wape_test"]).sum()
    print(f"\nEnsamble simple iguala/mejora al mejor individual en {beats}/{len(res)} familias")
    print(f"\nGuardado en {out}")


if __name__ == "__main__":
    main()
