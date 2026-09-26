"""Classement multicritère des cibles d'exploration."""

from __future__ import annotations

from compass_core.exploration.explainability import explain_target
from compass_core.exploration.targets import ExplorationTarget


def rank_targets(
    targets: list[ExplorationTarget],
    *,
    weights: dict[str, float] | None = None,
) -> list[ExplorationTarget]:
    """
    Classe par score composite d'exploration (explainability).

    Facteurs absents (géochimie, géophysique, etc.) = contribution nulle.
    Accessibilité / env / social restent None tant que non disponibles
    (ne pas inventer de scores de contraintes).
    """
    scored: list[tuple[float, ExplorationTarget]] = []
    for t in targets:
        explanation = explain_target(t, weights=weights)
        t.exploration_priority_score = float(explanation.composite_score)
        # Enrichir facteurs positifs/négatifs si vides
        if not t.positive_factors:
            t.positive_factors = list(explanation.positive_summary)
        if not t.negative_factors:
            t.negative_factors = list(explanation.negative_summary)
        scored.append((t.exploration_priority_score, t))

    ranked = [t for _, t in sorted(scored, key=lambda x: (-x[0], -x[1].prospectivity_score, x[1].target_id))]
    out: list[ExplorationTarget] = []
    for i, t in enumerate(ranked, start=1):
        t.target_id = f"CIBLE-{i:02d}"
        t.priority, t.priority_label = _prio(t.exploration_priority_score)
        t.stars = _stars(t.priority)
        out.append(t)
    return out


def _prio(blended: float) -> tuple[int, str]:
    if blended >= 85:
        return 1, "Très forte"
    if blended >= 70:
        return 2, "Forte"
    if blended >= 55:
        return 3, "Modérée"
    if blended >= 40:
        return 4, "Faible"
    return 5, "Très faible"


def _stars(priority: int) -> str:
    filled = max(1, min(5, 6 - priority))
    return "★" * filled + "☆" * (5 - filled)


def top_n(targets: list[ExplorationTarget], n: int = 5) -> list[ExplorationTarget]:
    return rank_targets(targets)[:n]
