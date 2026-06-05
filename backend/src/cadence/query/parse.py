"""Compile a natural-language query into editable structured filters (ADR 0004).

LLM-extracted content becomes editable hard predicates the user can see and correct; it is never
itself a filter input. Uses an LLM via OpenRouter (OpenAI-compatible structured outputs) when
OPENROUTER_API_KEY is set, with a heuristic offline fallback so the endpoint degrades gracefully
without a key.
"""

from __future__ import annotations

import re

from cadence.config import Settings
from cadence.models.query import ParsedQuery, QueryFilters

_SYSTEM = (
    "You compile an investor-search query into structured filters for the Cadence platform. "
    "Only set hard predicates the user explicitly stated. Put fuzzy sector/thesis language in "
    "soft_sectors (known sector slugs) and soft_text (the verbatim phrase). Do not invent "
    "constraints. Stages: pre_seed, seed, series_a, series_b, series_c, series_d_plus, growth, "
    "late_stage, public. Investor types include vc, angel, pe, growth_equity, family_office, "
    "corporate_venture, pension, endowment, fund_of_funds, sovereign_wealth, solo_gp. Capital "
    "roles: direct_investor, lp_allocator, strategic_acquirer. Amounts are USD (e.g. 15000000). "
    "Countries (hq_countries, mandate_geos, lp_base_geos) use 2-letter ISO codes: US, GB, DE, IN, IL."
)

_STAGES = {
    "pre-seed": "pre_seed",
    "preseed": "pre_seed",
    "pre seed": "pre_seed",
    "seed": "seed",
    "series a": "series_a",
    "series b": "series_b",
    "series c": "series_c",
    "series d": "series_d_plus",
    "growth": "growth",
}


def parse_query(text: str, settings: Settings) -> ParsedQuery:
    if settings.openrouter_api_key:
        try:
            return _parse_llm(text, settings)
        except Exception:
            pass  # any LLM/transport error falls back to the heuristic — never blocks the user
    return _parse_heuristic(text)


def _parse_llm(text: str, settings: Settings) -> ParsedQuery:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        default_headers={"X-Title": "Cadence"},
    )
    completion = client.chat.completions.parse(
        model=settings.llm_model,
        messages=[{"role": "system", "content": _SYSTEM}, {"role": "user", "content": text}],
        response_format=ParsedQuery,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        return _parse_heuristic(text)
    parsed.explanation = (
        f"Parsed by {settings.llm_model} via OpenRouter — review and edit the filters below."
    )
    return parsed


def _parse_heuristic(text: str) -> ParsedQuery:
    t = text.lower()
    f = QueryFilters(soft_text=text)
    for phrase, slug in _STAGES.items():
        if phrase in t and slug not in f.stages:
            f.stages.append(slug)
    if "lead" in t:
        f.lead_only = True
    if re.search(r"\bu\.?s\.?\b|united states|america", t):
        f.hq_countries = ["US"]
    m = re.search(r"\$?\s*(\d+)\s*m[a-z]*\s*(?:to|-|–|and)\s*\$?\s*(\d+)\s*m", t)
    if m:
        f.check_min = float(m.group(1)) * 1_000_000
        f.check_max = float(m.group(2)) * 1_000_000
    if any(w in t for w in ("pension", "endowment", "limited partner", " lp ", "allocat")):
        f.capital_roles.append("lp_allocator")
    if any(w in t for w in ("acquir", "buyer", "m&a", "strategic")):
        f.capital_roles.append("strategic_acquirer")
    return ParsedQuery(filters=f, explanation="Heuristic parse (no LLM); edit filters.")
