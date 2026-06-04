"""Build the deterministic seed universe and ingest it (idempotent: truncates data first).

Requires the sector taxonomy + thesis tags to be loaded first (`make seed-taxonomy`).
"""

import asyncio

import asyncpg

from cadence.cadence.compute import compute_and_store
from cadence.config import get_settings
from cadence.datasource.seed_source import SeedDataSource, SeedDealSource
from cadence.embeddings.build import build_firm_embeddings
from cadence.embeddings.embedder import get_embedder
from cadence.ingest.derive import recompute_all
from cadence.ingest.pipeline import ingest
from cadence.seed.universe import TODAY, build_universe


async def run() -> None:
    universe = build_universe()
    settings = get_settings()
    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        async with conn.transaction():
            # Clear prior data only (sector/stage/thesis_tag/schema_migrations are preserved).
            await conn.execute("TRUNCATE firm, company CASCADE")
            counts = await ingest(conn, SeedDataSource(universe), SeedDealSource(universe))
            await recompute_all(
                conn, activity_window_months=settings.activity_window_months, today=TODAY
            )
            await build_firm_embeddings(conn, get_embedder(settings))
            await compute_and_store(conn, today=TODAY)
    finally:
        await conn.close()

    summary = ", ".join(f"{k}={v}" for k, v in counts.items())
    print(f"seeded: {summary}")
    print(f"ground-truth queries: {len(universe.ground_truth)}")


if __name__ == "__main__":
    asyncio.run(run())
