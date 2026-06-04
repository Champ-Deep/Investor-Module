"""The Readiness label and a backtest harness (ADR 0005).

Readiness label: the firm makes >=1 NEW deal within the next 90 days. Because seeded deals are
dated, we can backtest the cold-start model now and report its hit-rate, making the score
falsifiable and proving the pipeline is swappable for a learned model.
"""

from __future__ import annotations

from datetime import date, timedelta

from cadence.cadence.features import FirmRaw, extract_features
from cadence.cadence.model import CadenceModel

DAYS_PER_MONTH = 30.44
HORIZON_DAYS = 90


def readiness_label(
    new_deal_dates: list[date], as_of: date, horizon_days: int = HORIZON_DAYS
) -> bool:
    end = as_of + timedelta(days=horizon_days)
    return any(as_of < d <= end for d in new_deal_dates)


def backtest(
    raws: dict[str, FirmRaw],
    model: CadenceModel,
    today: date,
    as_of_months: tuple[int, ...] = (3, 6, 9, 12),
    threshold: int = 50,
) -> float:
    """Time-split accuracy of predicted-ready (score >= threshold) vs the realized label."""
    correct = total = 0
    for raw in raws.values():
        for months in as_of_months:
            as_of = today - timedelta(days=round(months * DAYS_PER_MONTH))
            predicted_ready = model.predict(extract_features(raw, as_of)).score >= threshold
            actual_ready = readiness_label(raw.new_deal_dates, as_of)
            total += 1
            correct += int(predicted_ready == actual_ready)
    return correct / total if total else 0.0
