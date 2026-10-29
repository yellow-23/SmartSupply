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
    monkeypatch.setattr(orders, "_get_product_params", lambda *a: {"lead_time_days": 7, "unit_cost": 500.0, "supplier": "CCU"})
    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.distinct.return_value = [("ABARROTES",)]
    created = orders.generate_automatic_orders(9, 1, MagicMock(id=1), db)
    assert [o.supplier for o in created] == ["CCU"]
    assert [(l.family, l.quantity, l.reorder_point_s, l.unit_cost) for l in created[0].lines] == [("BEBIDAS", 901, 593, 500.0)]


def test_generate_orders_groups_by_supplier(monkeypatch):
    from app.api import orders
    monkeypatch.setattr(orders, "assert_business_access", lambda *a: None)
    skus = {"COCA-COLA 1.5L": "Andina", "SPRITE 1.5L": "Andina", "PEPSI 1.5L": "CCU", "PAN": None}
    monkeypatch.setattr(orders.service, "get_critical_skus", lambda **k: [
        {"family": f, "order_quantity": 10, "current_stock": 1, "reorder_point_s": 5, "order_up_to_S": 11} for f in skus
    ])
    lead = {"COCA-COLA 1.5L": 3, "SPRITE 1.5L": 9, "PEPSI 1.5L": 2, "PAN": 1}
    monkeypatch.setattr(orders, "_get_product_params", lambda db, b, s, fam: {"lead_time_days": lead[fam], "unit_cost": 1.0, "supplier": skus[fam]})
    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.distinct.return_value = []
    created = orders.generate_automatic_orders(9, 1, MagicMock(id=1), db)
    got = {o.supplier: ([l.family for l in o.lines], (o.expected_delivery - orders.date.today()).days) for o in created}
    assert got == {"Andina": (["COCA-COLA 1.5L", "SPRITE 1.5L"], 9), "CCU": (["PEPSI 1.5L"], 2), None: (["PAN"], 1)}


def test_order_search_by_number():
    from app.api.orders import _filtered_orders
    from sqlalchemy.dialects import postgresql
    db = MagicMock()
    _filtered_orders(db, 9, None, None, "OC-000042", None, None)
    cond = db.query.return_value.filter.return_value.filter.call_args.args[0]
    sql = str(cond.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "purchase_orders.id = 42" in sql


def test_order_response_number_and_total():
    from datetime import datetime
    from app.models.schemas import PurchaseOrderResponse
    line = dict(id=1, family="X", quantity=2, unit_cost=150.0, trigger_stock=None, reorder_point_s=None, order_up_to_S=None)
    r = PurchaseOrderResponse(id=7, business_id=1, store_nbr=1, supplier=None, policy_used="s_s", status="pending",
                              created_at=datetime.now(), expected_delivery=None, received_at=None,
                              lines=[line, {**line, "id": 2, "unit_cost": 50.0}])
    assert (r.order_number, r.total_cost) == ("OC-000007", 400.0)
    r.lines[1].unit_cost = None
    assert r.total_cost is None


def _catalog_db(products):
    db = MagicMock()
    db.query.return_value.filter.return_value = products
    return db


def test_manual_order_fills_cost_and_delivery_from_catalog(monkeypatch):
    from app.api import orders
    from app.models.schemas import PurchaseOrderCreate
    monkeypatch.setattr(orders, "assert_business_access", lambda *a: None)
    db = _catalog_db([MagicMock(family="MANTEQUILLA COLUN 250G", unit_cost=2190, lead_time_days=4)])
    body = PurchaseOrderCreate(business_id=9, supplier=" Colun ", lines=[{"family": "mantequilla colun 250g", "quantity": 12}])
    order = orders.create_order(body, MagicMock(id=1), db)
    assert (order.supplier, order.policy_used, order.status) == ("Colun", "manual", "pending")
    assert (order.expected_delivery - orders.date.today()).days == 4
    assert [(l.family, l.quantity, l.unit_cost) for l in order.lines] == [("MANTEQUILLA COLUN 250G", 12, 2190)]


@pytest.mark.parametrize("lines,msg", [
    ([{"family": "NO EXISTE", "quantity": 1}], "no registrados"),
    ([{"family": "A", "quantity": 1}, {"family": "a", "quantity": 2}], "repetidos"),
])
def test_manual_order_rejects_bad_lines(monkeypatch, lines, msg):
    from app.api import orders
    from app.models.schemas import PurchaseOrderCreate
    monkeypatch.setattr(orders, "assert_business_access", lambda *a: None)
    db = _catalog_db([MagicMock(family="A", unit_cost=1, lead_time_days=1)])
    with pytest.raises(HTTPException) as exc:
        orders.create_order(PurchaseOrderCreate(business_id=9, lines=lines), MagicMock(id=1), db)
    assert exc.value.status_code == 400 and msg in exc.value.detail


def test_order_edit_only_when_pending(monkeypatch):
    from app.api import orders
    from app.models.schemas import PurchaseOrderUpdate
    monkeypatch.setattr(orders, "assert_business_access", lambda *a: None)
    monkeypatch.setattr(orders, "_get_order", lambda *a: MagicMock(status="confirmed"))
    with pytest.raises(HTTPException) as exc:
        orders.update_order(1, 9, PurchaseOrderUpdate(supplier="X"), MagicMock(id=1), MagicMock())
    assert exc.value.status_code == 400


def test_order_pdf_renders(monkeypatch):
    from datetime import date, datetime
    from types import SimpleNamespace
    from app.api import orders
    monkeypatch.setattr(orders, "assert_business_access", lambda *a: None)
    line = SimpleNamespace(id=1, family="ÑANDÚ 1L", quantity=12, unit_cost=2190, trigger_stock=None, reorder_point_s=None, order_up_to_S=None)
    order = SimpleNamespace(id=42, business_id=9, store_nbr=1, supplier="Colun", policy_used="manual", status="pending",
                            created_at=datetime.now(), expected_delivery=date.today(), received_at=None, lines=[line])
    monkeypatch.setattr(orders, "_get_order", lambda *a: order)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
        name="Distribuidora El Roble", rut="76.086.428-5", address="Av. Grecia 1234", city="Ñuñoa", phone=None, email="a@b.cl")
    resp = orders.export_order_pdf(42, 9, MagicMock(id=1), db)
    assert resp.headers["content-disposition"].endswith("OC-000042.pdf")


@pytest.mark.parametrize("raw,out", [
    ("76086428-5", "76.086.428-5"),
    ("76.086.428-5", "76.086.428-5"),
    ("12.345.678-5", "12.345.678-5"),
    ("7.654.321-6", "7.654.321-6"),
    ("10.000.013-k", "10.000.013-K"),
    ("", None),
])
def test_rut_valid(raw, out):
    from app.services.rut import normalize_rut
    assert normalize_rut(raw) == out


@pytest.mark.parametrize("raw", ["76.086.428-4", "abc", "123-4"])
def test_rut_invalid(raw):
    from app.services.rut import normalize_rut
    with pytest.raises(ValueError):
        normalize_rut(raw)


def test_update_business_rejects_bad_rut(monkeypatch):
    from app.api import businesses
    from app.models.schemas import BusinessUpdate
    monkeypatch.setattr(businesses, "assert_business_owner", lambda *a: None)
    with pytest.raises(HTTPException) as exc:
        businesses.update_business(9, BusinessUpdate(rut="76.086.428-4"), MagicMock(id=1), MagicMock())
    assert exc.value.status_code == 422
