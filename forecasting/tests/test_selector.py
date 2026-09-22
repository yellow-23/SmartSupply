"""
Pruebas de AutoModelSelector.select() enfocadas en el WAPE reportado, no en la
calidad de los modelos reales (ARIMA/Prophet/XGBoost/LSTM son lentos y no
deterministas, asi que se inyecta un modelo falso y rapido via `_models`).

Corre con: pytest forecasting/tests/ (desde la raiz del repo, con PYTHONPATH=.)
"""
import numpy as np
import pandas as pd
import pytest

from forecasting.src.selector import AutoModelSelector


class DummyModel:
    """Modelo determinista: predice la media del set con que fue entrenado.
    Registra el largo de cada serie con que se llamo fit(), para poder
    verificar CON QUE PARTICION se entrena cada fase del selector."""

    fit_calls: list[int] = []

    def __init__(self):
        self._mean = 0.0

    def fit(self, series, **kwargs):
        DummyModel.fit_calls.append(len(series))
        self._mean = float(series.mean())

    def predict(self, horizon):
        idx = pd.date_range("2030-01-01", periods=horizon, freq="D")
        return pd.Series([self._mean] * horizon, index=idx)


class FlakyModel(DummyModel):
    """Igual que DummyModel, pero el fit falla la 3ra vez que se llama (que es
    siempre el fit adicional usado para medir wape_test, ver orden en select())."""

    call_count = 0

    def fit(self, series, **kwargs):
        FlakyModel.call_count += 1
        if FlakyModel.call_count == 3:
            raise RuntimeError("fit fallido a proposito, para probar el fallback")
        super().fit(series, **kwargs)


def _make_series(n=100):
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    values = np.arange(n, dtype=float)  # tendencia simple: sube 1/dia
    return pd.Series(values, index=idx)


def test_wape_reported_is_measured_on_test_window():
    """El WAPE final debe medirse sobre el 15% de PRUEBA (test), reentrenando
    el ganador solo con train+val — nunca sobre val, que es con lo que se
    eligio el modelo (eso inflaria el numero a favor del propio criterio)."""
    DummyModel.fit_calls = []
    series = _make_series(100)
    ams = AutoModelSelector(horizon=15, cv=False)
    ams._models = {"dummy": DummyModel}

    result = ams.select(series, sku_id="TEST")

    assert result["model"] == "dummy"
    assert result["wape_test"] is not None
    assert result["wape_selection"] is not None
    assert result["wape"] == result["wape_test"]

    # train=[0:70) val=[70:85) test=[85:100): se espera un fit con 70 obs
    # (evaluacion split unico), uno con 100 (reentreno final para predecir el
    # horizonte futuro) y uno con 85 = train+val (para medir wape_test sin
    # haber visto las 15 obs de test).
    assert sorted(DummyModel.fit_calls) == [70, 85, 100]


def test_wape_falls_back_to_selection_wape_if_test_fit_fails():
    """Si el fit adicional sobre train+val falla, wape_test queda en None y el
    WAPE reportado cae de vuelta al de seleccion, en vez de quedar vacio."""
    FlakyModel.call_count = 0
    series = _make_series(100)
    ams = AutoModelSelector(horizon=15, cv=False)
    ams._models = {"dummy": FlakyModel}

    result = ams.select(series, sku_id="TEST")

    assert result["wape_test"] is None
    assert result["wape_selection"] is not None
    assert result["wape"] == result["wape_selection"]
