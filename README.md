# Investor-Module

**Cadence** — the investor intelligence search platform from Champions Infometrics, powered by the LakeB2B Data API.

Founders and bankers go from a natural-language need to a ranked, exportable list of capital sources, each with verified partner contacts and an Investment Cadence score.

[![Stack](https://img.shields.io/badge/stack-FastAPI%20%C2%B7%20Postgres%20%C2%B7%20Django-informational?style=flat-square)](#tech-stack)

---

## The domain, in four words

Most of the value here is in getting the vocabulary right, so it is worth stating up front. The full glossary lives in [CONTEXT.md](./CONTEXT.md) and its definitions are treated as law, not suggestion.

| Term | What it is |
|---|---|
| **Firm** | An institutional source of capital. The atomic searchable entity. One result row equals one Firm. |
| **Partner** | A named decision-maker at a Firm. The person you actually contact. Partners nest inside a Firm. |
| **Investment Cadence** | A 0–100 firm-level score predicting the Readiness label ("makes a new deal within 90 days"). Attaches to a Firm, never to a person. |
| **Verified** | Two independently dated signals: deliverability *and* role currency, both inside SLA. A partial state is shown honestly rather than rounded up. |

"Investor" is deliberately **not** a search-unit term, because it is ambiguous between a Firm and a Partner. When precision matters, say Firm or Partner.

---

## Core design decisions

These are settled. They are recorded in full in `docs/adr/0001..0007`, and if code ever conflicts with an ADR, the ADR wins.

- **Filters first, semantics second.** Hard predicates filter the full universe for complete recall; semantic similarity only *ranks* within the matched set. Embeddings never retrieve a candidate set ahead of filtering. (ADR 0004)
- **Editable structured filters.** A natural-language query compiles into filters the user can see and correct. LLM-extracted content is display-only and never a filter input. (ADR 0004)
- **Behavioural over stated.** A Deal is a firm's participation in a funding event, tagged new or follow-on and lead or follow. Appetite weights new deals.
- **Recency decays, it never excludes.** A stale record is demoted, not filtered out.
- **Cadence is explainable.** A calibrated prediction that always exposes its top contributing factors, currently a cold-start heuristic and swappable for a learned model. (ADR 0005, 0007)

---

## Tech stack

FastAPI · PostgreSQL · SQLAlchemy · Alembic · Pydantic · Railway (deploy) · Docker.

Data sources are pluggable behind a `datasource` interface, currently the LakeB2B Data API, a Crunchbase importer, and a seed source.

---

## Layout

```
backend/src/cadence/
  api/routes/     firms, search, freshness, health
  cadence/        compute, features, label, model   <- the scoring engine
  datasource/     base, factory, lakeb2b_source, crunchbase, seed
  db/             migrations
  config.py
```

`docs/adr/` holds the numbered decision records. Read them before changing the scoring or the search path.

---

## Local development

**Requirements:** Python 3.11+, Postgres, Docker (optional).

```bash
git clone git@github.com:Champ-Deep/Investor-Module.git
cd Investor-Module
cd backend
cp .env.example .env      # DATABASE_URL and friends
make install
make migrate
make run
```

API on `http://localhost:8000`, docs at `/docs`. See [DEPLOY.md](./DEPLOY.md) for the Railway deployment.

---

## Read these first

| File | Why |
|---|---|
| [CONTEXT.md](./CONTEXT.md) | The domain glossary. Definitions override loose wording. |
| [CLAUDE.md](./CLAUDE.md) | Hard invariants, carried into every change. |
| [DEPLOY.md](./DEPLOY.md) | Deployment runbook. |
| `docs/adr/` | Settled architecture decisions. |

---

## Status

Phase 1 MVP in progress, for the capital-raise founder persona. No authentication in v0; Clerk is planned.
