"""The seam Protocols. Implementations: SeedDataSource (now), LakeB2BDataSource (live, later)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel

from cadence.datasource.models import (
    RawAcquisition,
    RawCompany,
    RawDeal,
    RawFirm,
    RawRound,
)


class DataSource(Protocol):
    """LakeB2B-shaped: identity + verified contacts + firmographics."""

    def fetch_firms(self) -> list[RawFirm]: ...
    def fetch_companies(self) -> list[RawCompany]: ...


class DealSource(Protocol):
    """Behavioral deal/portfolio data (a distinct provider behind the same seam)."""

    def fetch_rounds(self) -> list[RawRound]: ...
    def fetch_deals(self) -> list[RawDeal]: ...
    def fetch_acquisitions(self) -> list[RawAcquisition]: ...


class DeliverabilityResult(BaseModel):
    status: str  # deliverable | catch_all | undeliverable | unknown
    checked_at: datetime


class DeliverabilityProvider(Protocol):
    """Signal #1 (ADR 0002). Live impl wraps lakeb2b-email-verify; catch-all is not a pass."""

    def verify(self, channel_kind: str, value: str) -> DeliverabilityResult: ...


class RoleCurrencyResult(BaseModel):
    status: str  # current | stale | unknown
    checked_at: datetime


class RoleCurrencyProvider(Protocol):
    """Signal #2 (ADR 0002): does the person still hold the role, corroborated recently."""

    def check(self, partner_name: str, firm_name: str) -> RoleCurrencyResult: ...
