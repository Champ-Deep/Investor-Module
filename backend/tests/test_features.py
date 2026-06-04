"""Warm-intro (co-investor) and Look-Alike features (M5). Requires a migrated + seeded DB."""

from cadence.query.features import coinvestors, look_alike


async def test_sq8_coinvestors_with_lightspeed_in_healthtech(conn, today):
    res = await coinvestors(
        conn, lead_slug="lightspeed", sector="digital-health", within_months=36, today=today
    )
    slugs = {r["slug"] for r in res}
    for i in range(5):
        assert f"sq8-rel-{i}" in slugs
    # wrong sector / different round / too old must NOT appear
    for d in ["sq8-dis-sector", "sq8-dis-notlightspeed", "sq8-dis-old"]:
        assert d not in slugs


async def test_look_alike_surfaces_same_profile_firms(conn):
    res = await look_alike(conn, firm_slug="sq3-rel-0", limit=10)
    assert res, "expected look-alike results"
    # other vertical-SaaS relevants share the same behavioral profile -> high similarity
    assert any(r["slug"].startswith("sq3-rel-") for r in res[:8])
