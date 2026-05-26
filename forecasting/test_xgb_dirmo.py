"""
Test rápido del XGBoostModel DIRMO.
Compara WAPE vs el enfoque iterativo previo usando una serie con patrón semanal.
"""
import sys, time
sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from forecasting.src.xgboost_model import XGBoostModel


def wape(actual, predicted):
    return float(np.sum(np.abs(actual - predicted)) / (np.sum(np.abs(actual)) + 1e-8) * 100)


# ── Serie sintética: patrón semanal + ruido, 300 días ────────────────────────
np.random.seed(42)
n = 300
dates = pd.date_range("2024-01-01", periods=n)
weekly = np.tile([500_000, 520_000, 510_000, 490_000, 480_000, 200_000, 150_000], 50)[:n]
noise  = np.random.normal(0, 25_000, n)
series = pd.Series(weekly.astype(float) + noise, index=dates)

# ── Split 70/15/15 ────────────────────────────────────────────────────────────
train_end = int(n * 0.70)
val_end   = int(n * 0.85)
train = series.iloc[:train_end]
val   = series.iloc[train_end:val_end]

print(f"Serie: {n} dias | train={len(train)} | val={len(val)}")
print()

# ── Fit ───────────────────────────────────────────────────────────────────────
m = XGBoostModel()
t0 = time.time()
m.fit(train)
elapsed = time.time() - t0
print(f"Fit completado en {elapsed:.1f}s | modelos entrenados: {len(m.models)}")

# ── WAPE en validación ────────────────────────────────────────────────────────
pred_val = m.predict(len(val))
w = wape(val.values, pred_val.values)
print(f"WAPE validación ({len(val)} días): {w:.2f}%")

# ── Predicción 30 días ────────────────────────────────────────────────────────
m2 = XGBoostModel()
m2.fit(series.iloc[:val_end])
pred30 = m2.predict(30)

print()
print("Predicciones 30 días (Direct DIRMO):")
for d, v in pred30.items():
    print(f"  {d.strftime('%a %Y-%m-%d')}: {v:>12,.0f}")

# ── Verificar no hay zeros ni colapso ─────────────────────────────────────────
zeros = (pred30 == 0).sum()
min_v = pred30.min()
max_v = pred30.max()
print()
print(f"Zeros: {zeros} | Min: {min_v:,.0f} | Max: {max_v:,.0f}")
print("OK: sin colapso a cero" if zeros == 0 else "WARNING: hay predicciones en cero")
