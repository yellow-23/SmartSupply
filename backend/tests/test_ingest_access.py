from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.ingest import confirm_ingest
from app.models.schemas import IngestConfirm, IngestRecord


def test_confirm_rejects_business_without_membership():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None  # sin fila en user_businesses
    body = IngestConfirm(
        records=[IngestRecord(date=date(2026, 1, 1), family="PAN", sales=10.0)],
        business_id=999, store_nbr=1, sales_unit="units",
    )
    with pytest.raises(HTTPException) as exc:
        confirm_ingest(body, MagicMock(id=1), db)
    assert exc.value.status_code == 403
    db.add.assert_not_called()
