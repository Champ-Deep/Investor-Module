from datetime import date

from fastapi import APIRouter, Request
from pydantic import BaseModel

from cadence.models.query import ParsedQuery, QueryFilters
from cadence.query.features import coinvestors, look_alike
from cadence.query.parse import parse_query
from cadence.query.planner import execute_search

router = APIRouter(tags=["search"])


class ParseRequest(BaseModel):
    query: str


class CoinvestRequest(BaseModel):
    lead_slug: str
    sector: str
    within_months: int = 36


@router.post("/parse")
async def parse(req: ParseRequest, request: Request) -> ParsedQuery:
    return parse_query(req.query, request.app.state.settings)


@router.post("/search")
async def search(filters: QueryFilters, request: Request) -> dict:
    pool = request.app.state.pool
    settings = request.app.state.settings
    async with pool.acquire() as conn:
        results = await execute_search(conn, filters, settings)
        firms = [r.model_dump() for r in results]
        ids = [f["id"] for f in firms]
        if ids:
            sector_rows = await conn.fetch(
                "SELECT fid, name FROM ("
                "  SELECT fsp.firm_id::text AS fid, s.name,"
                "    row_number() OVER (PARTITION BY fsp.firm_id ORDER BY fsp.weight DESC) AS rn"
                "  FROM firm_sector_profile fsp JOIN sector s ON s.id = fsp.sector_id"
                "  WHERE fsp.firm_id::text = ANY($1::text[])"
                ") t WHERE rn <= 3",
                ids,
            )
            top_sectors: dict[str, list[str]] = {}
            for r in sector_rows:
                top_sectors.setdefault(r["fid"], []).append(r["name"])
            count_rows = await conn.fetch(
                "SELECT firm_id::text AS fid, count(*) AS n FROM deal "
                "WHERE firm_id::text = ANY($1::text[]) GROUP BY firm_id",
                ids,
            )
            deal_counts = {r["fid"]: r["n"] for r in count_rows}
            cs_rows = await conn.fetch(
                "SELECT fcs.firm_id::text AS fid, st.slug, fcs.median_amount "
                "FROM firm_check_size fcs JOIN stage st ON st.slug = fcs.stage_slug "
                "WHERE fcs.firm_id::text = ANY($1::text[]) ORDER BY st.sort_order",
                ids,
            )
            # Typical-check range = span of the firm's per-stage MEDIAN checks. Medians are robust
            # to the pro-rated round-size proxy's outliers (raw min/max produced noise like $2).
            stages_by: dict[str, list[str]] = {}
            check_lo: dict[str, float] = {}
            check_hi: dict[str, float] = {}
            for r in cs_rows:
                stages_by.setdefault(r["fid"], []).append(r["slug"])
                if r["median_amount"] is not None:
                    v = float(r["median_amount"])
                    check_lo[r["fid"]] = min(check_lo.get(r["fid"], v), v)
                    check_hi[r["fid"]] = max(check_hi.get(r["fid"], v), v)
            for f in firms:
                f["top_sectors"] = top_sectors.get(f["id"], [])
                f["deal_count"] = deal_counts.get(f["id"], 0)
                f["stages"] = stages_by.get(f["id"], [])
                f["check_lo"] = check_lo.get(f["id"])
                f["check_hi"] = check_hi.get(f["id"])
    return {"count": len(firms), "firms": firms}


@router.get("/look-alike/{firm_slug}")
async def look_alike_route(firm_slug: str, request: Request) -> dict:
    async with request.app.state.pool.acquire() as conn:
        results = await look_alike(conn, firm_slug=firm_slug)
    return {"count": len(results), "firms": results}


@router.post("/coinvestors")
async def coinvestors_route(req: CoinvestRequest, request: Request) -> dict:
    async with request.app.state.pool.acquire() as conn:
        results = await coinvestors(
            conn,
            lead_slug=req.lead_slug,
            sector=req.sector,
            within_months=req.within_months,
            today=date.today(),
        )
    return {"count": len(results), "firms": results}
