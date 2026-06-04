from datetime import datetime, timedelta, timezone

from cadence.verification import VerifiedState, compute_verified

NOW = datetime(2026, 6, 3, tzinfo=timezone.utc)
FRESH = NOW - timedelta(days=10)
STALE = NOW - timedelta(days=400)
SLA = 180


def _verdict(deliv_status, deliv_at, role_status, role_at):
    return compute_verified(
        deliverability_status=deliv_status,
        deliverability_checked_at=deliv_at,
        role_currency_status=role_status,
        role_currency_checked_at=role_at,
        sla_days=SLA,
        now=NOW,
    )


def test_both_fresh_passes_is_verified():
    assert _verdict("deliverable", FRESH, "current", FRESH) is VerifiedState.VERIFIED


def test_catch_all_is_never_verified_even_with_current_role():
    # The structural honesty point: catch-all must not read as Verified.
    assert _verdict("catch_all", FRESH, "current", FRESH) is VerifiedState.CATCH_ALL


def test_deliverable_but_role_stale_is_partial():
    assert _verdict("deliverable", FRESH, "current", STALE) is VerifiedState.DELIVERABLE_ONLY


def test_deliverability_expired_breaks_verified():
    assert _verdict("deliverable", STALE, "current", FRESH) is VerifiedState.ROLE_CURRENT_ONLY


def test_role_only_is_partial():
    assert _verdict("undeliverable", FRESH, "current", FRESH) is VerifiedState.ROLE_CURRENT_ONLY


def test_unknown_everything_is_unverified():
    assert _verdict("unknown", None, "unknown", None) is VerifiedState.UNVERIFIED
