"""Feature extraction shared by the cold-start and learned models (the stable swap point).

Features are normalized to 0-1. `as_of` lets the backtester compute features at a past date using
only deals known by then. time_since_last_check is shaped here (bucketed) because it is
non-monotonic: a long gap can mean pent-up demand OR a stalled fund (ADR 0005).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import asyncpg

DAYS_PER_MONTH = 30.44


@dataclass
class FirmRaw:
    dry_powder: float | None = None
    aum: float | None = None
    fund_sizes: list[float] = field(default_factory=list)
    fund_vintages: list[int] = field(default_factory=list)
    fund_statuses: list[str] = field(default_factory=list)
    new_deal_dates: list[date] = field(default_factory=list)


async def load_firm_raws(conn: asyncpg.Connection) -> dict[str, FirmRaw]:
    raws: dict[str, FirmRaw] = {}
    for r in await conn.fetch("SELECT id::text AS id, dry_powder, aum FROM firm"):
        raws[r["id"]] = FirmRaw(
            dry_powder=float(r["dry_powder"]) if r["dry_powder"] is not None else None,
            aum=float(r["aum"]) if r["aum"] is not None else None,
        )
    for r in await conn.fetch("SELECT firm_id::text AS fid, size, vintage_year, status FROM fund"):
        fr = raws.get(r["fid"])
        if fr is None:
            continue
        if r["size"] is not None:
            fr.fund_sizes.append(float(r["size"]))
        if r["vintage_year"] is not None:
            fr.fund_vintages.append(r["vintage_year"])
        fr.fund_statuses.append(r["status"])
    for r in await conn.fetch("SELECT firm_id::text AS fid, announced_at FROM deal WHERE is_new"):
        fr = raws.get(r["fid"])
        if fr is not None:
            fr.new_deal_dates.append(r["announced_at"])
    return raws


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _time_since_bucket(months: float) -> float:
    # non-monotonic: recent = steady, 2-9mo = likely pent-up, 9-18mo = cooling, >18mo = stalled
    if months < 2:
        return 0.5
    if months <= 9:
        return 1.0
    if months <= 18:
        return 0.5
    return 0.1


def _vintage_bucket(age_years: int) -> float:
    # mid-life funds deploy fastest; very young still ramping; very old winding down
    if age_years < 2:
        return 0.5
    if age_years <= 6:
        return 1.0
    if age_years <= 9:
        return 0.6
    return 0.3


def extract_features(raw: FirmRaw, as_of: date) -> dict[str, float]:
    features: dict[str, float] = {}

    denom = raw.aum or (sum(raw.fund_sizes) if raw.fund_sizes else 0.0)
    if raw.dry_powder is not None and denom > 0:
        features["dry_powder"] = _clamp(raw.dry_powder / denom)
    elif raw.dry_powder:
        features["dry_powder"] = 0.6
    else:
        features["dry_powder"] = 0.4

    window_start = as_of - timedelta(days=365)
    recent = [d for d in raw.new_deal_dates if window_start <= d <= as_of]
    features["deployment_pace"] = _clamp(len(recent) / 3.0)

    past = [d for d in raw.new_deal_dates if d <= as_of]
    if past:
        months = (as_of - max(past)).days / DAYS_PER_MONTH
        features["time_since_last_check"] = _time_since_bucket(months)
    else:
        features["time_since_last_check"] = 0.1

    if raw.fund_vintages:
        features["vintage_age"] = _vintage_bucket(as_of.year - max(raw.fund_vintages))
    else:
        features["vintage_age"] = 0.5

    features["fund_status"] = (
        1.0 if any(s in ("open", "investing") for s in raw.fund_statuses) else 0.0
    )
    return features
