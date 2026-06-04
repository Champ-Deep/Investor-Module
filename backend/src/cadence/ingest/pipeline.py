"""Insert Raw* records into the normalized store in dependency order.

Pure mapping: it does not compute derived tables (sector profile, check size, activity, cadence,
embeddings) — those are M3/M5/M6 and run after ingest.
"""

from __future__ import annotations

import asyncpg

from cadence.datasource.base import DataSource, DealSource


async def _slug_map(conn: asyncpg.Connection, table: str) -> dict[str, str]:
    rows = await conn.fetch(f"SELECT slug, id FROM {table}")
    return {r["slug"]: r["id"] for r in rows}


async def ingest(conn: asyncpg.Connection, source: DataSource, deals: DealSource) -> dict[str, int]:
    sectors = await _slug_map(conn, "sector")
    thesis_tags = await _slug_map(conn, "thesis_tag")
    counts: dict[str, int] = {}

    def sector_id(slug: str) -> str:
        try:
            return sectors[slug]
        except KeyError as exc:  # surfaces generator/taxonomy mismatches loudly
            raise KeyError(f"unknown sector slug in seed: {slug!r}") from exc

    # Companies + their sector labels.
    company_ids: dict[str, str] = {}
    for c in source.fetch_companies():
        cid = await conn.fetchval(
            "INSERT INTO company (slug, name, description, hq_country) "
            "VALUES ($1,$2,$3,$4) RETURNING id",
            c.slug,
            c.name,
            c.description,
            c.hq_country,
        )
        company_ids[c.slug] = cid
        for slug in c.primary_sectors:
            await conn.execute(
                "INSERT INTO company_sector (company_id, sector_id, rank) VALUES ($1,$2,'primary') "
                "ON CONFLICT DO NOTHING",
                cid,
                sector_id(slug),
            )
        for slug in c.secondary_sectors:
            await conn.execute(
                "INSERT INTO company_sector (company_id, sector_id, rank) "
                "VALUES ($1, $2, 'secondary') ON CONFLICT DO NOTHING",
                cid,
                sector_id(slug),
            )
    counts["companies"] = len(company_ids)

    # Firms + every nested facet.
    firm_ids: dict[str, str] = {}
    partner_count = deal_count = 0
    for f in source.fetch_firms():
        fid = await conn.fetchval(
            "INSERT INTO firm (slug, name, investor_type, hq_country, hq_region, hq_city, website, "
            "founded_year, gp_count, aum, dry_powder, description) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING id",
            f.slug,
            f.name,
            f.investor_type,
            f.hq_country,
            f.hq_region,
            f.hq_city,
            f.website,
            f.founded_year,
            f.gp_count,
            f.aum,
            f.dry_powder,
            f.description,
        )
        firm_ids[f.slug] = fid

        for geo in f.mandate_geos:
            await conn.execute(
                "INSERT INTO firm_geo (firm_id, kind, value) VALUES ($1,'mandate',$2) "
                "ON CONFLICT DO NOTHING",
                fid,
                geo,
            )
        for geo in f.lp_base_geos:
            await conn.execute(
                "INSERT INTO firm_geo (firm_id, kind, value) VALUES ($1,'lp_base',$2) "
                "ON CONFLICT DO NOTHING",
                fid,
                geo,
            )

        for role in f.roles:
            await conn.execute(
                "INSERT INTO capital_role (firm_id, role) VALUES ($1,$2) ON CONFLICT DO NOTHING",
                fid,
                role,
            )

        if f.role_direct is not None:
            await conn.execute(
                "INSERT INTO firm_role_direct (firm_id, takes_board_seat, co_invest_friendly) "
                "VALUES ($1,$2,$3)",
                fid,
                f.role_direct.takes_board_seat,
                f.role_direct.co_invest_friendly,
            )
        if f.role_lp is not None:
            await conn.execute(
                "INSERT INTO firm_role_lp (firm_id, ticket_min, ticket_max) VALUES ($1,$2,$3)",
                fid,
                f.role_lp.ticket_min,
                f.role_lp.ticket_max,
            )
            for a in f.role_lp.allocations:
                await conn.execute(
                    "INSERT INTO lp_allocation (firm_id, asset_class, pct) VALUES ($1,$2,$3) "
                    "ON CONFLICT DO NOTHING",
                    fid,
                    a.asset_class,
                    a.pct,
                )
            for cm in f.role_lp.commitments:
                await conn.execute(
                    "INSERT INTO lp_commitment (firm_id, target_gp_name, first_time_fund, amount, "
                    "committed_at) VALUES ($1,$2,$3,$4,$5)",
                    fid,
                    cm.target_gp_name,
                    cm.first_time_fund,
                    cm.amount,
                    cm.committed_at,
                )
        if f.role_acquirer is not None:
            ra = f.role_acquirer
            await conn.execute(
                "INSERT INTO firm_role_acquirer (firm_id, buyer_kind, platform_or_addon, "
                "ebitda_min, ebitda_max, revenue_min, revenue_max) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                fid,
                ra.buyer_kind,
                ra.platform_or_addon,
                ra.ebitda_min,
                ra.ebitda_max,
                ra.revenue_min,
                ra.revenue_max,
            )

        for fund in f.funds:
            await conn.execute(
                "INSERT INTO fund (firm_id, name, vintage_year, size, status, dry_powder) "
                "VALUES ($1,$2,$3,$4,$5,$6)",
                fid,
                fund.name,
                fund.vintage_year,
                fund.size,
                fund.status,
                fund.dry_powder,
            )

        for slug in f.thesis_tag_slugs:
            await conn.execute(
                "INSERT INTO firm_thesis_tag (firm_id, tag_id) VALUES ($1,$2) "
                "ON CONFLICT DO NOTHING",
                fid,
                thesis_tags[slug],
            )
        if f.thesis_narrative:
            await conn.execute(
                "INSERT INTO thesis_narrative (firm_id, narrative) VALUES ($1,$2)",
                fid,
                f.thesis_narrative,
            )

        for p in f.partners:
            pid = await conn.fetchval(
                "INSERT INTO partner (firm_id, name, title, location, linkedin_url, "
                "role_currency_status, role_currency_checked_at) VALUES ($1,$2,$3,$4,$5,$6,$7) "
                "RETURNING id",
                fid,
                p.name,
                p.title,
                p.location,
                p.linkedin_url,
                p.role_currency_status,
                p.role_currency_checked_at,
            )
            partner_count += 1
            for slug in p.sector_lead_slugs:
                await conn.execute(
                    "INSERT INTO partner_sector_lead (partner_id, sector_id) VALUES ($1,$2) "
                    "ON CONFLICT DO NOTHING",
                    pid,
                    sector_id(slug),
                )
            for st in p.stage_focus:
                await conn.execute(
                    "INSERT INTO partner_stage_focus (partner_id, stage_slug) VALUES ($1,$2) "
                    "ON CONFLICT DO NOTHING",
                    pid,
                    st,
                )
            for ch in p.contacts:
                await conn.execute(
                    "INSERT INTO contact_channel (partner_id, kind, value, deliverability_status, "
                    "deliverability_checked_at) VALUES ($1,$2,$3,$4,$5)",
                    pid,
                    ch.kind,
                    ch.value,
                    ch.deliverability_status,
                    ch.deliverability_checked_at,
                )
    counts["firms"] = len(firm_ids)
    counts["partners"] = partner_count

    # Rounds, then deals (linked to rounds), then acquisitions.
    round_ids: dict[str, str] = {}
    for r in deals.fetch_rounds():
        rid = await conn.fetchval(
            "INSERT INTO funding_round (company_id, stage_slug, announced_at, round_size) "
            "VALUES ($1,$2,$3,$4) RETURNING id",
            company_ids[r.company_slug],
            r.stage,
            r.announced_at,
            r.round_size,
        )
        round_ids[r.ref] = rid
    counts["rounds"] = len(round_ids)

    for d in deals.fetch_deals():
        await conn.execute(
            "INSERT INTO deal (firm_id, company_id, round_id, stage_slug, check_amount, is_new, "
            "is_lead, announced_at) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
            firm_ids[d.firm_slug],
            company_ids[d.company_slug],
            round_ids.get(d.round_ref) if d.round_ref else None,
            d.stage,
            d.check_amount,
            d.is_new,
            d.is_lead,
            d.announced_at,
        )
        deal_count += 1
    counts["deals"] = deal_count

    acq_count = 0
    for a in deals.fetch_acquisitions():
        await conn.execute(
            "INSERT INTO acquisition (acquirer_firm_id, target_company_id, ev_amount, "
            "revenue_multiple, ebitda_at_deal, advisor, deal_kind, announced_at) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
            firm_ids.get(a.acquirer_firm_slug) if a.acquirer_firm_slug else None,
            company_ids[a.target_company_slug],
            a.ev_amount,
            a.revenue_multiple,
            a.ebitda_at_deal,
            a.advisor,
            a.deal_kind,
            a.announced_at,
        )
        acq_count += 1
    counts["acquisitions"] = acq_count

    return counts
