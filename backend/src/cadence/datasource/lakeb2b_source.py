"""Live LakeB2B adapters.

LakeB2B supplies the identity + verified-contact + firmographic layer (per the LakeStream data
dictionary): people with company, title, verified email, etc. It does NOT supply behavioral
deal/fund data — that stays seeded (or a future DealSource) until a contract exists.

The exact request/response contract is the PRD's #1 open question, so the HTTP paths and the
`_map_*` functions below are an ASSUMED contract. When the real API lands, adjust ONLY this module
(auth, paths, mapping) — ingest/query/scoring/UI are untouched (ADR 0006).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterator

import httpx

from cadence.datasource.base import DeliverabilityResult
from cadence.datasource.models import (
    RawAcquisition,
    RawCompany,
    RawContact,
    RawDeal,
    RawFirm,
    RawPartner,
    RawRound,
)

_FIRMS_PATH = "prospects"  # assumed: paginated people/company enrichment records
_DELIVERABLE = {"valid": "deliverable", "deliverable": "deliverable", "ok": "deliverable"}


def _require(value: str | None, name: str) -> str:
    if not value:
        raise ValueError(f"{name} is required for the live LakeB2B source (set it in .env).")
    return value


class LakeB2BClient:
    def __init__(self, api_key: str | None, base_url: str | None, timeout: float = 30.0) -> None:
        self._base = _require(base_url, "LAKEB2B_BASE_URL").rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {_require(api_key, 'LAKEB2B_API_KEY')}",
            "Accept": "application/json",
        }
        self._timeout = timeout

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = httpx.get(
            f"{self._base}/{path.lstrip('/')}",
            headers=self._headers,
            params=params or {},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def paginate(self, path: str, params: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
        params = dict(params or {})
        cursor: str | None = None
        cap = 50_000
        seen = 0
        while True:
            if cursor:
                params["cursor"] = cursor
            payload = self.get_json(path, params)
            items = payload.get("data") or payload.get("results") or []
            for item in items:
                yield item
                seen += 1
                if seen >= cap:
                    return
            cursor = payload.get("next_cursor") or (payload.get("paging") or {}).get("next")
            if not cursor:
                return


def _contact_from(rec: dict[str, Any]) -> list[RawContact]:
    out: list[RawContact] = []
    email = rec.get("email") or rec.get("email_address")
    if email:
        status = _DELIVERABLE.get(str(rec.get("email_status", "")).lower(), "unknown")
        out.append(RawContact(kind="email", value=email, deliverability_status=status))
    phone = rec.get("phone") or rec.get("direct_dial") or rec.get("mobile")
    if phone:
        out.append(RawContact(kind="phone", value=phone))
    return out


class LakeB2BDataSource:
    """Identity + verified contacts, grouped from LakeB2B people records into firms + partners."""

    def __init__(self, api_key: str | None, base_url: str | None) -> None:
        self._client = LakeB2BClient(api_key, base_url)

    def fetch_firms(self) -> list[RawFirm]:
        firms: dict[str, RawFirm] = {}
        for rec in self._client.paginate(_FIRMS_PATH):
            company = rec.get("company") or rec.get("company_name")
            if not company:
                continue
            slug = str(company).lower().strip().replace(" ", "-")
            firm = firms.get(slug)
            if firm is None:
                firm = RawFirm(
                    slug=slug,
                    name=str(company),
                    investor_type=str(rec.get("investor_type") or "other"),
                    hq_country=rec.get("country"),
                    website=rec.get("website") or rec.get("domain"),
                    roles=["direct_investor"],
                )
                firms[slug] = firm
            name = " ".join(filter(None, [rec.get("first_name"), rec.get("last_name")])).strip()
            if name:
                firm.partners.append(
                    RawPartner(
                        name=name,
                        title=rec.get("job_title") or rec.get("title"),
                        location=rec.get("city") or rec.get("country"),
                        linkedin_url=rec.get("linkedin_url"),
                        contacts=_contact_from(rec),
                    )
                )
        return list(firms.values())

    def fetch_companies(self) -> list[RawCompany]:
        # Operating companies (deal targets) are not part of LakeB2B identity data.
        return []


class LakeB2BDealSource:
    """LakeB2B carries no behavioral deal/fund data; these stay empty until a DealSource exists."""

    def fetch_rounds(self) -> list[RawRound]:
        return []

    def fetch_deals(self) -> list[RawDeal]:
        return []

    def fetch_acquisitions(self) -> list[RawAcquisition]:
        return []


class LakeB2BEmailVerifyProvider:
    """Deliverability via the standalone `lakeb2b-email-verify` package (catch-all aware, ADR 0002).

    Lazy-imported so it is not a hard/CI dependency. Maps the pipeline verdict to our status;
    a catch-all is NEVER reported as deliverable. Any failure degrades to 'unknown'.
    """

    def verify(self, channel_kind: str, value: str) -> DeliverabilityResult:
        now = datetime.now(timezone.utc)
        if channel_kind != "email":
            return DeliverabilityResult(status="unknown", checked_at=now)
        try:
            from lakeb2b_email_verify.pipeline import verify_email  # type: ignore

            result = verify_email(value)
            if getattr(result, "is_catch_all", False) or getattr(result, "catch_all", False):
                status = "catch_all"
            elif getattr(result, "is_deliverable", None) is True:
                status = "deliverable"
            elif getattr(result, "is_deliverable", None) is False:
                status = "undeliverable"
            else:
                status = "unknown"
        except Exception:
            status = "unknown"
        return DeliverabilityResult(status=status, checked_at=now)
