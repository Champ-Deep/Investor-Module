"""Recompute derived intelligence from the base tables. Run after ingest and on refresh.

- firm_sector_profile: recency-weighted aggregation of NEW-deal sectors (half-life decay),
  normalized per firm; secondary sector labels contribute at half weight.
- firm_check_size: per-stage min/median/max/count from NEW deals.
- firm_activity: deal velocity in the activity window + role-aware Active-Firm gate.
"""

import asyncio
from datetime import date, timedelta

import asyncpg

from cadence.config import get_settings

HALFLIFE_MONTHS = 18
DAYS_PER_MONTH = 30.44


async def _sector_profile(conn: asyncpg.Connection, today: date, halflife_days: float) -> None:
    await conn.execute(
        """
        WITH raw AS (
            SELECT d.firm_id, cs.sector_id,
                   SUM(power(0.5, ($1::date - d.announced_at)::numeric / $2)
                       * CASE cs.rank WHEN 'primary' THEN 1.0 ELSE 0.5 END) AS w,
                   COUNT(*) AS cnt,
                   MAX(d.announced_at) AS last_at
            FROM deal d
            JOIN company_sector cs ON cs.company_id = d.company_id
            WHERE d.is_new
            GROUP BY d.firm_id, cs.sector_id
        ),
        tot AS (SELECT firm_id, SUM(w) AS total FROM raw GROUP BY firm_id)
        INSERT INTO firm_sector_profile (firm_id, sector_id, weight, new_deal_count, last_deal_at)
        SELECT r.firm_id, r.sector_id, (r.w / NULLIF(t.total, 0))::numeric(8,6), r.cnt, r.last_at
        FROM raw r JOIN tot t ON t.firm_id = r.firm_id
        """,
        today,
        halflife_days,
    )


async def _check_size(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        INSERT INTO firm_check_size (firm_id, stage_slug, min_amount, median_amount,
                                     max_amount, deal_count)
        SELECT firm_id, stage_slug,
               MIN(check_amount),
               percentile_cont(0.5) WITHIN GROUP (ORDER BY check_amount),
               MAX(check_amount),
               COUNT(*)
        FROM deal
        WHERE is_new AND check_amount IS NOT NULL
        GROUP BY firm_id, stage_slug
        """
    )


async def _activity(conn: asyncpg.Connection, cutoff: date, window_months: int) -> None:
    # Role-aware Active-Firm gate: direct investors need a recent deal + an open/investing fund;
    # acquirers a recent acquisition (+fund unless strategic); LPs a recent commitment.
    await conn.execute(
        """
        INSERT INTO firm_activity (firm_id, window_months, new_deal_count, total_deal_count,
                                   last_deal_at, has_open_or_investing_fund, is_active)
        SELECT f.id, $2,
               COALESCE(dv.new_cnt, 0), COALESCE(dv.tot_cnt, 0), dv.last_at,
               COALESCE(fnd.has_fund, false),
               (
                 (EXISTS (SELECT 1 FROM capital_role cr
                          WHERE cr.firm_id = f.id AND cr.role = 'direct_investor')
                  AND COALESCE(dv.recent, false) AND COALESCE(fnd.has_fund, false))
                 OR (EXISTS (SELECT 1 FROM capital_role cr
                             WHERE cr.firm_id = f.id AND cr.role = 'strategic_acquirer')
                     AND COALESCE(acq.recent, false)
                     AND (COALESCE(fnd.has_fund, false) OR ra.buyer_kind = 'strategic'))
                 OR (EXISTS (SELECT 1 FROM capital_role cr
                             WHERE cr.firm_id = f.id AND cr.role = 'lp_allocator')
                     AND COALESCE(cmt.recent, false))
               )
        FROM firm f
        LEFT JOIN (
            SELECT firm_id,
                   COUNT(*) FILTER (WHERE is_new) AS new_cnt,
                   COUNT(*) AS tot_cnt,
                   MAX(announced_at) AS last_at,
                   bool_or(announced_at >= $1) AS recent
            FROM deal GROUP BY firm_id
        ) dv ON dv.firm_id = f.id
        LEFT JOIN (
            SELECT firm_id, bool_or(status IN ('open', 'investing')) AS has_fund
            FROM fund GROUP BY firm_id
        ) fnd ON fnd.firm_id = f.id
        LEFT JOIN (
            SELECT acquirer_firm_id AS firm_id, bool_or(announced_at >= $1) AS recent
            FROM acquisition WHERE acquirer_firm_id IS NOT NULL GROUP BY acquirer_firm_id
        ) acq ON acq.firm_id = f.id
        LEFT JOIN (
            SELECT firm_id, bool_or(committed_at >= $1) AS recent
            FROM lp_commitment GROUP BY firm_id
        ) cmt ON cmt.firm_id = f.id
        LEFT JOIN firm_role_acquirer ra ON ra.firm_id = f.id
        """,
        cutoff,
        window_months,
    )


async def recompute_all(
    conn: asyncpg.Connection, *, activity_window_months: int, today: date | None = None
) -> None:
    today = today or date.today()
    halflife_days = HALFLIFE_MONTHS * DAYS_PER_MONTH
    cutoff = today - timedelta(days=round(activity_window_months * DAYS_PER_MONTH))
    await conn.execute("TRUNCATE firm_sector_profile, firm_check_size, firm_activity")
    await _sector_profile(conn, today, halflife_days)
    await _check_size(conn)
    await _activity(conn, cutoff, activity_window_months)


async def _main() -> None:
    settings = get_settings()
    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        await recompute_all(conn, activity_window_months=settings.activity_window_months)
    finally:
        await conn.close()
    print("derived intelligence recomputed")


if __name__ == "__main__":
    asyncio.run(_main())
