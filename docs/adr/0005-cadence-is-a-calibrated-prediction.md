# Investment Cadence is a calibrated prediction against an explicit label

Investment Cadence is defined as a prediction of an observable target, the Readiness label ("Firm makes at least one NEW Deal within the next 90 days", with a sector-conditioned variant), not a hand-weighted heuristic. Weights are learned and validated against historical deal outcomes by backtesting; the hand-weighted version in the PRD ships only as a labeled cold-start until enough data exists. The model must be interpretable (e.g. logistic regression or a monotonic GBM) to preserve the locked requirement that the profile shows top contributing factors, and the score's hit-rate against the label is reported so the score is falsifiable.

Why: "ready to invest now" is a predictive claim, and a score with no target variable cannot be tuned or trusted. One input, time-since-last-check, is explicitly non-monotonic (a long gap can mean pent-up or stalled), so a single linear hand-set weight is provably wrong in one regime; the shape must be learned. A black-box model was rejected because it violates the explainability requirement.

Considered options: (1) calibrated prediction, interpretable model (chosen); (2) transparent hand-weighted heuristic, no target; (3) black-box ML. Consequence: Cadence becomes a monitored model with drift and a validation cadence, not a static formula. Status: accepted.
