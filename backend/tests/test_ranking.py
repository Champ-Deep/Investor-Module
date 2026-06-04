"""Semantic ranking within the matched set (M5). Requires a migrated + seeded DB."""

from cadence.models.query import QueryFilters
from cadence.query.planner import execute_search


async def test_sq3_vsaas_ranks_above_offsector(conn, settings, today):
    filters = QueryFilters(
        capital_roles=["direct_investor"],
        hq_countries=["US"],
        stages=["series_b"],
        lead_only=True,
        check_min=15_000_000,
        check_max=25_000_000,
        led_within_months=6,
        soft_sectors=["vertical-saas"],
    )
    slugs = [r.slug for r in await execute_search(conn, filters, settings, today=today)]
    relevants = {f"sq3-rel-{i}" for i in range(8)}
    # Sector is soft: the off-sector firm is retained (recall) but must rank below every relevant.
    assert "sq3-dis-sector" in slugs
    assert set(slugs[:8]) == relevants, f"expected the 8 vsaas relevants on top, got {slugs[:8]}"
    assert slugs.index("sq3-dis-sector") >= 8
