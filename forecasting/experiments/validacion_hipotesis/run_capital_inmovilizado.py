"""
Prueba de capital inmovilizado (la segunda mitad de la hipotesis).
Pregunta: aunque el WAPE haya quedado parejo entre estrategias, ¿la ELECCION
del modelo (AMS / ensamble / modelo fijo) cambia el capital inmovilizado real
que resulta de usarlo para fijar la politica de inventario (s, S)?

Metodologia por familia (33 familias, tienda 1, Favorita):
  1. Se entrena ARIMA, Prophet y XGBoost SOLO con train+val (85%, nunca vieron
     el 15% de prueba) y se predice sobre todo el periodo de prueba (~253
     dias) -- misma logica honesta que el resto de la sesion.
  2. Se arma tambien el ensamble ARIMA+Prophet (promedio simple) y la
     estrategia "AMS" (la prediccion del modelo que el AMS elegiria para
     esa familia, tomado de favorita_validation_results.csv).
  3. Para cada estrategia, esa prediccion se usa para calcular el punto de
     reorden (s) y el nivel objetivo (S) via SsPolicyModel + EOQModel, con
     costos constantes entre estrategias (unit_cost=1000 CLP, order_cost=5000,
     holding_rate=0.25, lead_time=7 dias) para que la comparacion sea justa.
     Ojo: unit_cost no es el de produccion (1.0) -- ver la nota en UNIT_COST.
  4. Esa politica (s, S) se corre con InventorySimulator sobre la demanda
     REAL del periodo de prueba (no la predicha) -- mide que hubiera pasado
     de verdad si el negocio hubiese fijado su inventario con esa prediccion.

Guarda incremental (resume si se corta). No toca Supabase.
Las familias sin ventas en todo el periodo (BABY CARE) se saltan antes de
entrenar: no generan filas, asi que sin ese salto se reentrenarian en cada
corrida (~4 min de ARIMA + XGBoost para nada).
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

from forecasting.src.selector import MODELS
from inventory.src.eoq import EOQModel
from inventory.src.s_s_policy import SsPolicyModel
from inventory.src.simulator import InventorySimulator

INPUT_CSV = BASE_DIR / "data" / "store1_all_families.csv"
AMS_RESULTS_CSV = BASE_DIR / "resultados" / "favorita_validation_results.csv"  # trae ams_winner por familia
OUTPUT_CSV = BASE_DIR / "resultados" / "capital_inmovilizado_results.csv"

UNIT_COST = 1000.0  # placeholder generico (CLP) -- Favorita no trae costos reales.
                     # Con el fallback real de produccion (1.0) el EOQ se dispara
                     # a decenas de miles de unidades (bug ya documentado en
                     # CLAUDE.md) y el experimento deja de poder distinguir entre
                     # estrategias. 1000 CLP da una cobertura de ~1 mes, un
                     # regimen realista de retail. Es constante entre estrategias
                     # y familias, asi que no distorsiona la comparacion relativa
                     # (que es lo que se esta midiendo), solo la escala absoluta.
ORDER_COST = 5000.0
HOLDING_RATE = 0.25
LEAD_TIME = 7
SERVICE_LEVEL = 0.95


def fit_predict(model_cls, train_series: pd.Series, horizon: int):
    m = model_cls()
    m.fit(train_series)
    pred = m.predict(horizon).values[:horizon]
    return np.clip(pred, 0, None)  # la demanda no puede ser negativa


def policy_from_forecast(forecast: np.ndarray) -> tuple[float, float]:
    """Calcula (s, S) a partir de un forecast, con los parametros de costo
    por defecto de produccion."""
    holding_cost = UNIT_COST * HOLDING_RATE
    ss_model = SsPolicyModel(lead_time=LEAD_TIME, holding_cost=holding_cost, order_cost=ORDER_COST)
    s = ss_model.calculate_s(forecast, service_level=SERVICE_LEVEL)
    annual_demand = float(np.mean(forecast)) * 365
    eoq = EOQModel(demand=annual_demand, order_cost=ORDER_COST, holding_cost=holding_cost).optimal_quantity()
    S = ss_model.calculate_S(s, eoq)
    return s, S


def simulate(real_demand: pd.Series, s: float, S: float) -> dict:
    sim = InventorySimulator(unit_cost=UNIT_COST, holding_rate=HOLDING_RATE, order_cost=ORDER_COST)
    return sim.run(real_demand, policy="s_s", s=s, S=S, initial_stock=S, lead_time=LEAD_TIME)


def main():
    df = pd.read_csv(INPUT_CSV, parse_dates=["date"])
    ams_info = pd.read_csv(AMS_RESULTS_CSV).set_index("family")["ams_winner"].to_dict()
    families = sorted(df["family"].unique())

    fieldnames = ["family", "n_days", "strategy", "s", "S",
                  "capital_inmovilizado", "stockout_rate", "service_level",
                  "inventory_turnover", "total_inventory_cost", "num_orders",
                  "avg_order_quantity"]

    done_families: set[str] = set()
    if OUTPUT_CSV.exists():
        prev = pd.read_csv(OUTPUT_CSV)
        done_families = set(prev["family"].unique().tolist())
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
        if (series == 0).all():
            print(f"[{i:2d}/{len(pending)}] {family:<28} sin ventas en todo el periodo, se salta")
            continue
        val_end = int(n * 0.85)
        train_val = series.iloc[:val_end]
        test = series.iloc[val_end:]

        print(f"[{i:2d}/{len(pending)}] {family:<28} ({n}d) ...", end=" ", flush=True)
        t0 = time.time()

        preds = {}
        for name, cls in [("arima", MODELS["arima"]), ("prophet", MODELS["prophet"]), ("xgboost", MODELS["xgboost"])]:
            try:
                preds[name] = fit_predict(cls, train_val, len(test))
            except Exception as exc:
                print(f"\n      ERROR {name}: {exc}")
                preds[name] = None

        strategies: dict[str, np.ndarray] = {}
        for name in ("arima", "prophet", "xgboost"):
            if preds.get(name) is not None:
                strategies[name] = preds[name]
        if preds.get("arima") is not None and preds.get("prophet") is not None:
            strategies["ensemble_ap"] = np.mean(np.vstack([preds["arima"], preds["prophet"]]), axis=0)
        winner = ams_info.get(family)
        if winner and preds.get(winner) is not None:
            strategies["ams"] = preds[winner]

        rows_this_family = []
        for strat_name, forecast in strategies.items():
            try:
                if np.allclose(forecast, 0):
                    # Serie sin demanda (ej. BABY CARE): politica degenerada, no simular.
                    continue
                s, S = policy_from_forecast(forecast)
                metrics = simulate(test, s, S)
                rows_this_family.append({
                    "family": family, "n_days": n, "strategy": strat_name,
                    "s": round(s, 2), "S": round(S, 2),
                    **{k: round(v, 4) for k, v in metrics.items()},
                })
            except Exception as exc:
                print(f"\n      ERROR simulando {strat_name}: {exc}")

        for row in rows_this_family:
            writer.writerow(row)
        out_f.flush()

        elapsed = time.time() - t0
        total_elapsed = time.time() - t_start
        eta = total_elapsed / i * (len(pending) - i)
        cap_ams = next((r["capital_inmovilizado"] for r in rows_this_family if r["strategy"] == "ams"), None)
        cap_ens = next((r["capital_inmovilizado"] for r in rows_this_family if r["strategy"] == "ensemble_ap"), None)
        print(f"AMS_cap={cap_ams} ens_cap={cap_ens}  ({elapsed:.0f}s, ETA {eta/60:.0f}min)")

    out_f.close()
    print(f"\nTotal: {(time.time()-t_start)/60:.1f} min. Resultados en {OUTPUT_CSV}")

    # ── Resumen + Wilcoxon ──────────────────────────────────────────────────
    res = pd.read_csv(OUTPUT_CSV)
    pivot = res.pivot_table(index="family", columns="strategy", values="capital_inmovilizado")
    svc = res.pivot_table(index="family", columns="strategy", values="service_level")
    strategies_order = [s for s in ["ams", "ensemble_ap", "arima", "prophet", "xgboost"] if s in pivot.columns]

    print(f"\n{'='*70}\nCAPITAL INMOVILIZADO -- resumen ({len(pivot.dropna())} familias completas)\n{'='*70}")
    print(f"\n{'Estrategia':<16}{'Capital medio':>16}{'Capital mediana':>18}{'Nivel servicio medio':>24}")
    for s in strategies_order:
        cap_mean = pivot[s].mean()
        cap_med = pivot[s].median()
        svc_mean = svc[s].mean() * 100 if s in svc.columns else float("nan")
        print(f"{s:<16}{cap_mean:>15.1f} {cap_med:>17.1f} {svc_mean:>23.1f}%")

    valid = pivot.dropna()
    print(f"\n{'='*70}\nTEST DE WILCOXON (capital inmovilizado, pareado por familia)\n{'='*70}")
    base = "ams" if "ams" in valid.columns else strategies_order[0]
    for s in strategies_order:
        if s == base:
            continue
        try:
            stat, p = wilcoxon(valid[base], valid[s])
            direction = f"{base} MENOS capital" if valid[base].mean() < valid[s].mean() else f"{base} MAS capital"
            sig = "SI (p<0.05)" if p < 0.05 else "no"
            print(f"  {base} vs {s:<14} p={p:.4f}  sig={sig:12s} ({direction})")
        except Exception as exc:
            print(f"  {base} vs {s:<14} ERROR: {exc}")

    pivot.to_csv(BASE_DIR / "resultados" / "capital_inmovilizado_pivot.csv")
    print(f"\nPivot guardado en capital_inmovilizado_pivot.csv")


if __name__ == "__main__":
    main()
