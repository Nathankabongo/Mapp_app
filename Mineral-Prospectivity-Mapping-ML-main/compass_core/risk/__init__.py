"""Package risk — réexport."""

from compass_core.models.risk import load_rules, score_risk

__all__ = ["score_risk", "load_rules"]
