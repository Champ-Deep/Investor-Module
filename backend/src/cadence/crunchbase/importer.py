"""Import the Crunchbase-2015 CSVs into the normalized store (ADR 0008).

Two streaming passes over investments.csv: count deals per investor, keep those with >= min_deals,
then build rows for the selected set. Firms/companies/rounds get client-generated UUIDs so we can
bulk-load with asyncpg COPY (fast at ~150k deal rows). Derived tables/embeddings/Cadence run after.
"""

from __future__ import annotations

import csv
import pathlib
import re
import uuid
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import asyncpg
import httpx

from cadence.config import Settings
from cadence.crunchbase.map import investor_type_for, iso2, sectors_for, stage_for

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_RAW_BASE = "https://raw.githubusercontent.com/notpeter/crunchbase-data/master"
_DATA_FILES = ["investments.csv", "companies.csv", "acquisitions.csv"]


def _ensure_data(data_dir: pathlib.Path) -> None:
    """Download the Crunchbase CSVs if they aren't cached — lets the Railway container self-seed."""
    data_dir.mkdir(parents=True, exist_ok=True)
    for name in _DATA_FILES:
        path = data_dir / name
        if path.exists() and path.stat().st_size > 0:
            continue
        with httpx.stream("GET", f"{_RAW_BASE}/{name}", timeout=180, follow_redirects=True) as resp:
            resp.raise_for_status()
            with open(path, "wb") as fh:
                for chunk in resp.iter_bytes():
                    fh.write(chunk)


def _slugify(value: str) -> str:
    return _SLUG_RE.sub("-", (value or "").lower()).strip("-") or "x"


def _slug_from_permalink(permalink: str, fallback: str) -> str:
    tail = (permalink or "").rstrip("/").rsplit("/", 1)[-1]
    return _slugify(tail or fallback)


def _parse_date(value: str | None) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _year(value: str | None) -> int | None:
    d = _parse_date(value)
    return d.year if d else None


def _dec(value: str | None) -> Decimal | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


