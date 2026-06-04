#!/usr/bin/env bash
# Boot the full Cadence stack for preview: Postgres+pgvector, the FastAPI backend, and the Vite
# frontend (the port the preview watches). Idempotent — reuses anything already running. The Vite
# dev server proxies /api -> the backend, so the preview is self-contained on a single origin.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1. Database (idempotent; reuses the running container if present).
docker compose -f "$ROOT/docker-compose.yml" up -d >/dev/null 2>&1 || true

# 2. Backend on :8123 — start only if not already healthy. Migrate first (idempotent, cheap).
if ! curl -sf http://localhost:8123/health >/dev/null 2>&1; then
  (
    cd "$ROOT/backend" || exit 0
    PYTHONPATH=src .venv/bin/python -m cadence.db.migrate >/dev/null 2>&1 || true
    PYTHONPATH=src .venv/bin/uvicorn cadence.server:app --app-dir src --port 8123 \
      --log-level warning >/tmp/cadence_backend.log 2>&1 &
  )
  for _ in $(seq 1 40); do
    curl -sf http://localhost:8123/health >/dev/null 2>&1 && break
    sleep 0.5
  done
fi

# 3. Frontend (foreground; this is the port the preview watches).
cd "$ROOT/frontend" || exit 1
exec npm run dev -- --port "${PORT:-5173}" --host
