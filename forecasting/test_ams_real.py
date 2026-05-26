"""
Test AMS completo con datos reales de Supabase.
Corre el AutoModelSelector sobre un SKU real y muestra análisis detallado.

Uso:
  python forecasting/test_ams_real.py                          # business 18, primera familia
  python forecasting/test_ams_real.py --list                   # listar familias disponibles
  python forecasting/test_ams_real.py --all                    # correr todas las familias
  python forecasting/test_ams_real.py --family "ABARROTES"     # familia específica
  python forecasting/test_ams_real.py --business 2 --all       # otro business
"""
import sys, os, time, argparse, warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv
load_dotenv(ROOT / "backend" / ".env")

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import date

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

from forecasting.src.selector import AutoModelSelector, calculate_wape


# ── Carga de datos ─────────────────────────────────────────────────────────────

def load_series(business_id: int, family: str, store_nbr: int) -> pd.Series:
    with Session() as db:
        rows = db.execute(
            text("""
                SELECT date, CAST(sales AS FLOAT)
                FROM sales_history
                WHERE business_id = :bid
                  AND family      = :fam
                  AND store_nbr   = :snbr
                  AND date        <= :today
                ORDER BY date
            """),
            {"bid": business_id, "fam": family, "snbr": store_nbr, "today": date.today()},
        ).fetchall()

    if not rows:
        raise ValueError(f"Sin datos: business={business_id}, family={family}, store={store_nbr}")

    dates  = pd.to_datetime([r[0] for r in rows])
    values = [float(r[1]) for r in rows]
    s = pd.Series(values, index=dates)
    return s.asfreq("D", fill_value=0.0)


def list_families(business_id: int) -> list[tuple[str, int, int]]:
    with Session() as db:
        rows = db.execute(
            text("""
                SELECT family, store_nbr, COUNT(*) AS n
                FROM sales_history
                WHERE business_id = :bid AND date <= :today
                GROUP BY family, store_nbr
                ORDER BY n DESC
            """),
            {"bid": business_id, "today": date.today()},
        ).fetchall()
    return [(r[0], int(r[1]), int(r[2])) for r in rows]


# ── Estadísticas descriptivas ──────────────────────────────────────────────────

DAY_NAMES = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]

def series_stats(s: pd.Series) -> dict:
    nonzero = s[s > 0]
    dow_idx = pd.to_datetime(s.index).dayofweek
    weekly = [(DAY_NAMES[d], float(s[dow_idx == d].mean()), float(s[dow_idx == d].std()))
              for d in range(7)]
    return {
        "n": len(s), "n_nz": len(nonzero),
        "start": s.index[0].strftime("%Y-%m-%d"),
        "end":   s.index[-1].strftime("%Y-%m-%d"),
        "mean": float(s.mean()), "median": float(nonzero.median()),
        "std":  float(s.std()),  "cv": float(s.std() / s.mean() * 100) if s.mean() > 0 else 0,
        "min":  float(s.min()),  "max": float(s.max()),
        "weekly": weekly,
        "is_clp": float(nonzero.median()) > 10_000,
    }


def print_header(title: str):
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print(f"{'=' * 62}")


def print_stats(st: dict):
    unit = "CLP" if st["is_clp"] else "uds"
    print(f"  Periodo  : {st['start']} -> {st['end']}  ({st['n']} dias, {st['n_nz']} con ventas)")
    print(f"  Media    : {st['mean']:>14,.1f} {unit}    CV={st['cv']:.1f}%")
    print(f"  Mediana  : {st['median']:>14,.1f} {unit}")
    print(f"  Std      : {st['std']:>14,.1f} {unit}")
    print(f"  Rango    : {st['min']:>14,.1f} - {st['max']:>14,.1f}")
    print(f"  Patron semanal (media historica):")
    for day, mean, std in st["weekly"]:
        bar = "#" * max(1, int(mean / st["mean"] * 20)) if st["mean"] > 0 else ""
        print(f"    {day}  {mean:>14,.0f}  +/-{std:>12,.0f}  {bar}")


