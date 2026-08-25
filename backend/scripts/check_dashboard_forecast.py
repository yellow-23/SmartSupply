"""
Self-check: get_business_cached_forecasts dedup logic (usada por dashboard.chart-data).
Uso: cd backend && python3.11 scripts/check_dashboard_forecast.py
"""
import sys, os
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models.schemas import ForecastPoint, ForecastResponse
from app.services import forecast_service as fs


def _fake(business_id, sku_id, store_nbr, generated_at, value):
    key = fs._cache_key(business_id, sku_id, store_nbr, 14, "prophet")
    response = ForecastResponse(
        sku_id=sku_id,
        store_nbr=store_nbr,
        model_used="prophet",
        mape_validation=10.0,
        horizon_days=14,
        predictions=[ForecastPoint(date=date(2026, 9, 1), predicted_sales=value)],
        generated_at=generated_at,
        sales_unit="units",
    )
    fs._cache[key] = (response, 0.0)


if __name__ == "__main__":
    fs._cache.clear()

    # Mismo SKU, dos corridas: debe quedar solo la mas reciente (100, no 50)
    _fake(1, "PAN", 1, datetime(2026, 1, 1), 50.0)
    _fake(1, "PAN", 1, datetime(2026, 1, 2), 100.0)
    # SKU distinto, mismo negocio: debe sumarse aparte
    _fake(1, "LACTEOS", 1, datetime(2026, 1, 1), 30.0)
    # Otro negocio: no debe aparecer
    _fake(2, "PAN", 1, datetime(2026, 1, 1), 999.0)

    result = fs.get_business_cached_forecasts(1)
    by_sku = {r.sku_id: r.predictions[0].predicted_sales for r in result}

    assert len(result) == 2, f"esperaba 2 SKUs para business 1, salio {len(result)}"
    assert by_sku["PAN"] == 100.0, f"deberia quedar la corrida mas reciente (100), salio {by_sku['PAN']}"
    assert by_sku["LACTEOS"] == 30.0
    assert fs.get_business_cached_forecasts(2)[0].predictions[0].predicted_sales == 999.0
    assert fs.get_business_cached_forecasts(3) == []

    fs._cache.clear()
    print("OK: get_business_cached_forecasts dedup por SKU + aislamiento por business_id")
