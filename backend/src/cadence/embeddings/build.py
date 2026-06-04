"""Build per-firm embeddings from the behavioral sector profile + thesis tags + narrative."""

import asyncio

import asyncpg

from cadence.config import get_settings
from cadence.embeddings.embedder import Embedder, get_embedder, to_pgvector

# Always include investor_type so source text is never empty (acquirers/LPs have no deal-sectors);
# an empty text -> zero vector -> NaN cosine distance, which corrupts ranking.
_SOURCE_SQL = """
SELECT f.id::text AS id, f.investor_type AS itype,
  COALESCE((SELECT string_agg(s.name, ' ')
            FROM firm_sector_profile fsp JOIN sector s ON s.id = fsp.sector_id
            WHERE fsp.firm_id = f.id), '') AS sectors,
  COALESCE((SELECT string_agg(DISTINCT s.name, ' ')
            FROM acquisition a
            JOIN company_sector cs ON cs.company_id = a.target_company_id
            JOIN sector s ON s.id = cs.sector_id
            WHERE a.acquirer_firm_id = f.id), '') AS acq_sectors,
  COALESCE((SELECT string_agg(DISTINCT s.name, ' ')
            FROM partner p JOIN partner_sector_lead psl ON psl.partner_id = p.id
            JOIN sector s ON s.id = psl.sector_id WHERE p.firm_id = f.id), '') AS partner_sectors,
  COALESCE((SELECT string_agg(t.name, ' ')
            FROM firm_thesis_tag ft JOIN thesis_tag t ON t.id = ft.tag_id
            WHERE ft.firm_id = f.id), '') AS tags,
  COALESCE(tn.narrative, '') AS narrative
FROM firm f
LEFT JOIN thesis_narrative tn ON tn.firm_id = f.id
"""


async def build_firm_embeddings(conn: asyncpg.Connection, embedder: Embedder) -> int:
    rows = await conn.fetch(_SOURCE_SQL)
    texts = [
        " ".join(
            x
            for x in (
                r["itype"],
                r["sectors"],
                r["acq_sectors"],
                r["partner_sectors"],
                r["tags"],
                r["narrative"],
            )
            if x
        )
        for r in rows
    ]
    vectors = embedder.embed(texts)
    await conn.execute("TRUNCATE firm_embedding")
    for r, text, vec in zip(rows, texts, vectors):
        await conn.execute(
            "INSERT INTO firm_embedding (firm_id, embedding, source_text) "
            "VALUES ($1, $2::vector, $3)",
            r["id"],
            to_pgvector(vec),
            text,
        )
    return len(rows)


async def _main() -> None:
    settings = get_settings()
    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        n = await build_firm_embeddings(conn, get_embedder(settings))
    finally:
        await conn.close()
    print(f"embedded {n} firms")


if __name__ == "__main__":
    asyncio.run(_main())
