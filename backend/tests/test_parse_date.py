from datetime import date, datetime

import pytest

from app.services.ingest_service import IngestService


@pytest.fixture(scope="module")
def service():
    return IngestService()


@pytest.mark.parametrize("raw,expected", [
    ("15/03/2026", date(2026, 3, 15)),      # dd/mm/yyyy chileno inequivoco
    ("2026-03-15", date(2026, 3, 15)),      # ISO
    ("03/05/2026", date(2026, 5, 3)),       # ambiguo -> gana convencion chilena (dia=3, mes=5)
    ("13/02/2026", date(2026, 2, 13)),      # dia=13 invalido como mes -> solo puede ser dd/mm
    (None, None),
    ("", None),
    ("no es una fecha", None),
])
def test_parse_date_variants(service, raw, expected):
    assert service._parse_date(raw) == expected


def test_parse_date_passthrough_datetime_and_date(service):
    assert service._parse_date(datetime(2026, 7, 1, 10, 30)) == date(2026, 7, 1)
    assert service._parse_date(date(2026, 7, 1)) == date(2026, 7, 1)
