"""
IngestValidator — SmartSupply
Detecta problemas en los registros extraidos por el AI antes de cargarlos:
- Fechas futuras (probables proyecciones)
- Granularidad inconsistente (mezcla diaria/semanal/mensual)
- Saltos de escala entre periodos (posible mezcla de unidades)

Se invoca al final del preview para que el usuario vea los warnings antes
de confirmar la carga.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date
from typing import Iterable

from app.models.schemas import IngestRecord, QualityIssue

# Thresholds (todos ajustables)
MONTHLY_GAP_DAYS = 25      # gap mediano >=25 dias → datos mensuales
WEEKLY_GAP_DAYS = 5        # gap mediano entre 5 y 25 → semanales
MIXED_GAP_RATIO = 10       # max_gap / min_gap > 10 → granularidad inconsistente
SCALE_SHIFT_RATIO = 5.0    # cambio de escala >5x entre mitades → posible mezcla unidades
CURRENCY_MEDIAN_THRESHOLD = 10_000  # mediana diaria > 10k uds = casi seguro son pesos CLP
CURRENCY_FAMILY_RATIO = 0.5         # >=50% de familias afectadas → warning global
MIN_RECORDS_FOR_GRANULARITY = 3
MIN_RECORDS_FOR_SCALE = 10
MIN_RECORDS_FOR_CURRENCY = 5


def validate_ingest_records(records: Iterable[IngestRecord]) -> list[QualityIssue]:
    """
    Analiza los registros y devuelve una lista de problemas detectados.
    Cada issue tiene severity ('error' | 'warning' | 'info'), code, family (opcional)
    y mensaje en espanol para mostrar al usuario.
    """
    records = list(records)
    issues: list[QualityIssue] = []
    if not records:
        return issues

    today = date.today()

    # ── 1. Fechas futuras ─────────────────────────────────────────────────────
    future = [r for r in records if r.date > today]
    if future:
        max_future = max(r.date for r in future)
        issues.append(QualityIssue(
            severity="warning",
            code="FUTURE_DATES",
            message=(
                f"{len(future)} registros tienen fecha posterior a hoy ({today.isoformat()}), "
                f"hasta {max_future.isoformat()}. Probablemente son proyecciones — no se "
                f"cargaran al historico."
            ),
        ))

    # Para los demas chequeos usamos solo registros historicos
    past = [r for r in records if r.date <= today]
    if not past:
        return issues

    by_family: dict[str, list[IngestRecord]] = defaultdict(list)
    for r in past:
        by_family[r.family].append(r)

    # ── 2. Granularidad por familia ────────────────────────────────────────────
    for family, fam_records in by_family.items():
        if len(fam_records) < MIN_RECORDS_FOR_GRANULARITY:
            continue

        dates = sorted(r.date for r in fam_records)
        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1) if dates[i + 1] != dates[i]]
        if not gaps:
            continue

        median_gap = statistics.median(gaps)
        min_gap = min(gaps)
        max_gap = max(gaps)

        # Granularidad inconsistente
        if max_gap > 7 and (max_gap / max(min_gap, 1)) > MIXED_GAP_RATIO:
            issues.append(QualityIssue(
                severity="warning",
                code="MIXED_GRANULARITY",
                family=family,
                message=(
                    f"{family}: granularidad inconsistente (gaps entre {min_gap} y {max_gap} dias). "
                    f"Puede haber dias sin venta mezclados con periodos sin registro. "
                    f"Se cargara igual — los modelos usaran los datos disponibles."
                ),
            ))
        elif median_gap >= MONTHLY_GAP_DAYS:
            issues.append(QualityIssue(
                severity="warning",
                code="MONTHLY_GRANULARITY",
                family=family,
                message=(
                    f"{family}: registros mensuales detectados (gap mediano {int(median_gap)} dias). "
                    f"Si son totales del mes y no ventas unicas, los modelos de forecasting "
                    f"no funcionaran bien — necesitan datos diarios."
                ),
            ))
        elif median_gap >= WEEKLY_GAP_DAYS:
            issues.append(QualityIssue(
                severity="info",
                code="WEEKLY_GRANULARITY",
                family=family,
                message=(
                    f"{family}: registros semanales (gap mediano {int(median_gap)} dias). "
                    f"Funcional pero ideal seria diario."
                ),
            ))

    # ── 3. Cambios de escala por familia ──────────────────────────────────────
    for family, fam_records in by_family.items():
        if len(fam_records) < MIN_RECORDS_FOR_SCALE:
            continue
        fam_records_sorted = sorted(fam_records, key=lambda r: r.date)
        mid = len(fam_records_sorted) // 2
        first_half = [r.sales for r in fam_records_sorted[:mid] if r.sales > 0]
        second_half = [r.sales for r in fam_records_sorted[mid:] if r.sales > 0]
        if not first_half or not second_half:
            continue

        median_first = statistics.median(first_half)
        median_second = statistics.median(second_half)
        if median_first == 0 or median_second == 0:
            continue

        ratio = max(median_first, median_second) / min(median_first, median_second)
        if ratio > SCALE_SHIFT_RATIO:
            issues.append(QualityIssue(
                severity="warning",
                code="SCALE_SHIFT",
                family=family,
                message=(
                    f"{family}: cambio de escala {ratio:.1f}x entre primera y segunda mitad "
                    f"(mediana {median_first:.0f} → {median_second:.0f}). Verifica que las "
                    f"unidades sean consistentes (pesos vs unidades, totales vs diarios)."
                ),
            ))

    # ── 4. Pesos vs unidades (heuristica de magnitud) ─────────────────────────
    # Una distribuidora chilena dificilmente vende >10k unidades de UNA familia
    # por dia. Si la mediana es muy alta es casi seguro que son pesos CLP, no uds.
    flagged_families: list[tuple[str, float]] = []
    eligible_families = 0
    for family, fam_records in by_family.items():
        sales_vals = [r.sales for r in fam_records if r.sales > 0]
        if len(sales_vals) < MIN_RECORDS_FOR_CURRENCY:
            continue
        eligible_families += 1
        med = statistics.median(sales_vals)
        if med > CURRENCY_MEDIAN_THRESHOLD:
            flagged_families.append((family, med))

    if eligible_families > 0 and len(flagged_families) / eligible_families >= CURRENCY_FAMILY_RATIO:
        sample = ", ".join(f"{f} (~${m:,.0f})" for f, m in flagged_families[:3])
        more = f" y {len(flagged_families) - 3} mas" if len(flagged_families) > 3 else ""
        issues.append(QualityIssue(
            severity="warning",
            code="LIKELY_CURRENCY",
            message=(
                f"{len(flagged_families)} de {eligible_families} familias tienen mediana diaria "
                f">{CURRENCY_MEDIAN_THRESHOLD:,} (ej: {sample}{more}). Esto sugiere que los valores "
                f"son MONTO en pesos, no UNIDADES vendidas. Si cargas asi, el forecast y las "
                f"sugerencias de compra estaran en pesos en vez de unidades fisicas a reponer. "
                f"Verifica que columna del archivo elegiste."
            ),
        ))

    return issues


def filter_loadable_records(records: Iterable[IngestRecord]) -> list[IngestRecord]:
    """Devuelve solo los registros cargables: fecha <= hoy y sales > 0."""
    today = date.today()
    return [r for r in records if r.date <= today and r.sales > 0]