def print_wape_table(wapes: dict[str, float | None], winner: str):
    print(f"\n  {'Modelo':<12} {'WAPE':>10}  Barra de error")
    print(f"  {'-'*12} {'-'*10}  {'-'*35}")
    sorted_w = sorted(
        wapes.items(),
        key=lambda x: x[1] if (x[1] is not None) else 9999,
    )
    for name, w in sorted_w:
        tag = " <- GANADOR" if name == winner else ""
        if w is not None:
            bar = "#" * min(35, max(1, int(w / 3)))
            print(f"  {name.upper():<12} {w:>9.2f}%  {bar}{tag}")
        else:
            print(f"  {name.upper():<12} {'N/A':>10}  (fallo){tag}")


def print_predictions(pred: pd.Series, hist_series: pd.Series, is_clp: bool, model: str):
    unit = "CLP" if is_clp else "uds"
    hist_mean = float(hist_series.mean())
    dow_idx   = pd.to_datetime(pred.index).dayofweek
    print(f"  Predicciones {len(pred)} dias - modelo {model.upper()}:")
    print(f"  {'Fecha':<12} {'Dia':<4} {'Prediccion':>16}  vs media hist.")
    print(f"  {'-' * 12} {'-' * 4} {'-' * 16}  {'-' * 20}")
    for d, v in pred.items():
        delta = (v - hist_mean) / hist_mean * 100 if hist_mean > 0 else 0
        sign  = "+" if delta >= 0 else ""
        print(f"  {d.strftime('%Y-%m-%d'):<12} {DAY_NAMES[d.dayofweek]:<4} {v:>16,.0f}  {sign}{delta:.1f}%")

    print(f"  +----------------------------------------------------------+")
    print(f"  |  Total {len(pred):2d} dias : {pred.sum():>14,.0f} {unit}")
    print(f"  |  Media diaria   : {pred.mean():>14,.0f} {unit}")
    print(f"  |  Media historica: {hist_mean:>14,.0f} {unit}")
    drift = (pred.mean() - hist_mean) / hist_mean * 100 if hist_mean > 0 else 0
    print(f"  |  Drift          : {drift:>+.1f}%")
    print(f"  +----------------------------------------------------------+")

    print(f"  Patron semanal predicho vs historico:")
    print(f"  {'Dia':<4} {'Predicho':>14}  {'Historico':>14}  {'Diferencia':>12}")
    print(f"  {'----':<4} {'-'*14}  {'-'*14}  {'-'*12}")
    hist_dow = pd.to_datetime(hist_series.index).dayofweek
    for d in range(7):
        pred_vals = pred.values[dow_idx == d]
        hist_vals = hist_series.values[hist_dow == d]
        if len(pred_vals) == 0:
            continue
        pm = float(np.mean(pred_vals))
        hm = float(np.mean(hist_vals)) if len(hist_vals) > 0 else 0
        diff_pct = (pm - hm) / hm * 100 if hm > 0 else 0
        print(f"  {DAY_NAMES[d]:<4} {pm:>14,.0f}  {hm:>14,.0f}  {diff_pct:>+11.1f}%")


def print_val_comparison(result: dict, is_clp: bool):
    """Compara predicciones de todos los modelos en el período de validación."""
    val_actual = result["val"]
    val_preds  = result["val_preds"]
    print(f"  Periodo de validacion ({len(val_actual)} dias): {val_actual.index[0].strftime('%Y-%m-%d')} -> {val_actual.index[-1].strftime('%Y-%m-%d')}")
    print(f"  {'Fecha':<12} {'Real':>14} ", end="")
    for name in val_preds:
        print(f"  {name.upper():>10}", end="")
    print()
    print(f"  {'-'*12} {'-'*14} ", end="")
    for _ in val_preds:
        print(f"  {'-'*10}", end="")
    print()
    # Solo mostrar primeros 14 días para no saturar
    limit = min(14, len(val_actual))
    for i, (d, actual) in enumerate(val_actual.items()):
        if i >= limit:
            if i == limit:
                print(f"  ... (y {len(val_actual) - limit} dias mas)")
            continue
        print(f"  {d.strftime('%Y-%m-%d'):<12} {actual:>14,.0f} ", end="")
        for name, pred_s in val_preds.items():
            if pred_s is not None and i < len(pred_s):
                print(f"  {pred_s.values[i]:>10,.0f}", end="")
            else:
                print(f"  {'N/A':>10}", end="")
        print()


