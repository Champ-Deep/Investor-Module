-- Partners (contactable humans nested under a firm), companies, funding rounds, deals,
-- acquisitions, and thesis data.

CREATE TABLE partner (
    id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id                  uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    name                     text NOT NULL,
    title                    text,
    location                 text,
    linkedin_url             text,
    -- Role currency = signal #2 of the two-signal Verified standard (ADR 0002). Its own date.
    role_currency_status     text NOT NULL DEFAULT 'unknown'
                                  CHECK (role_currency_status IN ('current', 'stale', 'unknown')),
    role_currency_checked_at timestamptz,
    last_updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_partner_firm ON partner(firm_id);

CREATE TABLE partner_sector_lead (
    partner_id uuid NOT NULL REFERENCES partner(id) ON DELETE CASCADE,
    sector_id  uuid NOT NULL REFERENCES sector(id) ON DELETE CASCADE,
    PRIMARY KEY (partner_id, sector_id)
);

CREATE TABLE partner_stage_focus (
    partner_id uuid NOT NULL REFERENCES partner(id) ON DELETE CASCADE,
    stage_slug text NOT NULL REFERENCES stage(slug),
    PRIMARY KEY (partner_id, stage_slug)
);

-- Contact channel carries Deliverability = signal #1 (ADR 0002). catch_all is NOT a pass.
CREATE TABLE contact_channel (
    id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id                uuid NOT NULL REFERENCES partner(id) ON DELETE CASCADE,
    kind                      text NOT NULL CHECK (kind IN ('email', 'phone')),
    value                     text NOT NULL,
    deliverability_status     text NOT NULL DEFAULT 'unknown'
                                  CHECK (deliverability_status IN
                                      ('deliverable', 'catch_all', 'undeliverable', 'unknown')),
    deliverability_checked_at timestamptz
);
CREATE INDEX idx_contact_partner ON contact_channel(partner_id);

CREATE TABLE company (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        text UNIQUE NOT NULL,
    name        text NOT NULL,
    description text,
    hq_country  text
);

-- Multi-label sector tagging of companies (ADR 0003). Drives the behavioral firm sector profile.
CREATE TABLE company_sector (
    company_id uuid NOT NULL REFERENCES company(id) ON DELETE CASCADE,
    sector_id  uuid NOT NULL REFERENCES sector(id) ON DELETE CASCADE,
    rank       text NOT NULL CHECK (rank IN ('primary', 'secondary')),
    PRIMARY KEY (company_id, sector_id)
);
CREATE INDEX idx_company_sector_sector ON company_sector(sector_id);

-- The company-side funding event. Multiple firms' deals can share one round (co-investment).
CREATE TABLE funding_round (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES company(id) ON DELETE CASCADE,
    stage_slug text NOT NULL REFERENCES stage(slug),
    announced_at date NOT NULL,
    round_size numeric(20,2),
    currency   text NOT NULL DEFAULT 'USD'
);
CREATE INDEX idx_round_company ON funding_round(company_id);

-- A Deal = one firm's participation in a funding event (CONTEXT.md). Tagged new/follow-on
-- and lead/follow. check_amount is the firm's own check (per-stage check size derives from this).
CREATE TABLE deal (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id      uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    company_id   uuid NOT NULL REFERENCES company(id) ON DELETE CASCADE,
    round_id     uuid REFERENCES funding_round(id) ON DELETE SET NULL,
    stage_slug   text NOT NULL REFERENCES stage(slug),
    check_amount numeric(20,2),
    is_new       boolean NOT NULL,   -- new vs follow-on (appetite weights NEW)
    is_lead      boolean NOT NULL,   -- lead vs follow (per-deal, not a fixed firm trait)
    announced_at date NOT NULL
);
CREATE INDEX idx_deal_firm ON deal(firm_id);
CREATE INDEX idx_deal_company ON deal(company_id);
CREATE INDEX idx_deal_round ON deal(round_id);
CREATE INDEX idx_deal_stage ON deal(stage_slug);
CREATE INDEX idx_deal_new ON deal(is_new);
CREATE INDEX idx_deal_announced ON deal(announced_at);

-- An Acquisition = a Strategic Acquirer buying a company outright (CONTEXT.md). Distinct from a
-- Deal: carries EV, multiple, platform/add-on; never tagged new/follow-on or lead/follow.
-- acquirer_firm_id is nullable so M&A-comps rows can reference buyers outside our universe.
CREATE TABLE acquisition (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    acquirer_firm_id  uuid REFERENCES firm(id) ON DELETE SET NULL,
    target_company_id uuid NOT NULL REFERENCES company(id) ON DELETE CASCADE,
    ev_amount         numeric(20,2),  -- enterprise value
    revenue_multiple  numeric(8,2),
    ebitda_at_deal    numeric(20,2),
    advisor           text,
    deal_kind         text CHECK (deal_kind IN ('platform', 'addon')),
    announced_at      date NOT NULL
);
CREATE INDEX idx_acq_acquirer ON acquisition(acquirer_firm_id);
CREATE INDEX idx_acq_target ON acquisition(target_company_id);
CREATE INDEX idx_acq_announced ON acquisition(announced_at);

-- Filterable, deal-derived thesis tags.
CREATE TABLE firm_thesis_tag (
    firm_id uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    tag_id  uuid NOT NULL REFERENCES thesis_tag(id) ON DELETE CASCADE,
    PRIMARY KEY (firm_id, tag_id)
);

-- LLM-summarized, source-cited, READ-ONLY narrative. Never a filter input (ADR 0004).
CREATE TABLE thesis_narrative (
    firm_id      uuid PRIMARY KEY REFERENCES firm(id) ON DELETE CASCADE,
    narrative    text NOT NULL,
    sources      jsonb NOT NULL DEFAULT '[]',
    generated_at timestamptz NOT NULL DEFAULT now()
);
