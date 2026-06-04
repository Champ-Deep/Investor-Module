"""Two-signal Verified computation (ADR 0002).

"Verified" holds only when BOTH Deliverability and Role currency pass inside the freshness SLA.
A catch-all server is never a deliverability pass and is surfaced explicitly. When only one
signal passes, the partial state is returned honestly rather than a plain "verified".
"""

from datetime import datetime, timedelta, timezone
from enum import StrEnum


class VerifiedState(StrEnum):
    VERIFIED = "verified"  # both signals pass inside SLA
    CATCH_ALL = "catch_all"  # deliverability is a catch-all accept (never a pass)
    DELIVERABLE_ONLY = "deliverable_only"  # email deliverable, role currency missing/stale/expired
    ROLE_CURRENT_ONLY = "role_current_only"  # role current, email undeliverable/missing/expired
    UNVERIFIED = "unverified"  # neither signal passes


def _within_sla(checked_at: datetime | None, sla_days: int, now: datetime) -> bool:
    if checked_at is None:
        return False
    return checked_at >= now - timedelta(days=sla_days)


def compute_verified(
    *,
    deliverability_status: str | None,
    deliverability_checked_at: datetime | None,
    role_currency_status: str | None,
    role_currency_checked_at: datetime | None,
    sla_days: int,
    now: datetime | None = None,
) -> VerifiedState:
    now = now or datetime.now(timezone.utc)

    deliverable_pass = deliverability_status == "deliverable" and _within_sla(
        deliverability_checked_at, sla_days, now
    )
    role_pass = role_currency_status == "current" and _within_sla(
        role_currency_checked_at, sla_days, now
    )

    if deliverable_pass and role_pass:
        return VerifiedState.VERIFIED
    # Surface catch-all explicitly: it is never counted as deliverable (ADR 0002).
    if deliverability_status == "catch_all":
        return VerifiedState.CATCH_ALL
    if deliverable_pass:
        return VerifiedState.DELIVERABLE_ONLY
    if role_pass:
        return VerifiedState.ROLE_CURRENT_ONLY
    return VerifiedState.UNVERIFIED
