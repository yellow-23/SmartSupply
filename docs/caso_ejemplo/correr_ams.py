"""
Corre el AMS sobre todas las familias de un business y guarda los resultados.

Uso:
  python docs/caso_ejemplo/correr_ams.py
  python docs/caso_ejemplo/correr_ams.py --business 18 --horizon 14
  python docs/caso_ejemplo/correr_ams.py --business 18 --all-models

Genera:
  docs/caso_ejemplo/resultados_ams.txt   — tabla legible
  docs/caso_ejemplo/resultados_ams.csv   — datos para la tesis
"""
import sys, os, warnings, argparse, time
from pathlib import Path
warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from dotenv import load_dotenv
load_dotenv(ROOT / "backend" / ".env")

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)

from forecasting.src.selector import AutoModelSelector, calculate_wape
from forecasting.src.arima_model import ARIMAModel


def load_series(business_id: int, store_nbr: int, family: str) -> pd.Series | None:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT sh.date, CAST(sh.sales AS FLOAT)
            FROM sales_history sh
            JOIN ingest_log il ON il.id = sh.ingest_id
            WHERE sh.business_id = :bid AND sh.store_nbr = :snbr
              AND sh.family = :fam AND il.status = 'active'
              AND sh.date <= CURRENT_DATE
            ORDER BY sh.date
        """), {"bid": business_id, "snbr": store_nbr, "fam": family}).fetchall()
    if not rows:
        return None
    dates = pd.to_datetime([r[0] for r in rows])
    s = pd.Series([float(r[1]) for r in rows], index=dates).asfreq("D", fill_value=0.0)
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--business", type=int, default=18)
    parser.add_argument("--store", type=int, default=1)
    parser.add_argument("--horizon", type=int, default=14)
    args = parser.parse_args()

    with engine.connect() as conn:
        families = [r[0] for r in conn.execute(text("""
            SELECT DISTINCT sh.family FROM sales_history sh
            JOIN ingest_log il ON il.id = sh.ingest_id
            WHERE sh.business_id = :bid AND sh.store_nbr = :snbr AND il.status = 'active'
            ORDER BY sh.family
        """), {"bid": args.business, "snbr": args.store}).fetchall()]

    print(f"\n{'='*70}")
    print(f"  AMS — Business {args.business} | Store {args.store} | Horizonte {args.horizon} días")
    print(f"  {len(families)} familias encontradas")
    print(f"{'='*70}")
    print(f"  {'Familia':<28} {'Ganador':<12} {'WAPE AMS':>9} {'WAPE ARIMA':>11} {'Mejora':>9}")
    print(f"  {'-'*67}")

    resultados = []
    for fam in families:
        t0 = time.time()
        s = load_series(args.business, args.store, fam)
        if s is None or len(s) < 60:
            print(f"  {fam:<28} — insuficientes datos ({len(s) if s is not None else 0} días)")
            continue

        n = len(s)
        train = s.iloc[:int(n * 0.70)]
        val = s.iloc[int(n * 0.70):int(n * 0.85)]

        # Baseline: ARIMA solo
        try:
            m = ARIMAModel()
            m.fit(train)
            pred = m.predict(len(val))
            wape_arima = calculate_wape(val.values, pred.values[:len(val)])
        except Exception:
            wape_arima = np.nan

        # AMS completo
        try:
            ams = AutoModelSelector(horizon=args.horizon)
            result = ams.select(s, sku_id=fam)
            winner = result["model"]
            wape_ams = result["wape"] or np.nan
            wapes_all = result.get("wapes_all", {})
        except Exception as e:
            winner, wape_ams, wapes_all = "ERROR", np.nan, {}

        elapsed = time.time() - t0
        mejora = wape_arima - wape_ams if np.isfinite(wape_arima) and np.isfinite(wape_ams) else np.nan

        wape_ams_s    = f"{wape_ams:.1f}%"    if np.isfinite(wape_ams)    else "N/A"
        wape_arima_s  = f"{wape_arima:.1f}%"  if np.isfinite(wape_arima)  else "N/A"
        mejora_s      = f"{mejora:+.1f}pp"    if np.isfinite(mejora)      else "N/A"

        print(f"  {fam:<28} {winner:<12} {wape_ams_s:>9} {wape_arima_s:>11} {mejora_s:>9}  ({elapsed:.0f}s)")
        resultados.append({
            "familia": fam, "dias": n, "ganador": winner,
            "wape_ams": round(wape_ams, 2) if np.isfinite(wape_ams) else None,
            "wape_arima": round(wape_arima, 2) if np.isfinite(wape_arima) else None,
            "mejora_pp": round(mejora, 2) if np.isfinite(mejora) else None,
            "wapes_por_modelo": wapes_all,
        })

    # Resumen global
    validos = [r for r in resultados if r["wape_ams"] and r["wape_arima"]]
    if validos:
        avg_ams   = np.mean([r["wape_ams"]   for r in validos])
        avg_arima = np.mean([r["wape_arima"] for r in validos])
        from collections import Counter
        ganadores = Counter(r["ganador"] for r in resultados if r["ganador"] != "ERROR")

        print(f"\n{'='*70}")
        print(f"  WAPE promedio  →  AMS: {avg_ams:.1f}%   ARIMA único: {avg_arima:.1f}%")
        print(f"  Mejora global: {avg_arima - avg_ams:+.1f} puntos porcentuales")
        print(f"  Modelos ganadores: {dict(ganadores)}")
        print(f"{'='*70}\n")

        # Guardar CSV para la tesis
        out_dir = Path(__file__).parent
        df = pd.DataFrame(resultados)
        df.to_csv(out_dir / "resultados_ams.csv", index=False)
        print(f"  → resultados_ams.csv guardado en {out_dir}")

        # Guardar tabla legible
        with open(out_dir / "resultados_ams.txt", "w") as f:
            f.write(f"AMS Results — Business {args.business} — Horizonte {args.horizon} días\n")
            f.write(f"{'='*70}\n")
            f.write(f"{'Familia':<28} {'Ganador':<12} {'WAPE AMS':>9} {'WAPE ARIMA':>11} {'Mejora':>9}\n")
            f.write(f"{'-'*70}\n")
            for r in resultados:
                f.write(f"{r['familia']:<28} {r['ganador']:<12} "
                        f"{str(r['wape_ams'])+'%':>9} {str(r['wape_arima'])+'%':>11} "
                        f"{('+' if r['mejora_pp'] and r['mejora_pp']>0 else '')+str(r['mejora_pp'])+'pp':>9}\n")
            f.write(f"{'='*70}\n")
            f.write(f"WAPE promedio: AMS={avg_ams:.1f}%  ARIMA={avg_arima:.1f}%  Mejora={avg_arima-avg_ams:+.1f}pp\n")
            f.write(f"Ganadores: {dict(ganadores)}\n")
        print(f"  → resultados_ams.txt guardado en {out_dir}")


if __name__ == "__main__":
    main()
