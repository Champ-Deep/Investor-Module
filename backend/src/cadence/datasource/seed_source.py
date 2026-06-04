"""Seed-backed implementations of the seam. The universe is built by cadence.seed.universe."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from cadence.datasource.base import DeliverabilityResult, RoleCurrencyResult
from cadence.datasource.models import (
    RawAcquisition,
    RawCompany,
    RawDeal,
    RawFirm,
    RawRound,
)


@dataclass
class SeedUniverse:
    firms: list[RawFirm] = field(default_factory=list)
    companies: list[RawCompany] = field(default_factory=list)
    rounds: list[RawRound] = field(default_factory=list)
    deals: list[RawDeal] = field(default_factory=list)
    acquisitions: list[RawAcquisition] = field(default_factory=list)
    # query_id -> {"relevant": [firm_slug, ...], "distractors": [firm_slug, ...]}
    ground_truth: dict[str, dict[str, list[str]]] = field(default_factory=dict)


class SeedDataSource:
    def __init__(self, universe: SeedUniverse) -> None:
        self._u = universe

    def fetch_firms(self) -> list[RawFirm]:
        return self._u.firms

    def fetch_companies(self) -> list[RawCompany]:
        return self._u.companies


class SeedDealSource:
    def __init__(self, universe: SeedUniverse) -> None:
        self._u = universe

    def fetch_rounds(self) -> list[RawRound]:
        return self._u.rounds

    def fetch_deals(self) -> list[RawDeal]:
        return self._u.deals

    def fetch_acquisitions(self) -> list[RawAcquisition]:
        return self._u.acquisitions


# In the seed path, ingestion writes the deliverability/role-currency statuses already present on
# the Raw records. These providers exist for the live re-verification path (the seam parity point).
class SeedDeliverabilityProvider:
    def verify(self, channel_kind: str, value: str) -> DeliverabilityResult:
        return DeliverabilityResult(status="unknown", checked_at=datetime.now(timezone.utc))


class SeedRoleCurrencyProvider:
    def check(self, partner_name: str, firm_name: str) -> RoleCurrencyResult:
        return RoleCurrencyResult(status="unknown", checked_at=datetime.now(timezone.utc))
