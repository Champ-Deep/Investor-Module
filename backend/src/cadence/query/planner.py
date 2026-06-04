"""Compile QueryFilters into a single SQL WHERE over the full firm universe.

Filters-first (ADR 0004): every predicate here is an exact pass/fail. There is no LIMIT before
filtering and no embedding step — recall is complete. Sector/thesis *fit* is NOT applied here;
it ranks within the matched set in cadence.query.ranker (M5).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import asyncpg

from cadence.config import Settings
from cadence.embeddings.embedder import get_embedder, to_pgvector
from cadence.models.query import QueryFilters, SearchResultFirm

DAYS_PER_MONTH = 30.44

# Ranking weights: sector fit dominates; recency demotes stale; cadence is a capacity signal;
# free-text thesis similarity is a light nudge. Never affects recall (ADR 0004).
RANK_W_SECTOR = 0.55
RANK_W_RECENCY = 0.20
RANK_W_CADENCE = 0.15
RANK_W_TEXT = 0.10
RANK_HALFLIFE_DAYS = 18 * DAYS_PER_MONTH


class _Params:
    def __init__(self) -> None:
        self.values: list = []

    def add(self, value) -> str:
        self.values.append(value)
        return f"${len(self.values)}"


def _months_cutoff(today: date, months: int) -> date:
    return today - timedelta(days=round(months * DAYS_PER_MONTH))


def build_search_sql(
    filters: QueryFilters, *, today: date, sla_days: int, query_vec: str | None = None
) -> tuple[str, list]:
    p = _Params()
    where: list[str] = []

    if filters.investor_types:
        where.append(f"f.investor_type = ANY({p.add(filters.investor_types)})")
    for role in filters.capital_roles:
        where.append(
            f"EXISTS (SELECT 1 FROM capital_role cr "
            f"WHERE cr.firm_id = f.id AND cr.role = {p.add(role)})"
        )
    if filters.hq_countries:
        where.append(f"f.hq_country = ANY({p.add(filters.hq_countries)})")
    if filters.mandate_geos:
        where.append(
            f"EXISTS (SELECT 1 FROM firm_geo g WHERE g.firm_id = f.id "
            f"AND g.kind = 'mandate' AND g.value = ANY({p.add(filters.mandate_geos)}))"
        )
    if filters.lp_base_geos:
        where.append(
            f"EXISTS (SELECT 1 FROM firm_geo g WHERE g.firm_id = f.id "
            f"AND g.kind = 'lp_base' AND g.value = ANY({p.add(filters.lp_base_geos)}))"
        )

    # Behavioral deal predicate: stage + check + lead + recency evaluated on the SAME deal, so
    # the check-size filter operates strictly within the selected stage (no cross-stage match).
    deal_conds = ["d.firm_id = f.id"]
    if filters.new_only:
        deal_conds.append("d.is_new")
    if filters.lead_only:
        deal_conds.append("d.is_lead")
    if filters.stages:
        deal_conds.append(f"d.stage_slug = ANY({p.add(filters.stages)})")
    if filters.check_min is not None:
        deal_conds.append(f"d.check_amount >= {p.add(filters.check_min)}")
    if filters.check_max is not None:
        deal_conds.append(f"d.check_amount <= {p.add(filters.check_max)}")
    if filters.led_within_months is not None:
        deal_conds.append(
            f"d.announced_at >= {p.add(_months_cutoff(today, filters.led_within_months))}"
        )
    if (
        filters.stages
        or filters.check_min is not None
        or filters.check_max is not None
        or filters.lead_only
        or filters.led_within_months is not None
    ):
        where.append(f"EXISTS (SELECT 1 FROM deal d WHERE {' AND '.join(deal_conds)})")

    if filters.gp_count_max is not None:
        where.append(f"f.gp_count <= {p.add(filters.gp_count_max)}")
    if filters.aum_min is not None:
        where.append(f"f.aum >= {p.add(filters.aum_min)}")
    if filters.aum_max is not None:
        where.append(f"f.aum <= {p.add(filters.aum_max)}")
    if filters.dry_powder_min is not None:
        where.append(f"f.dry_powder >= {p.add(filters.dry_powder_min)}")
    if filters.fund_size_min is not None:
        where.append(
            f"EXISTS (SELECT 1 FROM fund fu WHERE fu.firm_id = f.id "
            f"AND fu.size >= {p.add(filters.fund_size_min)})"
        )
    if filters.fund_size_max is not None:
        where.append(
            f"EXISTS (SELECT 1 FROM fund fu WHERE fu.firm_id = f.id "
            f"AND fu.size <= {p.add(filters.fund_size_max)})"
        )
    if filters.min_new_deals_window is not None:
        where.append(f"COALESCE(fa.new_deal_count, 0) >= {p.add(filters.min_new_deals_window)}")

    for tag in filters.thesis_tags:
        where.append(
            f"EXISTS (SELECT 1 FROM firm_thesis_tag ft JOIN thesis_tag t ON t.id = ft.tag_id "
            f"WHERE ft.firm_id = f.id AND t.slug = {p.add(tag)})"
        )

    # Acquirer predicates
    if filters.acq_buyer_kind is not None:
        where.append(
            f"EXISTS (SELECT 1 FROM firm_role_acquirer ra WHERE ra.firm_id = f.id "
            f"AND ra.buyer_kind = {p.add(filters.acq_buyer_kind)})"
        )
    if filters.acq_platform:
        where.append(
            "EXISTS (SELECT 1 FROM firm_role_acquirer ra WHERE ra.firm_id = f.id "
            "AND ra.platform_or_addon IN ('platform', 'both'))"
        )
    if filters.ebitda_min is not None or filters.ebitda_max is not None:
        lo = filters.ebitda_min if filters.ebitda_min is not None else 0
        hi = filters.ebitda_max if filters.ebitda_max is not None else 1e18
        where.append(
            f"EXISTS (SELECT 1 FROM firm_role_acquirer ra WHERE ra.firm_id = f.id "
            f"AND COALESCE(ra.ebitda_min, 0) <= {p.add(hi)} "
            f"AND COALESCE(ra.ebitda_max, 1e18) >= {p.add(lo)})"
        )
    if filters.acq_min_count is not None:
        acq_conds = ["a.acquirer_firm_id = f.id"]
        join = ""
        if filters.acq_sector is not None:
            join = (
                "JOIN company_sector cs ON cs.company_id = a.target_company_id "
                f"JOIN sector s ON s.id = cs.sector_id AND s.slug = {p.add(filters.acq_sector)}"
            )
        if filters.acq_within_months is not None:
            acq_conds.append(
                f"a.announced_at >= {p.add(_months_cutoff(today, filters.acq_within_months))}"
            )
        if filters.ev_min is not None:
            acq_conds.append(f"a.ev_amount >= {p.add(filters.ev_min)}")
        if filters.ev_max is not None:
            acq_conds.append(f"a.ev_amount <= {p.add(filters.ev_max)}")
        where.append(
            f"(SELECT count(*) FROM acquisition a {join} WHERE {' AND '.join(acq_conds)}) "
            f">= {p.add(filters.acq_min_count)}"
        )

    # LP predicates
    if filters.asset_class is not None:
        alloc = f"la.asset_class = {p.add(filters.asset_class)}"
        if filters.allocation_min_pct is not None:
            alloc += f" AND la.pct >= {p.add(filters.allocation_min_pct)}"
        where.append(f"EXISTS (SELECT 1 FROM lp_allocation la WHERE la.firm_id = f.id AND {alloc})")
    if filters.committed_within_months is not None:
        commit_conds = [
            "lc.firm_id = f.id",
            f"lc.committed_at >= {p.add(_months_cutoff(today, filters.committed_within_months))}",
        ]
        if filters.committed_first_time_only:
            commit_conds.append("lc.first_time_fund")
        where.append(f"EXISTS (SELECT 1 FROM lp_commitment lc WHERE {' AND '.join(commit_conds)})")

    if filters.require_verified_contact:
        sla_cutoff = datetime.combine(today, time.min, tzinfo=timezone.utc) - timedelta(
            days=sla_days
        )
        ph = p.add(sla_cutoff)
        where.append(
            "EXISTS (SELECT 1 FROM partner pr JOIN contact_channel cc ON cc.partner_id = pr.id "
            "WHERE pr.firm_id = f.id "
            "AND cc.deliverability_status = 'deliverable' "
            f"AND cc.deliverability_checked_at >= {ph} "
            "AND pr.role_currency_status = 'current' "
            f"AND pr.role_currency_checked_at >= {ph})"
        )

    if not filters.include_inactive:
        where.append("COALESCE(fa.is_active, false)")

    # --- ranking within the matched set (soft signals only; never affects WHERE) ---
    soft_ph = p.add(filters.soft_sectors)
    today_ph = p.add(today)
    # group-expanded sector match: a queried group slug matches all its leaf sectors.
    match = (
        f"(s.slug = ANY({soft_ph}) "
        f"OR s.parent_id IN (SELECT id FROM sector WHERE slug = ANY({soft_ph})))"
    )
    sector_score = (
        "COALESCE((SELECT sum(fsp.weight) FROM firm_sector_profile fsp "
        f"JOIN sector s ON s.id = fsp.sector_id WHERE fsp.firm_id = f.id AND {match}), 0)"
    )
    recency_date = (
        "COALESCE((SELECT max(fsp.last_deal_at) FROM firm_sector_profile fsp "
        "JOIN sector s ON s.id = fsp.sector_id "
        f"WHERE fsp.firm_id = f.id AND {match}), fa.last_deal_at)"
    )
    recency_score = (
        f"CASE WHEN {recency_date} IS NULL THEN 0 ELSE "
        f"power(0.5, (({today_ph}::date - {recency_date})::numeric / {RANK_HALFLIFE_DAYS})) END"
    )
    cadence_expr = "(COALESCE(fc.score, 50) / 100.0)"
    if query_vec is not None:
        qph = p.add(query_vec)
        text_expr = f"COALESCE(1 - (fe.embedding <=> {qph}::vector), 0)"
    else:
        text_expr = "0"
    rank_expr = (
        f"({RANK_W_SECTOR} * {sector_score} + {RANK_W_RECENCY} * {recency_score} "
        f"+ {RANK_W_CADENCE} * {cadence_expr} + {RANK_W_TEXT} * {text_expr})"
    )

    sql = (
        "SELECT f.id::text, f.slug, f.name, f.investor_type, f.hq_country, "
        "COALESCE(fa.is_active, false) AS is_active, fc.score AS cadence_score, "
        f"{rank_expr} AS rank_score "
        "FROM firm f "
        "LEFT JOIN firm_activity fa ON fa.firm_id = f.id "
        "LEFT JOIN firm_cadence fc ON fc.firm_id = f.id "
        "LEFT JOIN firm_embedding fe ON fe.firm_id = f.id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY rank_score DESC, f.slug"
    return sql, p.values


async def execute_search(
    conn: asyncpg.Connection, filters: QueryFilters, settings: Settings, today: date | None = None
) -> list[SearchResultFirm]:
    today = today or date.today()
    query_vec = None
    if filters.soft_text:
        vec = get_embedder(settings).embed([filters.soft_text])[0]
        query_vec = to_pgvector(vec)
    sql, params = build_search_sql(
        filters, today=today, sla_days=settings.contact_sla_days, query_vec=query_vec
    )
    rows = await conn.fetch(sql, *params)
    return [
        SearchResultFirm(
            id=r["id"],
            slug=r["slug"],
            name=r["name"],
            investor_type=r["investor_type"],
            hq_country=r["hq_country"],
            is_active=r["is_active"],
            cadence_score=r["cadence_score"],
            rank_score=float(r["rank_score"]) if r["rank_score"] is not None else None,
        )
        for r in rows
    ]
