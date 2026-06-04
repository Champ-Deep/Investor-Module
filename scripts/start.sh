#!/usr/bin/env sh
# Container boot: wait for the DB + migrate (idempotent), seed only if empty, then exec uvicorn.
# $PORT is provided by Railway; expanded here because this runs in a shell (not exec-form args).
set -u

echo "[start] applying migrations (retrying until the DB is reachable)..."
i=0
until python -m cadence.db.migrate; do
  i=$((i + 1))
  if [ "$i" -ge 20 ]; then
    echo "[start] migrate still failing after $i tries — launching anyway so /api/health comes up"
    break
  fi
  echo "[start] DB not ready, retry $i/20 in 3s..."
  sleep 3
done

NEED_SEED=$(python - <<'PY'
import asyncio
import asyncpg
from cadence.config import get_settings


async def main():
    try:
        conn = await asyncpg.connect(dsn=get_settings().database_url)
        n = await conn.fetchval("SELECT count(*) FROM firm")
        await conn.close()
    except Exception:
        n = -1
    print("yes" if n == 0 else "no")


asyncio.run(main())
PY
)

if [ "$NEED_SEED" = "yes" ]; then
  echo "[start] empty DB — loading taxonomy + ingesting (DATA_SOURCE=${DATA_SOURCE:-seed})..."
  python -m cadence.taxonomy.load && python -m cadence.ingest.run || echo "[start] seed failed; continuing"
else
  echo "[start] data already present — skipping seed"
fi

echo "[start] launching uvicorn on 0.0.0.0:${PORT:-8000}"
exec uvicorn cadence.server:app --host 0.0.0.0 --port "${PORT:-8000}"
