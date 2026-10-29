"""Genera los archivos de prueba del video demo. Uso: python3.11 docs/demo_video/generar_datos.py"""
import csv, random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).parent / "datos"
random.seed(7)

# familia: (base uds/dia, factor por dia de semana lun..dom, tendencia total en 6 meses)
FAM = {
    "BEBIDAS":    (180, [0.9, 0.9, 0.95, 1.0, 1.25, 1.45, 1.2], 0.15),
    "LACTEOS":    (120, [1.1, 1.05, 1.0, 1.0, 1.05, 0.95, 0.85], 0.05),
    "ABARROTES":  (260, [1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 0.7], 0.0),
    "PANADERIA":  (90,  [1.0, 1.0, 1.0, 1.0, 1.1, 1.3, None], 0.0),   # None = cerrado domingo
    "LIMPIEZA":   (70,  [1.0, 1.0, 1.05, 1.0, 1.1, 1.2, 0.6], 0.25),
    "CONGELADOS": (55,  [0.9, 0.9, 1.0, 1.0, 1.2, 1.4, 1.1], -0.1),
}
INICIO, DIAS = date(2026, 4, 1), 183  # 2026-04-01 .. 2026-09-30

with open(OUT / "ventas_demo_limpio.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["fecha", "familia", "ventas", "oferta"])
    for i in range(DIAS):
        d = INICIO + timedelta(days=i)
        for fam, (base, dow, trend) in FAM.items():
            fac = dow[d.weekday()]
            if fac is None:
                continue
            promo = random.random() < 0.08
            v = base * fac * (1 + trend * i / DIAS) * (1.25 if promo else 1) * random.uniform(0.9, 1.1)
            w.writerow([d.strftime("%d/%m/%Y"), fam, round(v), "si" if promo else "no"])

# Catalogo: sin fechas -> el backend lo clasifica como "products"
with open(OUT / "catalogo_demo.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Familia", "Costo unitario", "Costo de pedido", "Lead time (dias)", "MOQ"])
    for r in [("BEBIDAS", 650, 12000, 4, 24), ("LACTEOS", 900, 8000, 2, 12),
              ("ABARROTES", 1100, 15000, 5, 20), ("PANADERIA", 450, 5000, 1, 10),
              ("LIMPIEZA", 1800, 10000, 6, 12), ("CONGELADOS", 2400, 14000, 7, 8)]:
        w.writerow(r)

# Stock: sin fechas -> "stock". Mezcla de criticos y sanos para que Inventario muestre variedad
with open(OUT / "stock_demo.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Familia", "Stock actual"])
    for r in [("BEBIDAS", 120), ("LACTEOS", 60), ("ABARROTES", 1500), ("PANADERIA", 25),
              ("LIMPIEZA", 400), ("CONGELADOS", 30)]:
        w.writerow(r)

# Archivo con problemas: BEBIDAS mezcla mensual+diario (MIXED_GRANULARITY = error, bloquea)
# y hay fechas futuras (FUTURE_DATES = warning)
with open(OUT / "ventas_con_problemas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["fecha", "familia", "ventas"])
    for m in (1, 2, 3, 4):
        w.writerow([f"01/{m:02d}/2026", "BEBIDAS", 5400])
    for i in range(20):
        w.writerow([(date(2026, 5, 1) + timedelta(days=i)).strftime("%d/%m/%Y"), "BEBIDAS", 180 + i])
    for i in range(10):
        w.writerow([(date(2026, 12, 1) + timedelta(days=i)).strftime("%d/%m/%Y"), "LACTEOS", 120])
print("ok", sorted(p.name for p in OUT.iterdir()))
