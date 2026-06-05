"""The editable structured filters a query compiles into, and a search result row.

Hard predicates (exact pass/fail) live here and filter the full universe. Sector/thesis *fit*
is carried as soft signals (soft_sectors / soft_text) used only to RANK within the matched set
(ADR 0004) — they are never hard filters.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class QueryFilters(BaseModel):
    # identity / role / geography
    investor_types: list[str] = []
    capital_roles: list[str] = []
    hq_countries: list[str] = []
    mandate_geos: list[str] = []
    lp_base_geos: list[str] = []

    # behavioral deal predicates (stage + check operate together, so check is per-stage)
    stages: list[str] = []
    check_min: float | None = None
    check_max: float | None = None
    new_only: bool = True
    lead_only: bool = False
    led_within_months: int | None = None

    # firm numerics
    gp_count_max: int | None = None
    aum_min: float | None = None
    aum_max: float | None = None
    dry_powder_min: float | None = None
    fund_size_min: float | None = None
    fund_size_max: float | None = None
    min_new_deals_window: int | None = None

    # thesis (deal-derived, filterable)
    thesis_tags: list[str] = []

    # acquirer predicates
    acq_buyer_kind: str | None = None
    acq_platform: bool = False
    ebitda_min: float | None = None
    ebitda_max: float | None = None
    acq_sector: str | None = None
    acq_min_count: int | None = None
    acq_within_months: int | None = None
    ev_min: float | None = None
    ev_max: float | None = None

    # LP predicates
    asset_class: str | None = None
    allocation_min_pct: float | None = None
    committed_within_months: int | None = None
    committed_first_time_only: bool = False

    # contact
    require_verified_contact: bool = False

    # gate + soft signals (soft_* are ranking inputs only, never hard filters)
    include_inactive: bool = False
    soft_sectors: list[str] = []
    soft_text: str | None = None


class SearchResultFirm(BaseModel):
    id: str
    slug: str
    name: str
    investor_type: str
    hq_country: str | None = None
    is_active: bool = False
    cadence_score: int | None = None
    rank_score: float | None = None
    last_deal_at: date | None = None


class ParsedQuery(BaseModel):
    """A natural-language query compiled into editable structured filters (ADR 0004)."""

    filters: QueryFilters
    explanation: str = ""