async def import_crunchbase(conn: asyncpg.Connection, settings: Settings) -> dict[str, int]:
    data_dir = pathlib.Path(settings.crunchbase_data_dir)
    _ensure_data(data_dir)
    inv_path = data_dir / "investments.csv"
    comp_path = data_dir / "companies.csv"
    acq_path = data_dir / "acquisitions.csv"
    min_deals = settings.crunchbase_min_deals

    sector_id = {r["slug"]: r["id"] for r in await conn.fetch("SELECT slug, id FROM sector")}

    companies_meta: dict[str, dict] = {}
    with open(comp_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            companies_meta[row["permalink"]] = row

    # Pass 1: count deals per investor (to select active ones) + investors per round (lead proxy).
    counts: Counter[str] = Counter()
    round_investors: Counter[str] = Counter()
    with open(inv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = row["investor_permalink"] or row["investor_name"]
            if key:
                counts[key] += 1
            rp = row["funding_round_permalink"]
            if rp:
                round_investors[rp] += 1
    selected = {k for k, c in counts.items() if c >= min_deals}

    # Pass 2: build rows for the selected investors.
    firms: dict[str, dict] = {}
    firm_by_permalink: dict[str, dict] = {}
    companies: dict[str, dict] = {}
    company_sectors: list[tuple] = []
    seen_cs: set[tuple] = set()
    rounds: dict[str, dict] = {}
    deals: list[dict] = []
    used_slugs: set[str] = set()

    def _unique(slug: str) -> str:
        base, i = slug, 2
        while slug in used_slugs:
            slug = f"{base}-{i}"
            i += 1
        used_slugs.add(slug)
        return slug

    def get_company(permalink: str, name: str, category_list: str, country: str) -> dict:
        c = companies.get(permalink)
        if c is None:
            cid = uuid.uuid4()
            c = {
                "id": cid,
                "slug": _unique(_slug_from_permalink(permalink, name)),
                "name": name or permalink,
                "country": iso2(country),
            }
            companies[permalink] = c
            for i, slug in enumerate(sectors_for(category_list)):
                sid = sector_id.get(slug)
                if sid and (cid, sid) not in seen_cs:
                    seen_cs.add((cid, sid))
                    company_sectors.append((cid, sid, "primary" if i == 0 else "secondary"))
        return c

    with open(inv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = row["investor_permalink"] or row["investor_name"]
            if key not in selected:
                continue
            funded = _parse_date(row["funded_at"])
            if funded is None:
                continue
            fm = firms.get(key)
            if fm is None:
                meta = companies_meta.get(row["investor_permalink"], {})
                fm = {
                    "id": uuid.uuid4(),
                    "slug": _unique(
                        _slug_from_permalink(row["investor_permalink"], row["investor_name"])
                    ),
                    "name": row["investor_name"] or key,
                    "type": investor_type_for(row["investor_name"]),
                    "country": iso2(row["investor_country_code"]),
                    "region": row["investor_region"] or None,
                    "city": row["investor_city"] or None,
                    "website": (meta.get("homepage_url") or None),
                    "founded": _year(meta.get("founded_at")),
                }
                firms[key] = fm
                if row["investor_permalink"]:
                    firm_by_permalink[row["investor_permalink"]] = fm
            comp = get_company(
                row["company_permalink"],
                row["company_name"],
                row["company_category_list"],
                row["company_country_code"],
            )
            stage = stage_for(row["funding_round_type"], row["funding_round_code"])
            rp = row["funding_round_permalink"]
            r = rounds.get(rp)
            if r is None:
                r = {
                    "id": uuid.uuid4(),
                    "company_id": comp["id"],
                    "stage": stage,
                    "date": funded,
                    "size": _dec(row["raised_amount_usd"]),
                }
                rounds[rp] = r
            deals.append(
                {
                    "firm_id": fm["id"],
                    "company_id": comp["id"],
                    "round_id": r["id"],
                    "stage": stage,
                    "date": funded,
                    # Lead proxy: sole investor in the round led it (open data lacks lead/follow).
                    "is_lead": round_investors.get(rp, 0) == 1,
                    # Check proxy: round size pro-rated by # investors (no per-investor checks in data).
                    "check_amount": (
                        r["size"] / round_investors[rp]
                        if r["size"] is not None and round_investors.get(rp)
                        else None
                    ),
                }
            )

    # Derive is_new: a firm's earliest deal into a given company is NEW, the rest follow-on.
    earliest: dict[tuple, date] = {}
    for d in deals:
        k = (d["firm_id"], d["company_id"])
        if k not in earliest or d["date"] < earliest[k]:
            earliest[k] = d["date"]
    marked_new: set[tuple] = set()
    for d in deals:
        k = (d["firm_id"], d["company_id"])
        d["is_new"] = d["date"] == earliest[k] and k not in marked_new
        if d["is_new"]:
            marked_new.add(k)

    # Acquisitions where the acquirer is one of our selected firms.
    acquisitions: list[tuple] = []
    acquirer_firm_ids: set = set()
    with open(acq_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fm = firm_by_permalink.get(row["acquirer_permalink"])
            if fm is None:
                continue
            acquired = _parse_date(row["acquired_at"])
            if acquired is None:
                continue
            target = get_company(
                row["company_permalink"],
                row["company_name"],
                row["company_category_list"],
                row["company_country_code"],
            )
            acquisitions.append(
                (uuid.uuid4(), fm["id"], target["id"], _dec(row["price_amount"]), acquired)
            )
            acquirer_firm_ids.add(fm["id"])

    # Bulk load.
    await conn.copy_records_to_table(
        "firm",
        records=[
            (
                f["id"],
                f["slug"],
                f["name"],
                f["type"],
                f["country"],
                f["region"],
                f["city"],
                f["website"],
                f["founded"],
            )
            for f in firms.values()
        ],
        columns=[
            "id",
            "slug",
            "name",
            "investor_type",
            "hq_country",
            "hq_region",
            "hq_city",
            "website",
            "founded_year",
        ],
    )
    # One nominal "investing" fund per firm — Crunchbase has no fund data, but an investor actively
    # doing deals has an active fund; this lets the Active-Firm gate work as designed (ADR 0008).
    await conn.copy_records_to_table(
        "fund",
        records=[
            (uuid.uuid4(), f["id"], f["name"] + " Fund", f["founded"], "investing")
            for f in firms.values()
        ],
        columns=["id", "firm_id", "name", "vintage_year", "status"],
    )
    roles = [(f["id"], "direct_investor") for f in firms.values()]
    roles += [(fid, "strategic_acquirer") for fid in acquirer_firm_ids]
    await conn.copy_records_to_table("capital_role", records=roles, columns=["firm_id", "role"])
    if acquirer_firm_ids:
        await conn.copy_records_to_table(
            "firm_role_acquirer",
            records=[(fid, "strategic") for fid in acquirer_firm_ids],
            columns=["firm_id", "buyer_kind"],
        )
    await conn.copy_records_to_table(
        "company",
        records=[(c["id"], c["slug"], c["name"], c["country"]) for c in companies.values()],
        columns=["id", "slug", "name", "hq_country"],
    )
    await conn.copy_records_to_table(
        "company_sector", records=company_sectors, columns=["company_id", "sector_id", "rank"]
    )
    await conn.copy_records_to_table(
        "funding_round",
        records=[
            (r["id"], r["company_id"], r["stage"], r["date"], r["size"]) for r in rounds.values()
        ],
        columns=["id", "company_id", "stage_slug", "announced_at", "round_size"],
    )
    await conn.copy_records_to_table(
        "deal",
        records=[
            (
                uuid.uuid4(),
                d["firm_id"],
                d["company_id"],
                d["round_id"],
                d["stage"],
                d["check_amount"],
                d["is_new"],
                d["is_lead"],
                d["date"],
            )
            for d in deals
        ],
        columns=[
            "id",
            "firm_id",
            "company_id",
            "round_id",
            "stage_slug",
            "check_amount",
            "is_new",
            "is_lead",
            "announced_at",
        ],
    )
    if acquisitions:
        await conn.copy_records_to_table(
            "acquisition",
            records=[(a[0], a[1], a[2], a[3], a[4]) for a in acquisitions],
            columns=["id", "acquirer_firm_id", "target_company_id", "ev_amount", "announced_at"],
        )

    return {
        "firms": len(firms),
        "companies": len(companies),
        "rounds": len(rounds),
        "deals": len(deals),
        "acquisitions": len(acquisitions),
    }
