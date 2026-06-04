-- Derived/materialized intelligence. Populated by the ingest pipeline (M3/M5/M6); recomputed
-- on refresh. Created here so the schema is complete and reviewable.

-- Behavioral sector signature: recency-weighted aggregation of a firm's NEW-deal sectors (ADR 0003).
-- last_deal_at per sector lets the ranker apply recency decay (demote stale-in-sector, never exclude).
CREATE TABLE firm_sector_profile (
    firm_id        uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    sector_id      uuid NOT NULL REFERENCES sector(id) ON DELETE CASCADE,
    weight         numeric(8,6) NOT NULL,
    new_deal_count int NOT NULL DEFAULT 0,
    last_deal_at   date,
    PRIMARY KEY (firm_id, sector_id)
);
CREATE INDEX idx_fsp_sector ON firm_sector_profile(sector_id);

-- Per-stage check-size distribution from NEW deals. The check-size filter operates within a stage.
CREATE TABLE firm_check_size (
    firm_id       uuid NOT NULL REFERENCES firm(id) ON DELETE CASCADE,
    stage_slug    text NOT NULL REFERENCES stage(slug),
    min_amount    numeric(20,2),
    median_amount numeric(20,2),
    max_amount    numeric(20,2),
    deal_count    int NOT NULL DEFAULT 0,
    PRIMARY KEY (firm_id, stage_slug)
);

-- Activity + Active-Firm gate. is_active = qualifying deal in window AND an open/investing fund.
CREATE TABLE firm_activity (
    firm_id                    uuid PRIMARY KEY REFERENCES firm(id) ON DELETE CASCADE,
    window_months              int NOT NULL,
    new_deal_count             int NOT NULL DEFAULT 0,
    total_deal_count           int NOT NULL DEFAULT 0,
    last_deal_at               date,
    has_open_or_investing_fund boolean NOT NULL DEFAULT false,
    is_active                  boolean NOT NULL DEFAULT false
);
CREATE INDEX idx_firm_activity_active ON firm_activity(is_active);

-- Investment Cadence: calibrated prediction of the Readiness label (ADR 0005). Stores the feature
-- snapshot, the top contributing factors (explainability), and the model version + hit-rate.
CREATE TABLE firm_cadence (
    firm_id            uuid PRIMARY KEY REFERENCES firm(id) ON DELETE CASCADE,
    score              int NOT NULL CHECK (score BETWEEN 0 AND 100),
    model_version      text NOT NULL,
    features           jsonb NOT NULL DEFAULT '{}',
    contributions      jsonb NOT NULL DEFAULT '[]',
    readiness_hit_rate numeric(5,4),
    computed_at        timestamptz NOT NULL DEFAULT now()
);

-- Firm sector/thesis embedding for ranking within the matched set ONLY (ADR 0004). 1536 dims =
-- text-embedding-3-small. No ANN index at MVP scale: exact distance over the filtered set keeps
-- recall exact and never gates retrieval.
CREATE TABLE firm_embedding (
    firm_id     uuid PRIMARY KEY REFERENCES firm(id) ON DELETE CASCADE,
    embedding   vector(1536),
    source_text text,
    embedded_at timestamptz NOT NULL DEFAULT now()
);
