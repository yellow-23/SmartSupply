"""
InventoryService — SmartSupply
Conecta los endpoints de inventario con la BD real (Supabase) y los módulos inventory/src/.
"""

import os
import sys
from datetime import datetime, date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

# Agregar el root del repo al path para importar inventory/src/
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROOT = os.path.dirname(_BACKEND_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from inventory.src.eoq import EOQModel
from inventory.src.s_s_policy import SsPolicyModel
from inventory.src.simulator import InventorySimulator

from app.models.orm import IngestLog, Product, PurchaseOrder, SalesHistory, StockLevel
from app.models.schemas import InventoryMetrics, InventoryStatus

_DEFAULT_ORDER_COST = 5000.0
_DEFAULT_HOLDING_RATE = 0.25
_DEFAULT_LEAD_TIME = 7
_DEFAULT_UNIT_COST = 1.0   # fallback si no hay unit_cost; EOQ = 0 sin él


def _load_demand_series(
    db: Session,
    business_id: int,
    store_nbr: int,
    family: str,
    days: int,
) -> pd.Series:
    """
    Carga la serie de demanda diaria de los últimos `days` días desde sales_history,
    excluyendo cargas revertidas. Usa last-wins por ingest_id cuando hay solapes.
    Retorna pd.Series indexada por fecha con gaps en 0.
    """
    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(SalesHistory.date, SalesHistory.sales, SalesHistory.ingest_id)
        .join(IngestLog, IngestLog.id == SalesHistory.ingest_id)
        .filter(SalesHistory.business_id == business_id)
        .filter(SalesHistory.store_nbr == store_nbr)
        .filter(SalesHistory.family == family)
        .filter(SalesHistory.date >= cutoff)
        .filter(SalesHistory.date <= date.today())
        .filter(IngestLog.status == "active")
        .order_by(SalesHistory.date, SalesHistory.ingest_id)
        .all()
    )
    if not rows:
        return pd.Series(dtype=float)

    df = pd.DataFrame(rows, columns=["date", "sales", "ingest_id"])
    df["date"] = pd.to_datetime(df["date"])
    # last-wins: keep highest ingest_id per date
    df = df.sort_values("ingest_id").groupby("date", as_index=False).last()
    df = df.set_index("date").sort_index()
    full_idx = pd.date_range(df.index.min(), df.index.max(), freq="D")
    series = df["sales"].reindex(full_idx, fill_value=0.0)
    return series


def _get_product_params(db: Session, business_id: int, store_nbr: int, family: str) -> dict:
    """Carga parámetros de producto; usa defaults si no existe el registro."""
    p = (
        db.query(Product)
        .filter(
            Product.business_id == business_id,
            Product.store_nbr == store_nbr,
            Product.family == family,
        )
        .first()
    )
    if p is None:
        return {
            "unit_cost": _DEFAULT_UNIT_COST,
            "order_cost": _DEFAULT_ORDER_COST,
            "holding_rate": _DEFAULT_HOLDING_RATE,
            "lead_time_days": _DEFAULT_LEAD_TIME,
            "moq": 0.0,
        }
    return {
        "unit_cost": float(p.unit_cost) if p.unit_cost is not None else _DEFAULT_UNIT_COST,
        "order_cost": float(p.order_cost) if p.order_cost is not None else _DEFAULT_ORDER_COST,
        "holding_rate": float(p.holding_rate) if p.holding_rate is not None else _DEFAULT_HOLDING_RATE,
        "lead_time_days": p.lead_time_days if p.lead_time_days is not None else _DEFAULT_LEAD_TIME,
        "moq": float(p.moq) if p.moq is not None else 0.0,
    }


def _get_current_stock(db: Session, business_id: int, store_nbr: int, family: str) -> float:
    sl = (
        db.query(StockLevel)
        .filter(
            StockLevel.business_id == business_id,
            StockLevel.store_nbr == store_nbr,
            StockLevel.family == family,
        )
        .first()
    )
    return float(sl.quantity) if sl is not None and sl.quantity is not None else 0.0


def _calc_s_S(
    series: pd.Series,
    params: dict,
) -> tuple[float, float, float]:
    """Returns (s, S, eoq)."""
    unit_cost = params["unit_cost"]
    order_cost = params["order_cost"]
    holding_rate = params["holding_rate"]
    lead_time = params["lead_time_days"]

    if len(series) == 0:
        return 0.0, 0.0, 0.0

    daily_demand = float(series.mean())
    annual_demand = daily_demand * 365
    holding_cost = unit_cost * holding_rate

    eoq_model = EOQModel(annual_demand, order_cost, holding_cost)
    eoq = eoq_model.optimal_quantity()

    forecast_arr = np.array(series.values, dtype=float)
    ss_policy = SsPolicyModel(lead_time, holding_cost, order_cost)
    s = ss_policy.calculate_s(forecast_arr)
    S = ss_policy.calculate_S(s, eoq)

    return s, S, eoq


