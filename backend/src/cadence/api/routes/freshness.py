from fastapi import APIRouter, Request

router = APIRouter(tags=["freshness"])

_DELIVERABILITY_SQL = """
SELECT count(*) AS total,
       count(*) FILTER (WHERE deliverability_checked_at >= now() - interval '90 days') AS within_90,
       count(*) FILTER (WHERE deliverability_checked_at
           >= now() - interval '180 days') AS within_180,
       count(*) FILTER (WHERE deliverability_checked_at IS NULL) AS undated,
       count(*) FILTER (WHERE deliverability_status = 'catch_all') AS catch_all
FROM contact_channel WHERE kind = 'email'
"""

_ROLE_SQL = """
SELECT count(*) AS total,
       count(*) FILTER (WHERE role_currency_checked_at >= now() - interval '90 days') AS within_90,
       count(*) FILTER (WHERE role_currency_checked_at
           >= now() - interval '180 days') AS within_180,
       count(*) FILTER (WHERE role_currency_checked_at IS NULL) AS undated
FROM partner
"""

_VERIFIED_FIRMS_SQL = """
SELECT count(DISTINCT p.firm_id)
FROM partner p JOIN contact_channel cc ON cc.partner_id = p.id
WHERE cc.deliverability_status = 'deliverable'
  AND cc.deliverability_checked_at >= now() - make_interval(days => $1)
  AND p.role_currency_status = 'current'
  AND p.role_currency_checked_at >= now() - make_interval(days => $1)
"""


@router.get("/freshness")
async def freshness(request: Request) -> dict:
    sla = request.app.state.settings.contact_sla_days
    async with request.app.state.pool.acquire() as conn:
        deliverability = await conn.fetchrow(_DELIVERABILITY_SQL)
        role = await conn.fetchrow(_ROLE_SQL)
        verified_firms = await conn.fetchval(_VERIFIED_FIRMS_SQL, sla)
        total_firms = await conn.fetchval("SELECT count(*) FROM firm")

    return {
        "sla_days": sla,
        "email_deliverability": dict(deliverability),
        "role_currency": dict(role),
        "firms_with_verified_contact": verified_firms,
        "total_firms": total_firms,
        "verified_coverage_pct": (
            round(100 * verified_firms / total_firms, 1) if total_firms else 0.0
        ),
    }
