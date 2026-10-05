# Validación de la hipótesis del AMS

Scripts y resultados de la validación estadística de la hipótesis central de
la tesis (capítulo 7.2). **No son parte del sistema en producción** —
`forecasting/src/` es el código que usa la API real; esta carpeta es material
de investigación para que los números reportados en la tesis sean
reproducibles y verificables, no una funcionalidad de SmartSupply.

## Qué se probó

Sobre las 33 familias de productos de la tienda 1 del dataset de
benchmarking Store Sales — Corporación Favorita (Kaggle), serie completa
2013-01-01 a 2017-08-15 (1.688 días por familia), partición cronológica
70% train / 15% val / 15% test:

1. **`run_favorita_validation.py`** — AMS con partición única (el criterio
   por defecto). Compara el AMS contra ARIMA, Prophet y XGBoost individuales
   y un baseline ingenuo estacional, con test de Wilcoxon pareado.
2. **`run_favorita_validation_cv.py`** — lo mismo, pero seleccionando el
   ganador con walk-forward de 3 folds en vez de partición única. Se corrió
   porque el resultado de (1) no confirmó la hipótesis, para descartar que
   fuera un problema de la ventana de selección.
3. **`pilot_ensemble.py`** — piloto de 6 familias: ¿promediar las
   predicciones de ARIMA+Prophet+XGBoost (en vez de elegir uno) rinde mejor?
   Salió peor — XGBoost arrastraba el promedio para abajo.
4. **`pilot_ensemble_ap.py`** — mismo piloto, pero solo ARIMA+Prophet (sin
   XGBoost). Mucho más prometedor.
5. **`run_favorita_ensemble_ap.py`** — el ensamble ARIMA+Prophet escalado a
   las 33 familias. Le gana de forma significativa a 2 de los 3 modelos
   individuales (excluyendo BOOKS, familia con 92,5% de días sin ventas
   donde el WAPE es matemáticamente inestable).
6. **`run_capital_inmovilizado.py`** — la otra mitad de la hipótesis: usa la
   predicción de cada estrategia (AMS, ensamble, cada modelo fijo) para
   fijar la política de inventario (s, S) de cada familia, vía
   `inventory/src/eoq.py` y `inventory/src/s_s_policy.py`, y simula esa
   política contra la demanda real del período de prueba con
   `inventory/src/simulator.py`, midiendo capital inmovilizado y nivel de
   servicio resultantes.

## Resultado (resumen — el detalle completo está en la tesis, capítulo 7.2)

- El AMS no le gana de forma estadísticamente significativa a usar Prophet o
  ARIMA solos, con ningún criterio de selección — sí le gana a XGBoost
  (el peor modelo del grupo).
- El modelo "ganador" cambia en el 55% de las familias según el criterio de
  selección usado — evidencia de que la selección captura ruido, no una
  diferencia real y estable entre modelos.
- El ensamble ARIMA+Prophet es el hallazgo más sólido: supera de forma
  significativa a 2 de los 3 modelos individuales.
- El mismo patrón (sin diferencia significativa del AMS) se repite en
  capital inmovilizado.

## Cómo correrlos

Desde la raíz del repo, con el venv activado:

```bash
python forecasting/experiments/validacion_hipotesis/run_favorita_validation.py
python forecasting/experiments/validacion_hipotesis/run_favorita_validation_cv.py
python forecasting/experiments/validacion_hipotesis/run_favorita_ensemble_ap.py
python forecasting/experiments/validacion_hipotesis/run_capital_inmovilizado.py
```

Cada script guarda sus resultados en `resultados/` de forma incremental
(fila por fila) y **reanuda solo** si se corta a mitad de camino — si ya
existe el CSV de salida, salta las familias ya calculadas. Para forzar una
corrida completa de nuevo, borrar el CSV correspondiente en `resultados/`
antes de correr.

**Tiempo (corrida desde cero, medido):** `run_favorita_validation.py` ~2,8 h,
`run_favorita_validation_cv.py` ~9,4 h (el walk-forward repite el ajuste en
3 folds), `run_favorita_ensemble_ap.py` ~2,5 h y `run_capital_inmovilizado.py`
~2 h. Lo que domina es el grid search de ARIMA (~150-200 s por familia);
XGBoost tarda ~30-40 s y Prophet ~1 s. La simulación de inventario es
instantánea. Los pilotos (6 familias) tardan 15-30 minutos.

Con los CSV de `resultados/` ya calculados, los cuatro scripts terminan en
segundos: solo saltan las familias hechas, imprimen el resumen y el test de
Wilcoxon, y reescriben los CSV consolidados.

## Estructura

```
validacion_hipotesis/
├── data/
│   └── store1_all_families.csv       # extraído del zip de Kaggle (tienda 1, 33 familias)
├── resultados/                        # CSVs de salida de cada script (ya calculados)
└── run_*.py, pilot_*.py               # los scripts en sí
```

## Nota sobre el dataset

Estos scripts usan `data/store1_all_families.csv` (1.688 días, 2013-2017),
extraído directo del zip de Kaggle. Esto es **distinto** del archivo que usa
`business_id=1` en producción (`datasets/processed/benchmark_store1.csv`,
592 días, 2016-2017) — son recortes distintos del mismo dataset, elegidos
por razones distintas (este por completitud estadística, el de producción
por tamaño de archivo).