# ── Runner principal ───────────────────────────────────────────────────────────

def run_analysis(business_id: int, family: str, store_nbr: int, horizon: int, cv: bool = False) -> dict | None:
    print_header(f"AMS  |  business={business_id}  |  SKU={family}  |  store={store_nbr}  |  h={horizon}d")

    # Cargar serie
    t0 = time.time()
    try:
        series = load_series(business_id, family, store_nbr)
    except Exception as e:
        print(f"\n  ERROR cargando datos: {e}")
        return None
    print(f"\n  Datos cargados en {time.time()-t0:.1f}s")

    st = series_stats(series)
    print_stats(st)

    if st["n"] < 91:
        print(f"  SKIP: serie muy corta ({st['n']} dias < 91 minimo para DIRMO)")
        return None

    # Correr AMS
    cv_label = f"walk-forward CV 3 folds" if cv else "split unico 70/15/15"
    print(f"\n{'-'*62}")
    print(f"  Corriendo AMS ({cv_label})...")
    print(f"{'-'*62}")
    ams = AutoModelSelector(horizon=horizon, cv=cv)
    t1 = time.time()
    result = ams.select(series, sku_id=family)
    elapsed = time.time() - t1

    print(f"\n  AMS completado en {elapsed:.1f}s")
    print(f"  +----------------------------------------------+")
    print(f"  |  GANADOR: {result['model'].upper():<10}  WAPE: {result['wape']:.2f}%           |")
    print(f"  +----------------------------------------------+")

    print(f"\n  Tabla WAPE todos los modelos:")
    print_wape_table(result["wapes_all"], result["model"])
    print_predictions(result["final_pred"], series, st["is_clp"], result["model"])

    print_val_comparison(result, st["is_clp"])

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--business", type=int, default=18)
    parser.add_argument("--family",   type=str, default=None)
    parser.add_argument("--store",    type=int, default=None)
    parser.add_argument("--horizon",  type=int, default=30)
    parser.add_argument("--cv",       action="store_true", help="Walk-forward CV de 3 folds")
    parser.add_argument("--list",     action="store_true")
    parser.add_argument("--all",      action="store_true")
    args = parser.parse_args()

    families = list_families(args.business)
    if not families:
        print(f"Sin datos para business_id={args.business}")
        return

    if args.list:
        print(f"\nFamilias - business_id={args.business}:")
        print(f"  {'Familia':<35} {'Store':>5} {'Dias':>6}")
        print(f"  {'-'*35} {'-'*5} {'-'*6}")
        for fam, store, n in families:
            print(f"  {fam:<35} {store:>5} {n:>6}")
        return

    if args.all:
        summary = []
        for fam, store, n in families:
            if n < 91:
                print(f"\n  SKIP {fam:<35} ({n} dias < 91)")
                continue
            r = run_analysis(args.business, fam, store, args.horizon, cv=args.cv)
            if r:
                summary.append((fam, r["model"], r["wape"]))

        print_header(f"RESUMEN GLOBAL - business_id={args.business}")
        print(f"\n  {'Familia':<35} {'Ganador':<12} {'WAPE':>8}")
        print(f"  {'-'*35} {'-'*12} {'-'*8}")
        counts: dict[str, int] = {}
        for fam, model, wape in sorted(summary, key=lambda x: x[2]):
            label = f"{wape:.2f}%" if wape is not None else "N/A"
            print(f"  {fam:<35} {model.upper():<12} {label:>8}")
            counts[model] = counts.get(model, 0) + 1
        if counts:
            print(f"\n  Distribucion ganadores:")
            for model, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                pct = cnt / len(summary) * 100
                print(f"    {model.upper():<12} {cnt} SKUs  ({pct:.0f}%)")
    else:
        fam   = args.family or families[0][0]
        store = args.store  or families[0][1]
        run_analysis(args.business, fam, store, args.horizon, cv=args.cv)


if __name__ == "__main__":
    main()
