"""Filters-first recall + exclusion (M4). Requires a migrated + seeded DB (make seed)."""

from cadence.models.query import QueryFilters
from cadence.query.planner import execute_search


async def test_sq3_series_b_vsaas_leads(conn, settings, today):
    filters = QueryFilters(
        capital_roles=["direct_investor"],
        hq_countries=["US"],
        stages=["series_b"],
        lead_only=True,
        check_min=15_000_000,
        check_max=25_000_000,
        led_within_months=6,
    )
    slugs = {r.slug for r in await execute_search(conn, filters, settings, today=today)}
    # Filters-first recall: every planted relevant is present.
    for i in range(8):
        assert f"sq3-rel-{i}" in slugs
    # Sector is SOFT (ADR 0004): the off-sector firm is NOT excluded by the hard filter.
    assert "sq3-dis-sector" in slugs
    # Hard distractors (each violates one hard predicate) are excluded.
    for d in [
        "sq3-dis-follow",
        "sq3-dis-bigcheck",
        "sq3-dis-stage",
        "sq3-dis-geo",
        "sq3-dis-stale",
    ]:
        assert d not in slugs


async def test_sq6_pension_pe_allocators(conn, settings, today):
    filters = QueryFilters(
        investor_types=["pension"],
        capital_roles=["lp_allocator"],
        asset_class="pe",
        allocation_min_pct=8,
        aum_min=20_000_000_000,
        committed_within_months=24,
        committed_first_time_only=True,
    )
    slugs = {r.slug for r in await execute_search(conn, filters, settings, today=today)}
    for i in range(5):
        assert f"sq6-rel-{i}" in slugs
    for d in ["sq6-dis-alloc", "sq6-dis-aum", "sq6-dis-established", "sq6-dis-old"]:
        assert d not in slugs


async def test_sq1_strategic_cyber_acquirers(conn, settings, today):
    filters = QueryFilters(
        capital_roles=["strategic_acquirer"],
        hq_countries=["US"],
        acq_buyer_kind="strategic",
        acq_sector="cybersecurity",
        acq_min_count=2,
        acq_within_months=24,
        ev_min=50_000_000,
        ev_max=300_000_000,
    )
    slugs = {r.slug for r in await execute_search(conn, filters, settings, today=today)}
    for i in range(6):
        assert f"sq1-rel-{i}" in slugs
    for d in ["sq1-dis-one", "sq1-dis-ev", "sq1-dis-sector", "sq1-dis-old"]:
        assert d not in slugs
