# Ejecución del módulo de forecasting

> Todos los comandos se ejecutan desde la raíz del proyecto `SmartSupply/`.

## Requisitos

```bash
py -3.13 -m pip install -r forecasting/requirements.txt
```

## 1 — Pipeline AMS para un solo SKU

```bash
py -3.13 -m forecasting.src.ams_pipeline \
  --csv datasets/processed/train_clean.csv \
  --sku "GROCERY I" \
  --store 1
```

Parámetros opcionales:

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `--horizon` | Días a predecir | 30 |
| `--output` | Carpeta de salida | `forecasting/outputs/` |
| `--cv` | Activa walk-forward cross-validation (3 folds) | desactivado |
| `--order-cost` | Costo de emitir una orden ($) | 50000 |
| `--holding-cost` | Costo de almacenamiento diario por unidad ($) | 1200 |
| `--lead-time` | Lead time en días | 7 |

Ejemplo con todas las opciones:

```bash
py -3.13 -m forecasting.src.ams_pipeline \
  --csv datasets/processed/train_clean.csv \
  --sku "BEVERAGES" \
  --store 3 \
  --horizon 30 \
  --cv \
  --output forecasting/outputs/
```

Salida generada:
- `forecasting/outputs/ams_<SKU>_<store>.png` — gráfico con train/val/test + predicción
- Resultado en consola con modelo elegido, WAPE, EOQ, Stock de Seguridad, ROP

---

## 2 — Validación batch (múltiples SKUs)

### Muestra aleatoria

```bash
py -3.13 etl/scripts/05_batch_ams_validation.py --sample 10 --seed 42
```

### SKUs y tiendas específicas

```bash
py -3.13 etl/scripts/05_batch_ams_validation.py \
  --skus "GROCERY I" "BEVERAGES" "MEATS" \
  --stores 1 2 3
```

### Todos los SKU/tienda disponibles

```bash
py -3.13 etl/scripts/05_batch_ams_validation.py --all
```

### Con cross-validation

```bash
py -3.13 etl/scripts/05_batch_ams_validation.py --sample 20 --cv --seed 42
```

Salida generada:
- `forecasting/outputs/batch_results_<timestamp>.csv` — tabla con modelo, WAPE y parámetros de inventario por SKU
- `forecasting/outputs/batch_summary.png` — gráfico 3 paneles: histograma WAPE, distribución de modelos elegidos, comparación AMS vs modelos individuales

---

## 3 — Modelos individuales (uso directo)

```python
import pandas as pd
from forecasting.src.arima_model import ARIMAModel
from forecasting.src.prophet_model import ProphetModel
from forecasting.src.xgboost_model import XGBoostModel
from forecasting.src.lstm_model import LSTMModel

series = pd.read_csv("datasets/processed/train_clean.csv", parse_dates=["date"])
series = series[(series["family"] == "GROCERY I") & (series["store_nbr"] == 1)]
series = series.groupby("date")["sales"].sum().asfreq("D", fill_value=0)

model = XGBoostModel()
model.fit(series)
pred = model.predict(horizon=30)  # pd.Series con 30 días
```

---

## 4 — Selector AMS directo

```python
from forecasting.src.selector import AutoModelSelector

selector = AutoModelSelector(horizon=30, cv=False)
result = selector.select(series, sku_id="GROCERY I_1")

print(result["model"])       # nombre del modelo ganador
print(result["wape"])        # WAPE en validación
print(result["final_pred"])  # pd.Series con predicción 30d
```

Con walk-forward CV:

```python
selector = AutoModelSelector(horizon=30, cv=True, n_splits=3)
result = selector.select(series, sku_id="GROCERY I_1")
print(result["wape_cv"])     # WAPE promedio cross-validation
```
