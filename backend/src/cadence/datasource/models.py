"""Typed records the adapters return (the seam's contract). Mapped into the schema by ingest.

These intentionally mirror the LakeB2B-shaped identity/contact/firmographic payload plus the
separate deal/portfolio payload. The seed adapters and the (future) live LakeB2B adapter both
produce these, so swapping the source changes nothing downstream (ADR 0006).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class RawContact(BaseModel):
    kind: str  # email | phone
    value: str
    deliverability_status: str = "unknown"  # deliverable | catch_all | undeliverable | unknown
    deliverability_checked_at: datetime | None = None


class RawPartner(BaseModel):
    name: str
    title: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    sector_lead_slugs: list[str] = []
    stage_focus: list[str] = []
    role_currency_status: str = "unknown"  # current | stale | unknown
    role_currency_checked_at: datetime | None = None
    contacts: list[RawContact] = []


class RawFund(BaseModel):
    name: str
    vintage_year: int | None = None
    size: float | None = None
    status: str  # open | investing | wound_down
    dry_powder: float | None = None


class RawLpAllocation(BaseModel):
    asset_class: str
    pct: float


class RawLpCommitment(BaseModel):
    target_gp_name: str
    first_time_fund: bool = False
    amount: float | None = None
    committed_at: date


class RawRoleDirect(BaseModel):
    takes_board_seat: bool | None = None
    co_invest_friendly: bool | None = None


class RawRoleLp(BaseModel):
    ticket_min: float | None = None
    ticket_max: float | None = None
    allocations: list[RawLpAllocation] = []
    commitments: list[RawLpCommitment] = []


class RawRoleAcquirer(BaseModel):
    buyer_kind: str  # strategic | financial_pe
    platform_or_addon: str | None = None
    ebitda_min: float | None = None
    ebitda_max: float | None = None
    revenue_min: float | None = None
    revenue_max: float | None = None


class RawFirm(BaseModel):
    slug: str
    name: str
    investor_type: str
    hq_country: str | None = None
    hq_region: str | None = None
    hq_city: str | None = None
    website: str | None = None
    founded_year: int | None = None
    gp_count: int | None = None
    aum: float | None = None
    dry_powder: float | None = None
    description: str | None = None
    roles: list[str] = []
    mandate_geos: list[str] = []
    lp_base_geos: list[str] = []
    thesis_tag_slugs: list[str] = []
    thesis_narrative: str | None = None
    funds: list[RawFund] = []
    partners: list[RawPartner] = []
    role_direct: RawRoleDirect | None = None
    role_lp: RawRoleLp | None = None
    role_acquirer: RawRoleAcquirer | None = None


class RawCompany(BaseModel):
    slug: str
    name: str
    description: str | None = None
    hq_country: str | None = None
    primary_sectors: list[str] = []
    secondary_sectors: list[str] = []


class RawRound(BaseModel):
    ref: str  # generator-local id used to link deals into the same round (co-investment)
    company_slug: str
    stage: str
    announced_at: date
    round_size: float | None = None


class RawDeal(BaseModel):
    firm_slug: str
    company_slug: str
    round_ref: str | None = None
    stage: str
    check_amount: float | None = None
    is_new: bool
    is_lead: bool
    announced_at: date


class RawAcquisition(BaseModel):
    acquirer_firm_slug: str | None
    target_company_slug: str
    ev_amount: float | None = None
    revenue_multiple: float | None = None
    ebitda_at_deal: float | None = None
    advisor: str | None = None
    deal_kind: str | None = None  # platform | addon
    announced_at: date
