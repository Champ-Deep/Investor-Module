"""Apply ordered SQL migrations from db/migrations/ exactly once each."""

import asyncio
import pathlib

import asyncpg

from cadence.config import get_settings

MIGRATIONS_DIR = pathlib.Path(__file__).parent / "migrations"


async def run() -> None:
    settings = get_settings()
    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "filename text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        rows = await conn.fetch("SELECT filename FROM schema_migrations")
        applied = {r["filename"] for r in rows}
        files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for f in files:
            if f.name in applied:
                continue
            async with conn.transaction():
                await conn.execute(f.read_text())
                await conn.execute("INSERT INTO schema_migrations(filename) VALUES($1)", f.name)
            print(f"applied {f.name}")
        print("migrations up to date")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run())
