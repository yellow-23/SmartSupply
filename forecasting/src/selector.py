import numpy as np
import pandas as pd

from forecasting.src.arima_model import ARIMAModel
from forecasting.src.prophet_model import ProphetModel
from forecasting.src.xgboost_model import XGBoostModel
from forecasting.src.lstm_model import LSTMModel


MODELS = {
    "arima": ARIMAModel,
    "prophet": ProphetModel,
    "xgboost": XGBoostModel,
    "lstm": LSTMModel,
}


def calculate_wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    WAPE = Σ|actual − predicted| / Σactual × 100

    Más robusta que MAPE ante demandas cercanas a cero, ya que pondera
    el error absoluto por el volumen total real en lugar de dividir
    observación a observación.
    """
    actual = np.array(actual, dtype=float)
    predicted = np.array(predicted, dtype=float)
    denom = actual.sum()
    if denom == 0:
        return np.nan
    return float(np.abs(actual - predicted).sum() / denom * 100)


def walk_forward_wape(
    series: pd.Series,
    ModelClass,
    horizon: int,
    n_splits: int = 3,
    min_train_ratio: float = 0.50,
) -> float:
    """
    Walk-forward cross-validation para un modelo dado.

    Divide la serie en ``n_splits`` ventanas rodantes:
      - Cada fold amplía el train en ``step`` días
      - El conjunto de validación siempre tiene ``horizon`` días
      - El train mínimo es ``min_train_ratio`` × len(series)

    Retorna el WAPE promedio entre folds (ignora folds fallidos).

    Ejemplo con n_splits=3, horizon=30 y 579 días:
      fold 1: train[0:346] → val[346:376]
      fold 2: train[0:376] → val[376:406]
      fold 3: train[0:406] → val[406:436]
    """
    n = len(series)
    min_train = int(n * min_train_ratio)
    max_train = n - horizon

    if max_train <= min_train:
        return np.nan

    # Puntos de corte equiespaciados entre min_train y max_train
    cutoffs = np.linspace(min_train, max_train, n_splits + 1, dtype=int)[:-1]

    fold_wapes: list[float] = []
    for cutoff in cutoffs:
        train = series.iloc[:cutoff]
        val = series.iloc[cutoff: cutoff + horizon]
        if len(val) < horizon:
            continue
        try:
            model_name = ModelClass.__name__.lower()
            fit_kwargs = {"epochs": 20} if "lstm" in model_name else {}
            m = ModelClass()
            m.fit(train, **fit_kwargs)
            pred = m.predict(horizon)
            w = calculate_wape(val.values, pred.values[:horizon])
            if np.isfinite(w):
                fold_wapes.append(w)
        except Exception:
            continue

    return float(np.mean(fold_wapes)) if fold_wapes else np.nan


class AutoModelSelector:
    """
    Automated Model Selector (AMS).

    Evaluación por defecto: split único 70/15/15 (rápido).
    Con ``cv=True``: walk-forward cross-validation de 3 folds (más robusto).

    En ambos casos reentrena el ganador sobre el 85% del historial
    y produce la predicción final sobre ``horizon`` días.
    """

    def __init__(self, horizon: int = 30, cv: bool = False, n_splits: int = 3, include_lstm: bool = False):
        self.horizon = horizon
        self.cv = cv
        self.n_splits = n_splits
        self.results: dict = {}
        self._models = {k: v for k, v in MODELS.items() if k != "lstm" or include_lstm}

    def select(self, series: pd.Series, sku_id: str = "SKU") -> dict:
        """
        Parámetros
        ----------
        series  : pd.Series con índice datetime y valores de ventas diarias.
        sku_id  : identificador del SKU (solo para logging).

        Retorna
        -------
        dict con claves: sku, model, wape, wape_cv, wapes_all, train, val,
                         test, val_preds, final_pred, winner_model.
        """
        n = len(series)
        train_end = int(n * 0.70)
        val_end = int(n * 0.85)

        train = series.iloc[:train_end]
        val = series.iloc[train_end:val_end]
        train_val = series.iloc[:val_end]

        wapes_single: dict[str, float] = {}
        wapes_cv: dict[str, float] = {}
        val_preds: dict[str, pd.Series] = {}

        for name, ModelClass in self._models.items():
            # ── Split único (siempre se calcula) ───────────────────────────
            try:
                m = ModelClass()
                fit_kwargs = {"epochs": 30} if name == "lstm" else {}
                m.fit(train, **fit_kwargs)
                pred = m.predict(len(val))
                pred_values = pred.values[: len(val)]
                wapes_single[name] = calculate_wape(val.values, pred_values)
                val_preds[name] = pred
            except Exception as exc:
                print(f"    [{name.upper():8s}] ERROR en split único: {exc}")
                wapes_single[name] = np.inf

            # ── Walk-forward CV (opcional) ─────────────────────────────────
            if self.cv:
                wapes_cv[name] = walk_forward_wape(
                    series, ModelClass, self.horizon, n_splits=self.n_splits
                )
                cv_val = wapes_cv[name]
                cv_str = f"{cv_val:.2f}%" if np.isfinite(cv_val) else "N/A"
                print(
                    f"    [{name.upper():8s}] WAPE_split = {wapes_single[name]:.2f}%"
                    f"  |  WAPE_cv({self.n_splits}f) = {cv_str}"
                )
            else:
                print(f"    [{name.upper():8s}] WAPE_val = {wapes_single[name]:.2f}%")

        # Métrica de ranking: CV si está activo, split único si no
        ranking = wapes_cv if self.cv else wapes_single
        best_name = min(
            ranking,
            key=lambda k: ranking[k] if np.isfinite(ranking.get(k, np.inf)) else np.inf,
        )

        # Reentrenar ganador sobre la serie COMPLETA (100%) y predecir horizonte futuro
        winner = self._models[best_name]()
        fit_kwargs = {"epochs": 50} if best_name == "lstm" else {}
        winner.fit(series, **fit_kwargs)
        final_pred = winner.predict(self.horizon)

        wape_final = (
            wapes_cv.get(best_name, wapes_single[best_name])
            if self.cv
            else wapes_single[best_name]
        )

        self.results = {
            "sku": sku_id,
            "model": best_name,
            "wape": round(wape_final, 2) if np.isfinite(wape_final) else None,
            "wape_cv": (
                round(wapes_cv[best_name], 2)
                if self.cv and np.isfinite(wapes_cv.get(best_name, np.nan))
                else None
            ),
            "wapes_all": {
                k: round(wapes_single[k], 2) if np.isfinite(wapes_single[k]) else None
                for k in wapes_single
            },
            "wapes_cv": (
                {k: round(wapes_cv[k], 2) if np.isfinite(wapes_cv.get(k, np.nan)) else None
                 for k in wapes_cv}
                if self.cv else {}
            ),
            "train": train,
            "val": val,
            "test": series.iloc[val_end:],
            "val_preds": val_preds,
            "final_pred": final_pred,
            "winner_model": winner,
        }
        return self.results
