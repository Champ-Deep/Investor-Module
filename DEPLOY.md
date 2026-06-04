# Deploying Cadence to Railway

One **app service** (FastAPI serves the API under `/api` **and** the built SPA at `/`) plus one
**pgvector Postgres**. The Docker image builds the frontend + backend; on boot `scripts/start.sh`
migrates and seeds-if-empty, then serves on `$PORT`. Config: `railway.toml` + `Dockerfile` (root).

## Prerequisites
- Railway CLI (you have 4.30.4). No git repo needed — `railway up` uploads this directory.

## 1 · Log in + create the project
```bash
cd "Investor Platform (Cadence)"
railway login            # opens a browser
railway init             # create a new project, e.g. "cadence"
```

## 2 · Add a pgvector Postgres
Dashboard → project → **New → Database → Add PostgreSQL**. Cadence needs the `vector` extension;
the migration runs `CREATE EXTENSION IF NOT EXISTS vector`. Railway's Postgres image ships pgvector,
so this works. If that migration ever errors with *"extension vector is not available"*, instead add
the **pgvector** template (New → Template → search "pgvector") and use that DB.

## 3 · Set the app service variables
Dashboard → **app service → Variables**:

| Variable | Value | Why |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | reference the Postgres service (asyncpg-ready `postgresql://`) |
| `OPENROUTER_API_KEY` | `sk-or-…` | **turns on LLM query parsing** |
| `LLM_MODEL` | `openai/gpt-4o-mini` | optional (default) |
| `CONTACT_SLA_DAYS` | `180` | optional |

LakeB2B is optional — set `LAKEB2B_API_KEY` + `LAKEB2B_BASE_URL` + `DATA_SOURCE=lakeb2b` only once you
have the contract. **Do not set `PORT`** — Railway injects it.

## 4 · Deploy
```bash
railway up               # uploads, builds the Dockerfile, runs start.sh (migrate + seed), serves
```

## 5 · Public domain
Dashboard → app service → **Settings → Networking → Generate Domain** → `https://<service>.up.railway.app`

## 6 · Test (live)
```bash
curl https://<domain>/api/health     # {"status":"ok","db":true}
curl https://<domain>/api/status     # "llm_parse":"openrouter"  <- confirms the key took effect
```
Then open `https://<domain>/` → the header badge should read green **`LLM · openai/gpt-4o-mini`**, and
a search ("Series B vertical SaaS leads, $15M–$25M, US, led in last 6 months") should return ranked firms.

## Notes
- Healthcheck is `/api/health` (liveness only — returns 200 even if the DB is briefly down).
- First deploy seeds ~115 firms; restarts skip seeding (data persists in the Postgres volume).
- LLM parse errors fall back to the heuristic parser — search never breaks.
