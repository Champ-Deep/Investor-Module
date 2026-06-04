"""Investment Cadence model + features (M6). Unit tests are hermetic; the last needs a seeded DB."""

import json
from datetime import date, timedelta

import pytest

from cadence.cadence.features import FirmRaw, extract_features
from cadence.cadence.model import ColdStartCadenceModel, LearnedCadenceModel

TODAY = date(2026, 6, 3)
_FEATURES = ["dry_powder", "deployment_pace", "time_since_last_check", "vintage_age", "fund_status"]


def test_coldstart_score_bounds():
    model = ColdStartCadenceModel()
    assert model.predict({k: 1.0 for k in _FEATURES}).score == 100
    assert model.predict({k: 0.0 for k in _FEATURES}).score == 0


def test_coldstart_top_factor_is_largest_contribution():
    model = ColdStartCadenceModel()
    res = model.predict(
        {
            "dry_powder": 1.0,
            "deployment_pace": 0.0,
            "time_since_last_check": 0.0,
            "vintage_age": 0.0,
            "fund_status": 0.0,
        }
    )
    assert res.top_factors(1)[0].feature == "dry_powder"


def test_time_since_last_check_is_non_monotonic():
    def tslc(months: float) -> float:
        raw = FirmRaw(new_deal_dates=[TODAY - timedelta(days=round(months * 30.44))])
        return extract_features(raw, TODAY)["time_since_last_check"]

    # The 2-9mo "pent-up" window must score higher than both very-recent and stalled gaps.
    assert tslc(5) > tslc(1)
    assert tslc(5) > tslc(24)


def test_learned_model_requires_training():
    with pytest.raises(NotImplementedError):
        LearnedCadenceModel().predict({k: 1.0 for k in _FEATURES})


async def test_cadence_persisted_for_active_firms(conn):
    rows = await conn.fetch("SELECT score FROM firm_cadence")
    assert rows, "expected cadence rows for active firms"
    assert all(0 <= r["score"] <= 100 for r in rows)
    rel = await conn.fetchrow(
        "SELECT fc.score, fc.contributions, fc.readiness_hit_rate "
        "FROM firm_cadence fc JOIN firm f ON f.id = fc.firm_id WHERE f.slug = 'sq3-rel-0'"
    )
    assert rel is not None
    assert rel["readiness_hit_rate"] is not None
    assert json.loads(rel["contributions"]), "expected explainability contributions"
