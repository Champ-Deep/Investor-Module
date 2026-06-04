"""Map Crunchbase fields to Cadence's vocabulary: categories -> sector slugs, round type/code ->
stage, investor name -> investor_type. Best-effort over the highest-volume categories (ADR 0008)."""

from __future__ import annotations

# Crunchbase category_list value -> our sector slug (leaf where clear, else group). Lowercased keys.
_CATEGORY_TO_SECTOR_RAW = {
    "Software": "horizontal-saas",
    "SaaS": "horizontal-saas",
    "Enterprise Software": "horizontal-saas",
    "Business Services": "horizontal-saas",
    "Information Technology": "horizontal-saas",
    "Technology": "horizontal-saas",
    "Mobile": "consumer-apps",
    "Apps": "consumer-apps",
    "Android": "consumer-apps",
    "iPhone": "consumer-apps",
    "Consumer Internet": "consumer-apps",
    "Curated Web": "consumer-apps",
    "Internet": "consumer-apps",
    "Messaging": "consumer-apps",
    "Location Based Services": "consumer-apps",
    "Social Media": "consumer-apps",
    "Social Network Media": "consumer-apps",
    "Social Network": "consumer-apps",
    "Biotechnology": "biotech",
    "Pharmaceuticals": "biotech",
    "Life Sciences": "biotech",
    "E-Commerce": "ecommerce-enablement",
    "E-commerce": "ecommerce-enablement",
    "Retail": "ecommerce-enablement",
    "Retail Technology": "ecommerce-enablement",
    "Advertising": "martech-salestech",
    "Ad Targeting": "martech-salestech",
    "Sales and Marketing": "martech-salestech",
    "Marketing Automation": "martech-salestech",
    "CRM": "martech-salestech",
    "Health Care": "healthcare-services",
    "Health Care Information Technology": "digital-health",
    "Health and Wellness": "digital-health",
    "Medical": "medical-devices",
    "Medical Devices": "medical-devices",
    "Diagnostics": "diagnostics",
    "Games": "gaming",
    "Video Games": "gaming",
    "Analytics": "data-infrastructure",
    "Big Data": "data-infrastructure",
    "Big Data Analytics": "data-infrastructure",
    "Database": "data-infrastructure",
    "Predictive Analytics": "data-infrastructure",
    "Artificial Intelligence": "applied-ai",
    "Machine Learning": "ml-platforms",
    "Natural Language Processing": "applied-ai",
    "Finance": "banking-infrastructure",
    "Financial Services": "banking-infrastructure",
    "FinTech": "banking-infrastructure",
    "Banking": "banking-infrastructure",
    "Payments": "payments",
    "Lending": "lending-credit",
    "Credit": "lending-credit",
    "Insurance": "insurtech",
    "Bitcoin": "crypto-web3",
    "Cryptocurrency": "crypto-web3",
    "Blockchain": "crypto-web3",
    "Education": "edtech",
    "EdTech": "edtech",
    "Edutainment": "edtech",
    "Clean Technology": "climate-tech",
    "CleanTech": "climate-tech",
    "Renewable Energy": "clean-energy",
    "Solar": "clean-energy",
    "Energy": "clean-energy",
    "Energy Storage": "energy-storage",
    "Batteries": "energy-storage",
    "Agriculture": "agtech-foodtech",
    "AgTech": "agtech-foodtech",
    "Food and Beverages": "agtech-foodtech",
    "Food Processing": "agtech-foodtech",
    "Manufacturing": "manufacturing-tech",
    "Industrial": "manufacturing-tech",
    "Semiconductors": "manufacturing-tech",
    "3D Printing": "manufacturing-tech",
    "Marketplaces": "marketplaces",
    "Marketplace": "marketplaces",
    "Security": "cybersecurity",
    "Cyber Security": "cybersecurity",
    "Network Security": "cybersecurity",
    "Identity Management": "identity-access",
    "Cloud Computing": "cloud-infrastructure",
    "Cloud Infrastructure": "cloud-infrastructure",
    "Web Hosting": "cloud-infrastructure",
    "Networking": "cloud-infrastructure",
    "Infrastructure": "cloud-infrastructure",
    "Developer Tools": "dev-tools",
    "Developer APIs": "dev-tools",
    "Web Development": "dev-tools",
    "Open Source": "dev-tools",
    "Fashion": "d2c-brands",
    "Apparel": "d2c-brands",
    "Consumer Goods": "d2c-brands",
    "Video": "creator-economy",
    "Music": "creator-economy",
    "Media": "creator-economy",
    "Digital Media": "creator-economy",
    "Content": "creator-economy",
    "Content Creators": "creator-economy",
    "News": "creator-economy",
    "Publishing": "creator-economy",
    "Photography": "creator-economy",
    "Entertainment": "consumer-apps",
    "Real Estate": "proptech",
    "Property Management": "proptech",
    "Construction": "construction-tech",
    "Automotive": "mobility",
    "Transportation": "mobility",
    "Logistics": "supply-chain-logistics",
    "Supply Chain Management": "supply-chain-logistics",
    "Shipping": "supply-chain-logistics",
    "Electric Vehicles": "ev-infrastructure",
    "Autonomous Vehicles": "autonomous-vehicles",
    "Robotics": "robotics-automation",
    "Drones": "robotics-automation",
    "Internet of Things": "robotics-automation",
    "Space Travel": "space-tech",
    "Aerospace": "space-tech",
    "Defense": "defense-tech",
    "Human Resources": "hr-tech",
    "Recruiting": "hr-tech",
    "Collaboration": "collaboration-productivity",
    "Productivity Software": "collaboration-productivity",
    "Travel": "consumer-apps",
    "Hospitality": "consumer-apps",
    "Sports": "consumer-apps",
    "Wearables": "consumer-apps",
    "Mental Health": "mental-health",
}
CATEGORY_TO_SECTOR = {k.lower(): v for k, v in _CATEGORY_TO_SECTOR_RAW.items()}

