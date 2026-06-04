"""Load the canonical sector taxonomy from sectors.json into the sector table (idempotent)."""

import asyncio
import json
import pathlib

import asyncpg

from cadence.config import get_settings

SECTORS_FILE = pathlib.Path(__file__).parent / "sectors.json"
THESIS_FILE = pathlib.Path(__file__).parent / "thesis_tags.json"


async def load() -> int:
    data = json.loads(SECTORS_FILE.read_text())
    settings = get_settings()
    conn = await asyncpg.connect(dsn=settings.database_url)
    count = 0
    try:
        async with conn.transaction():
            for gi, group in enumerate(data["groups"]):
                group_id = await conn.fetchval(
                    """
                    INSERT INTO sector (slug, name, parent_id, aliases, sort_order)
                    VALUES ($1, $2, NULL, $3, $4)
                    ON CONFLICT (slug) DO UPDATE
                      SET name = EXCLUDED.name,
                          aliases = EXCLUDED.aliases,
                          sort_order = EXCLUDED.sort_order
                    RETURNING id
                    """,
                    group["slug"],
                    group["name"],
                    group.get("aliases", []),
                    gi * 100,
                )
                count += 1
                for si, sec in enumerate(group["sectors"]):
                    await conn.execute(
                        """
                        INSERT INTO sector (slug, name, parent_id, aliases, sort_order)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (slug) DO UPDATE
                          SET name = EXCLUDED.name,
                              parent_id = EXCLUDED.parent_id,
                              aliases = EXCLUDED.aliases,
                              sort_order = EXCLUDED.sort_order
                        """,
                        sec["slug"],
                        sec["name"],
                        group_id,
                        sec.get("aliases", []),
                        gi * 100 + si + 1,
                    )
                    count += 1
    finally:
        await conn.close()
    return count


async def load_thesis_tags() -> int:
    data = json.loads(THESIS_FILE.read_text())
    settings = get_settings()
    conn = await asyncpg.connect(dsn=settings.database_url)
    count = 0
    try:
        async with conn.transaction():
            for t in data["tags"]:
                await conn.execute(
                    "INSERT INTO thesis_tag (slug, name, dimension) VALUES ($1, $2, $3) "
                    "ON CONFLICT (slug) DO UPDATE "
                    "  SET name = EXCLUDED.name, dimension = EXCLUDED.dimension",
                    t["slug"],
                    t["name"],
                    t["dimension"],
                )
                count += 1
    finally:
        await conn.close()
    return count


async def _main() -> None:
    sectors = await load()
    tags = await load_thesis_tags()
    print(f"loaded {sectors} sector rows, {tags} thesis tags")


if __name__ == "__main__":
    asyncio.run(_main())
