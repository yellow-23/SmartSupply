from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.admin import update_user, AdminUserUpdate
from app.api.forecast import export_forecast_pdf
from app.api.sales import get_date_range, get_sales_history, get_sales_summary


def _no_membership_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


@pytest.mark.parametrize("call", [
    lambda db: get_date_range(MagicMock(id=1), 999, db),
    lambda db: get_sales_history(MagicMock(id=1), 999, "PAN", None, None, None, db),
    lambda db: get_sales_summary(MagicMock(id=1), 999, None, None, None, db),
])
def test_sales_reads_require_membership(call):
    with pytest.raises(HTTPException) as exc:
        call(_no_membership_db())
    assert exc.value.status_code == 403


def test_admin_cannot_deactivate_or_demote_self():
    me = MagicMock(id=7)
    for body in (AdminUserUpdate(is_active=False), AdminUserUpdate(role="analyst")):
        with pytest.raises(HTTPException) as exc:
            update_user(7, body, me, MagicMock())
        assert exc.value.status_code == 400


def test_export_without_cached_forecast_is_409():
    with pytest.raises(HTTPException) as exc:
        export_forecast_pdf("NO-EXISTE", MagicMock(id=1), 1, 14, "auto", 1, MagicMock())
    assert exc.value.status_code == 409


def test_create_store_requires_owner():
    from app.api.businesses import create_business_store
    from app.models.schemas import StoreCreate
    with pytest.raises(HTTPException) as exc:
        create_business_store(999, StoreCreate(name="Sucursal"), MagicMock(id=1, role="business_admin"), _no_membership_db())
    assert exc.value.status_code == 403


def test_generate_orders_skips_open_and_rounds(monkeypatch):
    from app.api import orders
    monkeypatch.setattr(orders, "assert_business_access", lambda *a: None)
    monkeypatch.setattr(orders.service, "get_critical_skus", lambda **k: [
        {"family": "ABARROTES", "order_quantity": 1068.52, "current_stock": 712.4,
         "reorder_point_s": 815.84, "order_up_to_S": 1780.6},
        {"family": "BEBIDAS", "order_quantity": 900.1, "current_stock": 500.0,
         "reorder_point_s": 593.38, "order_up_to_S": 1400.2},
    ])
    monkeypatch.setattr("app.services.inventory_service._get_product_params", lambda *a: {"lead_time_days": 7})
    db = MagicMock()
    db.query.return_value.filter.return_value.distinct.return_value = [("ABARROTES",)]
    created = orders.generate_automatic_orders(9, 1, MagicMock(id=1), db)
    assert [(o.family, o.quantity, o.reorder_point_s) for o in created] == [("BEBIDAS", 901, 593)]
