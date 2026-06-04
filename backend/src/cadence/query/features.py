"""Embedding-ranked Look-Alike and co-investor (warm-intro) discovery.

Both rank/derive within structured sets; neither gates recall for the main search (ADR 0004).
"""

from __future__ import annotations

from datetime import date, timedelta

import asyncpg

DAYS_PER_MONTH = 30.44


async def coinvestors(
    conn: asyncpg.Connection,
    *,
    lead_slug: str,
    sector: str,
    within_months: int,
    today: date,
    limit: int = 50,
) -> list[dict]:
    """Firms that shared a funding round with `lead_slug` in `sector` within the window."""
    cutoff = today - timedelta(days=round(within_months * DAYS_PER_MONTH))
    rows = await conn.fetch(
        """
        SELECT DISTINCT f.slug, f.name
        FROM deal d_lead
        JOIN firm lead ON lead.id = d_lead.firm_id AND lead.slug = $1
        JOIN deal d_co ON d_co.round_id = d_lead.round_id AND d_co.firm_id <> d_lead.firm_id
        JOIN firm f ON f.id = d_co.firm_id
        JOIN company_sector cs ON cs.company_id = d_co.company_id
        JOIN sector s ON s.id = cs.sector_id
          AND (s.slug = $2 OR s.parent_id IN (SELECT id FROM sector WHERE slug = $2))
        WHERE d_lead.round_id IS NOT NULL AND d_co.announced_at >= $3
        ORDER BY f.slug
        LIMIT $4
        """,
        lead_slug,
        sector,
        cutoff,
        limit,
    )
    return [{"slug": r["slug"], "name": r["name"]} for r in rows]


async def look_alike(conn: asyncpg.Connection, *, firm_slug: str, limit: int = 20) -> list[dict]:
    """Rank other firms by embedding cosine similarity to the given firm (exact, no ANN gate)."""
    rows = await conn.fetch(
        """
        WITH t AS (
            SELECT fe.embedding FROM firm_embedding fe
            JOIN firm f ON f.id = fe.firm_id WHERE f.slug = $1
        )
        SELECT f.slug, f.name, (1 - (fe.embedding <=> t.embedding)) AS similarity
        FROM firm_embedding fe JOIN firm f ON f.id = fe.firm_id, t
        WHERE f.slug <> $1
        ORDER BY similarity DESC
        LIMIT $2
        """,
        firm_slug,
        limit,
    )
    return [
        {"slug": r["slug"], "name": r["name"], "similarity": float(r["similarity"])} for r in rows
    ]


async def comps(
    conn: asyncpg.Connection, *, sector: str, ev_min: float, ev_max: float, limit: int = 10
) -> list[dict]:
    """Comparable-deal engine: recent acquisitions in `sector` within an EV band (sell-side)."""
    rows = await conn.fetch(
        """
        SELECT c.slug AS target_slug, c.name, a.ev_amount, a.revenue_multiple, a.advisor,
               a.announced_at
        FROM acquisition a
        JOIN company c ON c.id = a.target_company_id
        JOIN company_sector cs ON cs.company_id = a.target_company_id
        JOIN sector s ON s.id = cs.sector_id
          AND (s.slug = $1 OR s.parent_id IN (SELECT id FROM sector WHERE slug = $1))
        WHERE a.ev_amount BETWEEN $2 AND $3
        ORDER BY a.announced_at DESC
        LIMIT $4
        """,
        sector,
        ev_min,
        ev_max,
        limit,
    )
    return [
        {
            "target_slug": r["target_slug"],
            "name": r["name"],
            "ev_amount": float(r["ev_amount"]) if r["ev_amount"] is not None else None,
            "revenue_multiple": float(r["revenue_multiple"]) if r["revenue_multiple"] else None,
            "advisor": r["advisor"],
            "announced_at": r["announced_at"],
        }
        for r in rows
    ]


async def conflict_check(
    conn: asyncpg.Connection, *, target_firm_slugs: list[str], competitor_company_slugs: list[str]
) -> list[str]:
    """Which target firms already back any named competitor company (cross-cutting check)."""
    rows = await conn.fetch(
        """
        SELECT DISTINCT f.slug
        FROM deal d
        JOIN firm f ON f.id = d.firm_id
        JOIN company c ON c.id = d.company_id
        WHERE f.slug = ANY($1) AND c.slug = ANY($2)
        ORDER BY f.slug
        """,
        target_firm_slugs,
        competitor_company_slugs,
    )
    return [r["slug"] for r in rows]
