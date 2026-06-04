-- Firm (the atomic searchable entity, ADR 0001) + its capital-role facets + funds.

CREATE TABLE firm (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            text UNIQUE NOT NULL,
    name            text NOT NULL,
    -- Institutional kind (filter #1). Distinct axis from capital_role (deployment mode).
    investor_type   text NOT NULL CHECK (investor_type IN (
        'vc', 'angel', 'pe', 'growth_equity', 'family_office', 'corporate_venture',
        'hedge_fund', 'sovereign_wealth', 'pension', 'endowment', 'foundation',
        'fund_of_funds', 'accelerator', 'solo_gp', 'bank', 'insurance', 'other')),
    hq_country      text,
    hq_region       text,
    hq_city         text,
    website         text,
    founded_year    int,
    gp_count        int,            -- supports "3 GPs or fewer" style predicates
    aum             numeric(20,2),  -- assets under management (placement persona filters)
    dry_powder      numeric(20,2),  -- firm-level deployable capital (Tier 2; appears in stress queries)
    description     text,
    last_updated_at timestamptz NOT NULL DEFAULT now(),
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_firm_investor_type ON firm(investor_type);
CREATE INDEX idx_firm_hq_country ON firm(hq_country);

-- Where a firm actually invests (mandate) and where its capital comes from (lp_base).
-- HQ geography lives on firm; these are the multi-valued geographies.
CREATE TABLE firm_geo (
    firm_id uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    kind    text NOT NULL CHECK (kind IN ('mandate', 'lp_base')),
    value   text NOT NULL,           -- region/country code e.g. US, EU, UK, APAC, MENA
    PRIMARY KEY (firm_id, kind, value)
);
CREATE INDEX idx_firm_geo_value ON firm_geo(kind, value);

-- One firm, multiple capital-role facets (ADR 0001). Membership row = the investor-role filter.
CREATE TABLE capital_role (
    firm_id uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    role    text NOT NULL CHECK (role IN ('direct_investor', 'lp_allocator', 'strategic_acquirer')),
    PRIMARY KEY (firm_id, role)
);
CREATE INDEX idx_capital_role_role ON capital_role(role);

-- Role-specific field sets (each optional 1:1 with firm; only present if the firm has that facet).
CREATE TABLE firm_role_direct (
    firm_id            uuid PRIMARY KEY REFERENCES firm(id) ON DELETE CASCADE,
    lead_ratio         numeric(4,3),   -- derived in M3 from deal.is_lead
    takes_board_seat   boolean,
    co_invest_friendly boolean
);

CREATE TABLE firm_role_lp (
    firm_id    uuid PRIMARY KEY REFERENCES firm(id) ON DELETE CASCADE,
    ticket_min numeric(20,2),          -- ticket size into funds
    ticket_max numeric(20,2)
);

CREATE TABLE lp_allocation (
    firm_id     uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    asset_class text NOT NULL CHECK (asset_class IN (
        'pe', 'vc', 'private_credit', 'real_estate', 'infrastructure',
        'hedge_funds', 'natural_resources', 'public_equity')),
    pct         numeric(5,2) NOT NULL, -- % of portfolio allocated to this asset class
    PRIMARY KEY (firm_id, asset_class)
);

CREATE TABLE lp_commitment (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id         uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    target_gp_name  text NOT NULL,
    first_time_fund boolean NOT NULL DEFAULT false,
    amount          numeric(20,2),
    committed_at    date NOT NULL
);
CREATE INDEX idx_lp_commitment_firm ON lp_commitment(firm_id);

CREATE TABLE firm_role_acquirer (
    firm_id           uuid PRIMARY KEY REFERENCES firm(id) ON DELETE CASCADE,
    buyer_kind        text NOT NULL CHECK (buyer_kind IN ('strategic', 'financial_pe')),
    platform_or_addon text CHECK (platform_or_addon IN ('platform', 'addon', 'both')),
    ebitda_min        numeric(20,2),
    ebitda_max        numeric(20,2),
    revenue_min       numeric(20,2),
    revenue_max       numeric(20,2)
);

CREATE TABLE fund (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id      uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    name         text NOT NULL,
    vintage_year int,
    size         numeric(20,2),       -- sets the upper bound on what they can write
    status       text NOT NULL CHECK (status IN ('open', 'investing', 'wound_down')),
    dry_powder   numeric(20,2)
);
CREATE INDEX idx_fund_firm ON fund(firm_id);
CREATE INDEX idx_fund_status ON fund(status);
