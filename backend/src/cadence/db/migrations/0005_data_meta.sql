-- Records which DataSource last populated the store, so the boot script re-seeds automatically
-- when DATA_SOURCE changes (e.g. synthetic seed -> crunchbase) without a manual DB reset.
CREATE TABLE IF NOT EXISTS data_meta (
    id          int PRIMARY KEY DEFAULT 1,
    source      text NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT data_meta_singleton CHECK (id = 1)
);
