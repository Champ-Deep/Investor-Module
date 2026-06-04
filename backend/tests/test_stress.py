"""PRD Section-17 stress-test regression (the headline acceptance suite).

For each query: filters-first must achieve complete recall of the planted relevants, and ranking
must place them in the top-K (K = number of relevants) — i.e. top-K relevance = 100% >= the 80% bar.
Requires a migrated + seeded DB (make docker-up migrate seed-taxonomy seed).
"""

import pytest

from cadence.models.query import QueryFilters
from cadence.query.features import coinvestors, comps, conflict_check
from cadence.query.planner import execute_search
from cadence.seed.universe import build_universe

pytestmark = pytest.mark.stress

GROUND_TRUTH = build_universe().ground_truth

# Firm-search queries (SQ1-SQ7) compiled to structured filters. Sector intent is soft where the
# query is about the firm's own focus; it is hard (a deal/acquisition count) for sell-side.
FILTERS: dict[str, QueryFilters] = {
    "raise_vsaas_b": QueryFilters(
        capital_roles=["direct_investor"],
        hq_countries=["US"],
        stages=["series_b"],
        lead_only=True,
        check_min=15_000_000,
        check_max=25_000_000,
        led_within_months=6,
        soft_sectors=["vertical-saas"],
    ),
    "raise_climate_growth": QueryFilters(
        capital_roles=["direct_investor"],
        lp_base_geos=["EU"],
        stages=["series_c"],
        check_min=25_000_000,
        check_max=50_000_000,
        soft_sectors=["climate-tech"],
    ),
    "raise_solo_preseed_ai": QueryFilters(
        capital_roles=["direct_investor"],
        hq_countries=["US"],
        stages=["pre_seed"],
        gp_count_max=3,
        soft_sectors=["ai-infrastructure"],
    ),
    "sell_side_cyber": QueryFilters(
        capital_roles=["strategic_acquirer"],
        hq_countries=["US"],
        acq_buyer_kind="strategic",
        acq_sector="cybersecurity",
        acq_min_count=2,
        acq_within_months=24,
        ev_min=50_000_000,
        ev_max=300_000_000,
    ),
    "sell_side_pe_health": QueryFilters(
        investor_types=["pe"],
        capital_roles=["strategic_acquirer"],
        acq_platform=True,
        ebitda_min=5_000_000,
        ebitda_max=15_000_000,
        dry_powder_min=1,
        acq_sector="healthcare-services",
        acq_min_count=1,
        acq_within_months=36,
    ),
    "placement_pension_pe": QueryFilters(
        investor_types=["pension"],
        capital_roles=["lp_allocator"],
        asset_class="pe",
        allocation_min_pct=8,
        aum_min=20_000_000_000,
        committed_within_months=24,
        committed_first_time_only=True,
    ),
    "placement_fo_fintech": QueryFilters(
        investor_types=["family_office"],
        capital_roles=["direct_investor", "lp_allocator"],
        committed_within_months=17,
        soft_sectors=["fintech"],
    ),
}


@pytest.mark.parametrize("query_id", list(FILTERS))
async def test_firm_query_recall_and_top_k_precision(conn, settings, today, query_id):
    relevants = set(GROUND_TRUTH[query_id]["relevant"])
    ranked = [r.slug for r in await execute_search(conn, FILTERS[query_id], settings, today=today)]
    matched = set(ranked)
    # Filters-first: complete recall (no qualifying firm dropped).
    assert relevants <= matched, f"{query_id}: missing {relevants - matched}"
    # Ranking precision: the planted relevants occupy the top-K.
    k = len(relevants)
    assert set(ranked[:k]) == relevants, f"{query_id}: top-{k} was {ranked[:k]}"


async def test_warm_intro_lightspeed(conn, today):
    relevants = set(GROUND_TRUTH["warm_intro_lightspeed"]["relevant"])
    res = await coinvestors(
        conn, lead_slug="lightspeed", sector="digital-health", within_months=36, today=today
    )
    assert {r["slug"] for r in res} == relevants


async def test_comps_marketplaces(conn):
    gt = GROUND_TRUTH["comps_marketplaces"]
    res = await comps(conn, sector="marketplaces", ev_min=100_000_000, ev_max=500_000_000, limit=20)
    returned = {r["target_slug"] for r in res}
    assert set(gt["relevant"]) <= returned
    assert not (set(gt["distractors"]) & returned)


async def test_conflict_check(conn):
    gt = GROUND_TRUTH["conflict_check"]
    res = await conflict_check(
        conn, target_firm_slugs=gt["targets"], competitor_company_slugs=gt["competitors"]
    )
    assert set(res) == set(gt["relevant"])
