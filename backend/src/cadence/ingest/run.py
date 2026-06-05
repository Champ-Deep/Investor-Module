"""Source-agnostic ingest: pick seed / live LakeB2B / Crunchbase test data via DATA_SOURCE, then
recompute derived tables, embeddings, and Cadence.

  make ingest                          # DATA_SOURCE (default seed)
  DATA_SOURCE=crunchbase make ingest   # real investors + deals from the Crunchbase-2015 cache
  DATA_SOURCE=lakeb2b   make ingest    # live LakeB2B identity/contacts (needs key + base URL)
"""

import asyncio
from datetime import date

import asyncpg

from cadence.cadence.compute import compute_and_store
from cadence.config import SEED_VERSION, get_settings
from cadence.embeddings.build import build_firm_embeddings
from cadence.embeddings.embedder import get_embedder
from cadence.ingest.derive import recompute_all
from cadence.ingest.pipeline import ingest

# The Crunchbase snapshot is from 2015 — anchor the activity window to it so recency/Cadence make
# sense; live/seed sources use the real current date.
CRUNCHBASE_ANCHOR = date(2015, 12, 31)


async def run() -> None:
    settings = get_settings()
    source = settings.active_data_source
    today = CRUNCHBASE_ANCHOR if source == "crunchbase" else date.today()

    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        async with conn.transaction():
            await conn.execute("TRUNCATE firm, company CASCADE")
            if source == "crunchbase":
                from cadence.crunchbase.importer import import_crunchbase

                counts = await import_crunchbase(conn, settings)
            else:
                from cadence.datasource.factory import get_sources

                data_source, deal_source = get_sources(settings)
                counts = await ingest(conn, data_source, deal_source)

            await recompute_all(
                conn, activity_window_months=settings.activity_window_months, today=today
            )
            await build_firm_embeddings(conn, get_embedder(settings))
            await compute_and_store(conn, today=today)
            await conn.execute(
                "INSERT INTO data_meta (id, source, ingested_at) VALUES (1, $1, now()) "
                "ON CONFLICT (id) DO UPDATE SET source = EXCLUDED.source, ingested_at = now()",
                f"{source}@{SEED_VERSION}",
            )
    finally:
        await conn.close()

    summary = ", ".join(f"{k}={v}" for k, v in counts.items())
    print(f"ingested from '{source}' (anchor {today}): {summary}")


if __name__ == "__main__":
    asyncio.run(run())