_VENTURE_CODE_STAGE = {
    "A": "series_a",
    "B": "series_b",
    "C": "series_c",
    "D": "series_d_plus",
    "E": "series_d_plus",
    "F": "series_d_plus",
    "G": "series_d_plus",
    "H": "series_d_plus",
}
_TYPE_STAGE = {
    "seed": "seed",
    "angel": "pre_seed",
    "grant": "pre_seed",
    "non_equity_assistance": "pre_seed",
    "convertible_note": "seed",
    "equity_crowdfunding": "seed",
    "product_crowdfunding": "seed",
    "crowdfunding": "seed",
    "private_equity": "growth",
    "debt_financing": "late_stage",
    "secondary_market": "late_stage",
    "post_ipo_equity": "public",
    "post_ipo_debt": "public",
}


def sectors_for(category_list: str | None) -> list[str]:
    """Ordered, de-duplicated sector slugs for a Crunchbase pipe-delimited category_list."""
    out: list[str] = []
    for raw in (category_list or "").split("|"):
        slug = CATEGORY_TO_SECTOR.get(raw.strip().lower())
        if slug and slug not in out:
            out.append(slug)
    return out


def stage_for(round_type: str | None, round_code: str | None) -> str:
    t = (round_type or "").strip().lower()
    if t == "venture":
        return _VENTURE_CODE_STAGE.get((round_code or "").strip().upper(), "series_a")
    return _TYPE_STAGE.get(t, "series_a")


# Crunchbase uses ISO-3 country codes; the app/seed/parser use 2-letter. Normalize the common ones.
_ISO3_TO_ISO2 = {
    "USA": "US", "GBR": "GB", "CAN": "CA", "DEU": "DE", "FRA": "FR", "IND": "IN", "CHN": "CN",
    "ISR": "IL", "SGP": "SG", "AUS": "AU", "NLD": "NL", "SWE": "SE", "ESP": "ES", "ITA": "IT",
    "CHE": "CH", "IRL": "IE", "JPN": "JP", "KOR": "KR", "BRA": "BR", "RUS": "RU", "HKG": "HK",
    "FIN": "FI", "DNK": "DK", "NOR": "NO", "BEL": "BE", "AUT": "AT", "POL": "PL", "NZL": "NZ",
    "MEX": "MX", "ZAF": "ZA", "ARE": "AE", "TUR": "TR", "IDN": "ID", "THA": "TH", "MYS": "MY",
    "PHL": "PH", "VNM": "VN", "UKR": "UA", "PRT": "PT", "TWN": "TW", "EST": "EE", "CZE": "CZ",
}


def iso2(code: str | None) -> str | None:
    c = (code or "").strip().upper()
    return _ISO3_TO_ISO2.get(c, c or None)


def investor_type_for(name: str | None) -> str:
    n = (name or "").lower()
    if any(w in n for w in ("accelerator", "y combinator", "techstars", "incubator", "startup")):
        return "accelerator"
    if "angel" in n:
        return "angel"
    if any(w in n for w in ("private equity", "buyout", "capital partners", "equity partners")):
        return "pe"
    if any(w in n for w in ("bank", "sachs", "morgan")):
        return "bank"
    if any(w in n for w in ("ventures", "capital", "partners", "fund", "vc", " vp", "investors")):
        return "vc"
    return "vc"
