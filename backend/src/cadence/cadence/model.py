"""Cadence model interface + cold-start impl + learned stub (ADR 0005, 0007).

Both impls consume the SAME feature vector and return the SAME result shape, so swapping cold-start
for a learned model is a config change. The result always exposes per-feature contributions so the
profile can show the top contributing factors (the locked explainability requirement).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

# Cold-start weights = the PRD Deployment Urgency table. Replaced by learned weights once enough
# labeled history exists. time_since_last_check is non-monotonic and is shaped in the feature
# extractor (bucketed), not by a single linear weight here.
COLD_START_WEIGHTS: dict[str, float] = {
    "dry_powder": 0.30,
    "deployment_pace": 0.25,
    "time_since_last_check": 0.20,
    "vintage_age": 0.15,
    "fund_status": 0.10,
}


@dataclass
class Contribution:
    feature: str
    value: float
    weight: float
    contribution: float


@dataclass
class CadenceResult:
    score: int
    model_version: str
    contributions: list[Contribution]

    def top_factors(self, n: int | None = None) -> list[Contribution]:
        ordered = sorted(self.contributions, key=lambda c: c.contribution, reverse=True)
        return ordered if n is None else ordered[:n]


class CadenceModel(Protocol):
    model_version: str

    def predict(self, features: dict[str, float]) -> CadenceResult: ...


class ColdStartCadenceModel:
    """Transparent labeled cold-start: weighted sum of normalized features, scaled to 0-100."""

    model_version = "coldstart-v1"

    def predict(self, features: dict[str, float]) -> CadenceResult:
        contributions = []
        for feature, weight in COLD_START_WEIGHTS.items():
            value = float(features.get(feature, 0.5))
            contributions.append(Contribution(feature, value, weight, weight * value))
        raw = sum(c.contribution for c in contributions)
        score = max(0, min(100, round(100 * raw)))
        return CadenceResult(
            score=score, model_version=self.model_version, contributions=contributions
        )


class LearnedCadenceModel:
    """Same interface; trained (logistic regression / monotonic GBM) against the Readiness label."""

    model_version = "learned-v0"

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self._weights = weights

    def predict(self, features: dict[str, float]) -> CadenceResult:
        if not self._weights:
            raise NotImplementedError(
                "LearnedCadenceModel is not trained yet; ship ColdStartCadenceModel until enough "
                "labeled history exists to learn and backtest weights (ADR 0005)."
            )
        contributions = [
            Contribution(f, float(features.get(f, 0.5)), w, w * float(features.get(f, 0.5)))
            for f, w in self._weights.items()
        ]
        raw = sum(c.contribution for c in contributions)
        score = max(0, min(100, round(100 * raw)))
        return CadenceResult(
            score=score, model_version=self.model_version, contributions=contributions
        )
