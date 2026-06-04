-- Extensions + canonical reference data (stage ladder, sector taxonomy shell, thesis dimensions).

CREATE EXTENSION IF NOT EXISTS vector;

-- Canonical investment-stage ladder. sort_order enables range semantics (e.g. "Series B+").
CREATE TABLE stage (
    slug        text PRIMARY KEY,
    label       text NOT NULL,
    sort_order  int  NOT NULL UNIQUE
);

INSERT INTO stage (slug, label, sort_order) VALUES
    ('pre_seed',      'Pre-Seed',        10),
    ('seed',          'Seed',            20),
    ('series_a',      'Series A',        30),
    ('series_b',      'Series B',        40),
    ('series_c',      'Series C',        50),
    ('series_d_plus', 'Series D+',       60),
    ('growth',        'Growth',          70),
    ('late_stage',    'Late Stage',      80),
    ('public',        'Public',          90);

-- The single canonical startup-native sector taxonomy (ADR 0003). Multi-label, hierarchical
-- (groups have parent_id NULL; leaf sectors point to their group). Populated from
-- cadence/taxonomy/sectors.json by the taxonomy loader, kept here so FKs resolve.
CREATE TABLE sector (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        text UNIQUE NOT NULL,
    name        text NOT NULL,
    parent_id   uuid REFERENCES sector(id) ON DELETE CASCADE,
    aliases     text[] NOT NULL DEFAULT '{}',
    sort_order  int NOT NULL DEFAULT 0
);
CREATE INDEX idx_sector_parent ON sector(parent_id);

-- Controlled, filterable thesis dimensions (ADR: only deal-derived structured thesis filters).
CREATE TABLE thesis_tag (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        text UNIQUE NOT NULL,
    name        text NOT NULL,
    dimension   text NOT NULL CHECK (dimension IN (
        'business_model', 'ownership_target', 'technical_risk',
        'go_to_market', 'capital_intensity'))
);
