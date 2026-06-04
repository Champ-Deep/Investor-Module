# CLAUDE.md — Cadence (Investor Platform)

Guidance for Claude Code when working in this repo. Read this first, every session.

## What this is
Cadence — an investor-intelligence **search platform** (Champions Infometrics, "powered by the LakeB2B Data API"). Founders/bankers go from a natural-language need to a ranked, exportable list of capital sources, each with verified partner contacts and an Investment Cadence score. We are building the **Phase 1 MVP** for the capital-raise founder persona. No auth in v0 (Clerk later).

## Source of truth (these override loose wording — read them)
- `CONTEXT.md` — the domain glossary. Term definitions are **law**.
- `docs/adr/0001..0007` — settled architecture decisions. If code conflicts with an ADR, the ADR wins — raise it, don't silently deviate.
- `Cadence_Investor_Platform_PRD.docx` (one directory up) — the full PRD. Read with `pandoc`/python if needed.
- Approved build plan: `~/.claude/plans/you-are-building-the-glimmering-engelbart.md`.

## Hard invariants (carry into every change)
- **Firm** is the atomic searchable entity; **Partners** nest under a Firm; **Investment Cadence** attaches to the Firm, never a person. (ADR 0001)
- One Firm record carries multiple **capital-role** facets (Direct Investor / LP-Allocator / Strategic Acquirer), not separate entity types. (ADR 0001)
- **Verified** = TWO independently dated signals: Deliverability (a catch-all server is NOT a pass) AND Role currency, both inside SLA. Otherwise show the partial state honestly. (ADR 0002)
- One canonical **startup-native, multi-label** sector taxonomy (NOT GICS). A Firm's sector profile = the recency-weighted aggregation of its NEW-deal sectors. (ADR 0003)
- **Filters-first**: hard predicates filter the full universe first for complete recall; semantic similarity only RANKS within the matched set. Never use embeddings to retrieve a candidate set ahead of filtering. (ADR 0004)
- NL queries compile into **editable structured filters** the user can see and correct; LLM-extracted content is display-only and never a filter input.
- **Behavioral over stated**: a Deal is a Firm's participation in a funding event, tagged new/follow-on and lead/follow; appetite weights NEW deals. Check size is a per-stage distribution and the filter operates within the selected stage.
- **Investment Cadence** is a calibrated PREDICTION of the Readiness label ("Firm makes a NEW deal within 90 days"), interpretable, always exposing its top contributing factors. Cold-start heuristic now, swappable for a learned model. (ADR 0005, 0007)
- **Active Firm** gates default search (≥1 qualifying deal in the activity window + an open/investing fund). Recency decay DEMOTES, never excludes.

## Tech stack
- **Backend:** Python 3.12, FastAPI + uvicorn, Pydantic v2, Postgres 16 + pgvector, async **raw SQL via asyncpg** (no ORM), OpenAI SDK (embeddings + query parse). ruff + pytest.
- **Frontend:** React 18 + Vite + TypeScript + Tailwind + shadcn/ui + TanStack Query + axios + recharts.
- **Data seam:** the whole app runs against `DataSource`/`DealSource` adapters backed by seeded data; the live LakeB2B API drops in later with no UI/search/scoring change. (ADR 0006)
- **Deliverability** reuses the `lakeb2b-email-verify` package from `../LakeB2B Email Verifier` (catch-all aware, conditional scoring).

## Layout
```
backend/src/cadence/{api,models,db,datasource,ingest,query,taxonomy,cadence,embeddings,export}
backend/{seed,tests}
frontend/src/{features/{search,results,profile,export,freshness},lib,components}
docs/adr   scripts   docker-compose.yml
```

## Commands (Makefile in backend/)
First-time setup (from `backend/`, after `uv venv && uv pip install -e ".[dev]"`):
`make docker-up && make migrate && make seed-taxonomy && make seed && make dev`
The API serves on **:8123**; Postgres+pgvector on **:5436**; the frontend (Vite) on **:5173**.

- `make docker-up` — local Postgres 16 + pgvector (port 5436)
- `make migrate` — apply SQL migrations
- `make seed-taxonomy` — load the sector taxonomy + thesis tags (run before `seed`)
- `make seed` — generate + ingest the seed universe, then recompute derived tables, embeddings, Cadence
- `make derive` / `make embed` / `make cadence` — recompute an individual derived layer
- `make dev` — run the FastAPI app on :8123 (uvicorn, reload)
- `make test` / `make stress` — pytest / the Section-17 stress regression
- `make lint` / `make format` / `make typecheck` — ruff + mypy
- Frontend: `cd frontend && npm install && npm run dev` (Vite on :5173; calls the API on :8123)

## Conventions
- Python 3.12+, Pydantic v2 models for all data structures, raw SQL via asyncpg (queries live in `db/queries/`).
- ruff for lint + format; pytest with asyncio auto mode.
- The **stress-test suite** (PRD Section 17) is the headline regression: recall of planted ground-truth = 100% (filters-first), top-20 relevance ≥ 80%.
- New hard-to-reverse decision → add `docs/adr/<NNN>-<slug>.md`. New/sharpened domain term → update `CONTEXT.md`. Keep both living.
- Verify library APIs via Context7 before using them — don't write framework APIs from memory.
- Simplicity first; no premature abstraction; default to no comments.
