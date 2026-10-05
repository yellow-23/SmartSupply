"""
Verifica que POST /api/ingest/confirm rechace en el BACKEND las cargas con
incidencias de calidad bloqueantes (severity="error"), no solo que el boton
del frontend se deshabilite. Complementa test_ingest_validator.py (que prueba
el detector) y test_ingest_access.py (que prueba el aislamiento por negocio).
"""
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.ingest import confirm_ingest
from app.models.schemas import IngestConfirm, IngestRecord

TODAY = date.today()


def _member_db():
    """DB mock donde el usuario SI pertenece al negocio (assert_business_access
    encuentra la fila en user_businesses) y cualquier Product ya "existe", para
    no ejercitar mas ramas de las necesarias en este test."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock()
    return db


def test_confirm_rejects_mixed_granularity():
    """Una carga con granularidad mezclada (diaria + gaps mensuales en la misma
    familia) debe rechazarse en el backend con 422, sin llegar a insertar nada."""
    db = _member_db()
    records = [
        IngestRecord(date=TODAY - timedelta(days=i), family="PAN", sales=10.0)
        for i in range(5)
    ] + [
        IngestRecord(date=TODAY - timedelta(days=90), family="PAN", sales=10.0),
        IngestRecord(date=TODAY - timedelta(days=120), family="PAN", sales=10.0),
    ]
    body = IngestConfirm(records=records, business_id=1, store_nbr=1, sales_unit="units")

    with pytest.raises(HTTPException) as exc:
        confirm_ingest(body, MagicMock(id=1), db)

    assert exc.value.status_code == 422
    assert "MIXED_GRANULARITY" in exc.value.detail
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_confirm_allows_clean_daily_data():
    """Una carga diaria sin incidencias bloqueantes debe pasar la validacion y
    llegar a insertar filas con normalidad."""
    db = _member_db()
    records = [
        IngestRecord(date=TODAY - timedelta(days=i), family="PAN", sales=10.0)
        for i in range(10)
    ]
    body = IngestConfirm(
        records=records, business_id=1, store_nbr=1, sales_unit="units", filename="test.xlsx"
    )

    result = confirm_ingest(body, MagicMock(id=1), db)

    assert result.records_loaded == 10
    db.add.assert_called()
    db.commit.assert_called()


def test_confirm_allows_warning_only_issues():
    """Incidencias no bloqueantes (ej. MONTHLY_GRANULARITY, que es 'warning')
    no deben impedir la carga, a diferencia de MIXED_GRANULARITY."""
    db = _member_db()
    records = [
        IngestRecord(date=TODAY - timedelta(days=30 * i), family="PAN", sales=10.0)
        for i in range(4)
    ]
    body = IngestConfirm(
        records=records, business_id=1, store_nbr=1, sales_unit="units", filename="test.xlsx"
    )

    result = confirm_ingest(body, MagicMock(id=1), db)

    assert result.records_loaded == 4
    db.commit.assert_called()