class InventoryService:

    def get_status(
        self, db: Session, business_id: int, store_nbr: int, family: str
    ) -> InventoryStatus:
        series = _load_demand_series(db, business_id, store_nbr, family, days=90)
        params = _get_product_params(db, business_id, store_nbr, family)
        current_stock = _get_current_stock(db, business_id, store_nbr, family)

        s, S, eoq = _calc_s_S(series, params)

        daily_demand = float(series.mean()) if len(series) > 0 else 0.0
        days_until_stockout = (
            round(current_stock / daily_demand, 1) if daily_demand > 0 else None
        )

        return InventoryStatus(
            sku_id=family,
            store_nbr=store_nbr,
            current_stock=current_stock,
            reorder_point_s=round(s, 2),
            order_up_to_S=round(S, 2),
            eoq=round(eoq, 2),
            policy="s_s",
            needs_reorder=current_stock <= s,
            days_until_stockout=days_until_stockout,
            updated_at=datetime.now(),
        )

    def get_metrics(
        self, db: Session, business_id: int, store_nbr: int, family: str, period_days: int
    ) -> InventoryMetrics:
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        series = _load_demand_series(db, business_id, store_nbr, family, days=period_days)
        params = _get_product_params(db, business_id, store_nbr, family)
        current_stock = _get_current_stock(db, business_id, store_nbr, family)

        if len(series) == 0:
            return InventoryMetrics(
                sku_id=family,
                store_nbr=store_nbr,
                period_start=start_date,
                period_end=end_date,
                capital_inmovilizado=0.0,
                stockout_rate=0.0,
                inventory_turnover=0.0,
                service_level=0.0,
                total_inventory_cost=0.0,
            )

        s, S, _ = _calc_s_S(series, params)
        unit_cost = params["unit_cost"]
        holding_rate = params["holding_rate"]
        order_cost = params["order_cost"]
        lead_time = params["lead_time_days"]

        sim = InventorySimulator(unit_cost, holding_rate, order_cost)
        result = sim.run(series, "s_s", s, S, current_stock, lead_time)

        return InventoryMetrics(
            sku_id=family,
            store_nbr=store_nbr,
            period_start=start_date,
            period_end=end_date,
            capital_inmovilizado=round(result["capital_inmovilizado"], 2),
            stockout_rate=round(result["stockout_rate"] * 100, 2),
            inventory_turnover=round(result["inventory_turnover"], 2),
            service_level=round(result["service_level"] * 100, 2),
            total_inventory_cost=round(result["total_inventory_cost"], 2),
        )

    def get_critical_skus(
        self, db: Session, business_id: int, store_nbr: int
    ) -> list[dict]:
        """
        Retorna todos los SKUs cuyo stock actual <= punto de reorden (s).
        Deriva familias desde sales_history; stock desde stock_levels (0 si no existe).
        """
        families = [
            row[0]
            for row in (
                db.query(SalesHistory.family)
                .join(IngestLog, IngestLog.id == SalesHistory.ingest_id)
                .filter(
                    SalesHistory.business_id == business_id,
                    SalesHistory.store_nbr == store_nbr,
                    IngestLog.status == "active",
                )
                .distinct()
                .all()
            )
        ]

        stock_map = {
            sl.family: float(sl.quantity) if sl.quantity is not None else 0.0
            for sl in db.query(StockLevel).filter(
                StockLevel.business_id == business_id,
                StockLevel.store_nbr == store_nbr,
            ).all()
        }

        critical = []
        for family in families:
            current_stock = stock_map.get(family, 0.0)
            series = _load_demand_series(db, business_id, store_nbr, family, days=90)
            params = _get_product_params(db, business_id, store_nbr, family)
            s, S, eoq = _calc_s_S(series, params)

            if current_stock <= s:
                moq = params["moq"]
                order_qty = max(S - current_stock, moq)
                critical.append(
                    {
                        "family": family,
                        "current_stock": current_stock,
                        "reorder_point_s": round(s, 2),
                        "order_up_to_S": round(S, 2),
                        "order_quantity": round(order_qty, 2),
                    }
                )

        return critical
