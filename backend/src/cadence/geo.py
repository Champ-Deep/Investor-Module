"""Normalize country names/codes to the 2-letter ISO codes stored on firms.

The LLM (and users) may type "United States", "USA", or "US"; the data store uses ISO-2. This keeps
the country filter from silently matching nothing.
"""

from __future__ import annotations

_COUNTRY_TO_ISO2 = {
    "us": "US", "usa": "US", "u.s.": "US", "u.s.a.": "US", "united states": "US",
    "united states of america": "US", "america": "US",
    "uk": "GB", "u.k.": "GB", "gb": "GB", "united kingdom": "GB", "britain": "GB",
    "great britain": "GB", "england": "GB",
    "canada": "CA", "can": "CA",
    "germany": "DE", "deu": "DE",
    "france": "FR", "fra": "FR",
    "india": "IN", "ind": "IN",
    "china": "CN", "chn": "CN",
    "israel": "IL", "isr": "IL",
    "singapore": "SG", "sgp": "SG",
    "australia": "AU", "aus": "AU",
    "netherlands": "NL", "nld": "NL",
    "sweden": "SE", "spain": "ES", "italy": "IT", "switzerland": "CH", "ireland": "IE",
    "japan": "JP", "south korea": "KR", "korea": "KR", "brazil": "BR", "hong kong": "HK",
    "finland": "FI", "denmark": "DK", "norway": "NO", "belgium": "BE", "austria": "AT",
    "poland": "PL", "new zealand": "NZ", "mexico": "MX", "south africa": "ZA",
    "united arab emirates": "AE", "uae": "AE", "turkey": "TR", "indonesia": "ID",
    "russia": "RU", "ukraine": "UA", "portugal": "PT", "taiwan": "TW", "estonia": "EE",
}


def normalize_country(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return v
    iso = _COUNTRY_TO_ISO2.get(v.lower())
    if iso:
        return iso
    if len(v) == 2:
        return v.upper()
    return v


def normalize_countries(values: list[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        n = normalize_country(v)
        if n and n not in out:
            out.append(n)
    return out
