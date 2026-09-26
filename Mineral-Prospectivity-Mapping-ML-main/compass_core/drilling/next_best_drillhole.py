"""Next Best Drillhole — valeur de l'information."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE
from compass_core.drilling.planning import propose_drill_from_target


def next_best_drillhole(*, targets: list[dict], existing_holes: int = 0) -> dict:
    """
    Priorise potentiel + incertitude (faible confiance = besoin d'info)
    + absence de forages existants.
    """
    if not targets:
        return {
            "status": "NON DISPONIBLE",
            "message": "Aucune cible pour calculer le prochain forage.",
            "data_class": "unavailable",
        }

    scored = []
    for t in targets:
        pot = float(t.get("prospectivity_score") or 0)
        conf = float(t.get("confidence_pct") or 50)
        uncertainty = 100.0 - conf
        # Valeur d'information : fort potentiel × incertitude
        voi = 0.5 * pot + 0.4 * uncertainty + (10.0 if existing_holes == 0 else 0.0)
        scored.append((voi, t))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][1]
    proposal = propose_drill_from_target(best)
    proposal["voi_score"] = round(scored[0][0], 1)
    proposal["logic"] = (
        "Next Best Drillhole = potentiel + incertitude + valeur de l'information "
        "(+ accessibilité lorsque disponible)."
    )
    proposal["accessibility"] = UNAVAILABLE
    proposal["status"] = "PROPOSITION"
    return proposal
