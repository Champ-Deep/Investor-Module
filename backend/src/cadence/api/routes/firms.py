import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from cadence.verification import compute_verified

router = APIRouter(tags=["firms"])


@router.get("/firms/{slug}")
async def firm_profile(slug: str, request: Request) -> dict:
    pool = request.app.state.pool
    settings = request.app.state.settings
    now = datetime.now(timezone.utc)

    async with pool.acquire() as conn:
        firm = await conn.fetchrow(
            "SELECT id::text AS id, slug, name, investor_type, hq_country, hq_region, hq_city, "
            "website, founded_year, gp_count, aum, dry_powder, description, last_updated_at "
            "FROM firm WHERE slug = $1",
            slug,
        )
        if firm is None:
            raise HTTPException(status_code=404, detail="firm not found")
        fid = firm["id"]

        roles = [
            r["role"]
            for r in await conn.fetch("SELECT role FROM capital_role WHERE firm_id = $1", fid)
        ]
        activity = await conn.fetchrow(
            "SELECT is_active, new_deal_count, last_deal_at FROM firm_activity WHERE firm_id = $1",
            fid,
        )
        cad = await conn.fetchrow(
            "SELECT score, model_version, contributions, readiness_hit_rate "
            "FROM firm_cadence WHERE firm_id = $1",
            fid,
        )
        sectors = await conn.fetch(
            "SELECT s.slug, s.name, fsp.weight FROM firm_sector_profile fsp "
            "JOIN sector s ON s.id = fsp.sector_id WHERE fsp.firm_id = $1 "
            "ORDER BY fsp.weight DESC LIMIT 6",
            fid,
        )
        checks = await conn.fetch(
            "SELECT stage_slug, min_amount, median_amount, max_amount, deal_count "
            "FROM firm_check_size WHERE firm_id = $1 "
            "ORDER BY (SELECT sort_order FROM stage WHERE slug = stage_slug)",
            fid,
        )
        partners = await conn.fetch(
            "SELECT id::text AS id, name, title, location, role_currency_status, "
            "role_currency_checked_at FROM partner WHERE firm_id = $1 ORDER BY name",
            fid,
        )
        recent_deals = await conn.fetch(
            "SELECT c.name AS company, d.stage_slug, d.is_new, d.is_lead, d.announced_at "
            "FROM deal d JOIN company c ON c.id = d.company_id WHERE d.firm_id = $1 "
            "ORDER BY d.announced_at DESC LIMIT 12",
            fid,
        )
        deal_count = await conn.fetchval("SELECT count(*) FROM deal WHERE firm_id = $1", fid)

        partner_out = []
        for p in partners:
            contacts = await conn.fetch(
                "SELECT kind, value, deliverability_status, deliverability_checked_at "
                "FROM contact_channel WHERE partner_id = $1",
                p["id"],
            )
            contact_out = []
            for c in contacts:
                state = compute_verified(
                    deliverability_status=c["deliverability_status"],
                    deliverability_checked_at=c["deliverability_checked_at"],
                    role_currency_status=p["role_currency_status"],
                    role_currency_checked_at=p["role_currency_checked_at"],
                    sla_days=settings.contact_sla_days,
                    now=now,
                )
                contact_out.append(
                    {
                        "kind": c["kind"],
                        "value": c["value"],
                        "deliverability_status": c["deliverability_status"],
                        "deliverability_checked_at": c["deliverability_checked_at"],
                        "verified_state": state.value,
                    }
                )
            partner_out.append(
                {
                    "name": p["name"],
                    "title": p["title"],
                    "location": p["location"],
                    "role_currency_status": p["role_currency_status"],
                    "role_currency_checked_at": p["role_currency_checked_at"],
                    "contacts": contact_out,
                }
            )

    cadence = None
    if cad is not None:
        factors = json.loads(cad["contributions"]) if cad["contributions"] else []
        cadence = {
            "score": cad["score"],
            "model_version": cad["model_version"],
            "readiness_hit_rate": (
                float(cad["readiness_hit_rate"]) if cad["readiness_hit_rate"] is not None else None
            ),
            "top_factors": factors[:3],
        }

    return {
        "firm": dict(firm),
        "roles": roles,
        "is_active": activity["is_active"] if activity else False,
        "cadence": cadence,
        "sector_profile": [
            {"slug": s["slug"], "name": s["name"], "weight": float(s["weight"])} for s in sectors
        ],
        "check_sizes": [dict(c) for c in checks],
        "partners": partner_out,
        "recent_deals": [dict(d) for d in recent_deals],
        "deal_count": deal_count,
    }
