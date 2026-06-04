"""Compute + persist Investment Cadence for active firms (recompute weekly per the SLA)."""

import asyncio
import json
from datetime import date

import asyncpg

from cadence.cadence.features import extract_features, load_firm_raws
from cadence.cadence.label import backtest
from cadence.cadence.model import CadenceModel, ColdStartCadenceModel
from cadence.config import get_settings


async def compute_and_store(
    conn: asyncpg.Connection, *, today: date, model: CadenceModel | None = None
) -> int:
    model = model or ColdStartCadenceModel()
    raws = await load_firm_raws(conn)
    hit_rate = backtest(raws, model, today)
    active = {
        r["id"]
        for r in await conn.fetch("SELECT firm_id::text AS id FROM firm_activity WHERE is_active")
    }
    await conn.execute("TRUNCATE firm_cadence")
    count = 0
    for fid, raw in raws.items():
        if fid not in active:
            continue
        features = extract_features(raw, today)
        result = model.predict(features)
        contributions = [
            {
                "feature": c.feature,
                "value": round(c.value, 4),
                "weight": c.weight,
                "contribution": round(c.contribution, 4),
            }
            for c in result.top_factors()
        ]
        await conn.execute(
            "INSERT INTO firm_cadence (firm_id, score, model_version, features, contributions, "
            "readiness_hit_rate) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6)",
            fid,
            result.score,
            result.model_version,
            json.dumps({k: round(v, 4) for k, v in features.items()}),
            json.dumps(contributions),
            round(hit_rate, 4),
        )
        count += 1
    return count


async def _main() -> None:
    settings = get_settings()
    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        n = await compute_and_store(conn, today=date.today())
    finally:
        await conn.close()
    print(f"cadence computed for {n} active firms")


if __name__ == "__main__":
    asyncio.run(_main())
