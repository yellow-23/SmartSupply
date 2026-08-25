from datetime import date, timedelta

from app.models.schemas import IngestRecord
from app.services.ingest_validator import filter_loadable_records, validate_ingest_records

TODAY = date.today()


def rec(days_ago, family="PAN", sales=10.0):
    return IngestRecord(date=TODAY - timedelta(days=days_ago), family=family, sales=sales)


def test_empty_records_no_issues():
    assert validate_ingest_records([]) == []


def test_future_dates_flagged():
    records = [
        IngestRecord(date=TODAY + timedelta(days=5), family="PAN", sales=10.0),
        rec(1), rec(2), rec(3),
    ]
    issues = validate_ingest_records(records)
    codes = [i.code for i in issues]
    assert "FUTURE_DATES" in codes


def test_monthly_granularity_flagged():
    records = [IngestRecord(date=TODAY - timedelta(days=30 * i), family="PAN", sales=10.0) for i in range(4)]
    issues = validate_ingest_records(records)
    codes = [i.code for i in issues]
    assert "MONTHLY_GRANULARITY" in codes


def test_daily_granularity_no_warning():
    records = [rec(i) for i in range(10)]
    issues = validate_ingest_records(records)
    codes = [i.code for i in issues]
    assert "MONTHLY_GRANULARITY" not in codes
    assert "MIXED_GRANULARITY" not in codes


def test_mixed_granularity_flagged():
    daily = [rec(i) for i in range(5)]
    monthly_gap = [rec(90), rec(120)]
    issues = validate_ingest_records(daily + monthly_gap)
    codes = [i.code for i in issues]
    assert "MIXED_GRANULARITY" in codes


def test_scale_shift_flagged():
    first_half = [rec(20 - i, sales=10.0) for i in range(10)]
    second_half = [rec(10 - i, sales=100.0) for i in range(10)]
    issues = validate_ingest_records(first_half + second_half)
    codes = [i.code for i in issues]
    assert "SCALE_SHIFT" in codes


def test_likely_currency_flagged_when_median_high():
    records = [rec(i, family="PAN", sales=50_000.0) for i in range(10)]
    issues = validate_ingest_records(records)
    codes = [i.code for i in issues]
    assert "LIKELY_CURRENCY" in codes


def test_likely_currency_not_flagged_for_normal_units():
    records = [rec(i, family="PAN", sales=25.0) for i in range(10)]
    issues = validate_ingest_records(records)
    codes = [i.code for i in issues]
    assert "LIKELY_CURRENCY" not in codes


def test_filter_loadable_records_drops_future_and_zero_sales():
    records = [
        rec(1, sales=10.0),
        IngestRecord(date=TODAY + timedelta(days=1), family="PAN", sales=10.0),  # futuro
        rec(2, sales=0.0),  # sin venta
        rec(3, sales=5.0),
    ]
    loadable = filter_loadable_records(records)
    assert len(loadable) == 2
    assert all(r.date <= TODAY and r.sales > 0 for r in loadable)
