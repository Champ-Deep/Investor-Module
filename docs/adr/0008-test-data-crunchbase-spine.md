# Test/demo data: Crunchbase-2015 behavioral spine (+ optional OpenVC overlay)

To test Cadence on real investor data we ingest the open Crunchbase October-2015 CSV export
(`notpeter/crunchbase-data`, CC BY-NC) behind the existing DataSource seam (ADR 0006):
`investments.csv` → firms + deals + funding rounds, `companies.csv` → company metadata + sectors,
`acquisitions.csv` → acquisitions. Investor names and their deals are already linked in the export,
so the behavioral engine (sector profile, deal velocity, per-stage activity, Active-Firm gate,
Investment Cadence) runs on real data with no internal entity resolution. OpenVC is an optional,
additive overlay (current website/stage/check/thesis), matched by normalized firm name.

Why: it is the only freely fetchable, relationally-linked open investor+deal dataset. Stated-only
directories (OpenVC alone) cannot exercise the behavioral differentiators that are the product's
thesis. Selected via `DATA_SOURCE=crunchbase`; the synthetic seed remains the default and the
regression fixture.

Limitations (surfaced honestly in-app): per-investor check size is not in the data, so it is
approximated as the round size pro-rated by the round's investor count (a sole investor/lead gets
the full round); lead/follow is not in the data either, so lead is approximated (the sole investor
in a round is treated as the lead); the snapshot is 2015, so the activity
"today" is anchored to 2015-12-31; the data is CC BY-NC — test/demo only, attributed in the UI,
never resold; Crunchbase categories are mapped best-effort to our startup-native taxonomy; and the
export has no people, so contacts/verification are empty for real-data firms — verified contacts
remain the LakeB2B advantage demonstrated by the synthetic seed. Status: accepted.
