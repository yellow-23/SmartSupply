"""
ForecastService — SmartSupply
Capa de servicio que conecta los endpoints de la API con el motor AMS.

business_id == 1 es el dataset de benchmarking de Corporación Favorita (Kaggle):
se sigue leyendo desde el CSV procesado para no romper la validación de la tesis.
Cualquier otro business_id usa el historial real del usuario en Supabase.
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from datetime import date as date_type

from app.models.orm import IngestLog, SalesHistory
from app.models.schemas import ForecastResponse, ForecastPoint

# Agregar el root del repo al path para importar el módulo forecasting/
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROOT = os.path.dirname(_BACKEND_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# CSV de ventas limpias (solo se usa para business_id == 1: benchmark Kaggle)
_CSV_PATH = os.path.join(_ROOT, "datasets", "processed", "train_clean.csv")
_BENCHMARK_BUSINESS_ID = 1
_MIN_DAYS = 30

# Cache en memoria: clave -> (resultado, timestamp). TTL 1 hora.
_CACHE_TTL = int(os.getenv("FORECAST_CACHE_TTL", "3600"))  # override con env var para dev
_cache: dict[str, tuple] = {}
_cache_lock = threading.Lock()

# Cache de WAPE por SKU: (business_id, store_nbr, family) -> wape
# Se llena cada vez que el usuario corre un forecast. Leído por el dashboard.
_wape_cache: dict[tuple, float] = {}


def get_business_wapes(business_id: int) -> list[float]:
    """Retorna todos los WAPEs almacenados para un business. Vacío si aún no corrió ningún forecast."""
    with _cache_lock:
        return [v for (bid, _, _), v in _wape_cache.items() if bid == business_id]


class InsufficientDataError(Exception):
    """Se levanta cuando la serie no tiene los 90 días mínimos para el AMS."""

    def __init__(self, days_available: int, days_required: int = _MIN_DAYS):
        self.days_available = days_available
        self.days_required = days_required
        super().__init__(
            f"Serie insuficiente: {days_available} días disponibles, "
            f"se requieren al menos {days_required}."
        )


def _cache_key(business_id: int, sku_id: str, store_nbr: int, horizon_days: int, model: str) -> str:
    return f"{business_id}|{sku_id}|{store_nbr}|{horizon_days}|{model or 'auto'}"


def _load_series_from_db(
    db: Session,
    business_id: int,
    family: str,
    store_nbr: int,
) -> pd.Series:
    """
    Construye una serie diaria de ventas desde sales_history scoped por business_id.
    Solo cuenta cargas activas (ingest_log.status='active'); las revertidas se excluyen.
    Si dos cargas activas cubren el mismo dia, gana la mas reciente (mayor ingest_id).
    Devuelve un pd.Series indexado por fecha (frecuencia diaria, gaps en 0).
    """
    rows = (
        db.query(SalesHistory.date, SalesHistory.sales, SalesHistory.ingest_id)
        .join(IngestLog, IngestLog.id == SalesHistory.ingest_id)
        .filter(SalesHistory.business_id == business_id)
        .filter(SalesHistory.family == family)
        .filter(SalesHistory.store_nbr == store_nbr)
        .filter(SalesHistory.date <= date_type.today())
        .filter(IngestLog.status == "active")
        .order_by(SalesHistory.date)
        .all()
    )

    if not rows:
        raise InsufficientDataError(days_available=0)

    df = pd.DataFrame([
        {"date": r.date, "sales": float(r.sales), "ingest_id": r.ingest_id or 0}
        for r in rows
    ])
    df["date"] = pd.to_datetime(df["date"])
    # ultima gana: por fecha, conservar la fila de la carga mas reciente
    df = df.sort_values(["date", "ingest_id"]).drop_duplicates("date", keep="last")
    daily = df.set_index("date")["sales"].sort_index()
    daily = daily.asfreq("D", fill_value=0.0)
    return daily.clip(lower=0)


class ForecastService:
    """
    Servicio de predicción de demanda.
    Llama al motor AMS (forecasting/src/ams_pipeline.py) para cada request.
    Resultados se cachean en memoria por 1 hora (clave incluye business_id).
    """

    def predict(
        self,
        db: Session,
        business_id: int,
        sku_id: str,
        store_nbr: int,
        horizon_days: int,
        model: Optional[str] = "auto",
    ) -> ForecastResponse:
        key = _cache_key(business_id, sku_id, store_nbr, horizon_days, model or "auto")
        with _cache_lock:
            if key in _cache:
                result, ts = _cache[key]
                if time.monotonic() - ts < _CACHE_TTL:
                    return result

        from forecasting.src.ams_pipeline import run_ams_pipeline, load_sku_series
        from forecasting.src.selector import MODELS, calculate_wape

        # Cargar serie según fuente: CSV (Kaggle benchmark) o Supabase (usuario real)
        if business_id == _BENCHMARK_BUSINESS_ID:
            series = load_sku_series(_CSV_PATH, sku_family=sku_id, store_nbr=store_nbr)
            sales_unit = "units"
        else:
            series = _load_series_from_db(db, business_id, sku_id, store_nbr)
            # Detectar unidad predominante de esta serie
            unit_row = (
                db.query(SalesHistory.sales_unit)
                .filter(
                    SalesHistory.business_id == business_id,
                    SalesHistory.family == sku_id,
                    SalesHistory.store_nbr == store_nbr,
                )
                .first()
            )
            sales_unit = (unit_row.sales_unit if unit_row and unit_row.sales_unit else "units")

        if len(series) < _MIN_DAYS:
            raise InsufficientDataError(days_available=len(series))

        forced_model = None if model in ("auto", None) else model

        if forced_model:
            # Modo modelo forzado: entrena solo el modelo solicitado
            n = len(series)
            train_end = int(n * 0.70)
            val_end = int(n * 0.85)
            train = series.iloc[:train_end]
            val = series.iloc[train_end:val_end]
            train_val = series.iloc[:val_end]

            ModelClass = MODELS.get(forced_model)
            if ModelClass is None:
                raise ValueError(f"Modelo desconocido: '{forced_model}'. Opciones: {list(MODELS)}")

            fit_kwargs = {"epochs": 50} if forced_model == "lstm" else {}
            m = ModelClass()
            m.fit(train, **fit_kwargs)
            val_pred = m.predict(len(val))
            wape_val = calculate_wape(val.values, val_pred.values[:len(val)])

            m2 = ModelClass()
            m2.fit(series, **fit_kwargs)
            final_pred = m2.predict(horizon_days)

            model_used = forced_model
            wape_used = round(float(wape_val), 2) if np.isfinite(wape_val) else None
            pred_series = final_pred

        else:
            # Modo AMS completo (sin generar PNG, no lo usa el API)
            result = run_ams_pipeline(
                sku_id=sku_id,
                store_nbr=store_nbr,
                horizon=horizon_days,
                series=series,
                save_plot=False,
            )
            model_used = result["Modelo_Elegido"].lower()
            wape_used = result["WAPE"]
            pred_series = result["final_pred"]

        predictions = [
            ForecastPoint(
                date=idx.date() if hasattr(idx, "date") else idx,
                predicted_sales=round(float(val), 2),
            )
            for idx, val in pred_series.items()
        ]

        response = ForecastResponse(
            sku_id=sku_id,
            store_nbr=store_nbr,
            model_used=model_used,
            mape_validation=wape_used,
            horizon_days=horizon_days,
            predictions=predictions,
            generated_at=datetime.now(),
            sales_unit=sales_unit,
        )
        with _cache_lock:
            _cache[key] = (response, time.monotonic())
            if wape_used is not None:
                _wape_cache[(business_id, store_nbr, sku_id)] = wape_used
        return response
