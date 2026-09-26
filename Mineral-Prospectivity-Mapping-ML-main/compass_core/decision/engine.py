"""Aide à la décision explicable."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from compass_core.environment.assessment import environmental_state
from compass_core.mining.asm import asm_status
from compass_core.mining.cami import cami_status
from compass_core.models.risk import score_risk
from compass_core.prospectivity.prediction import ProspectivityResult, run_prospectivity
from compass_core.analysis.site_evaluation import evaluate_site


@dataclass
class DecisionReport:
    zone: str
    mineral: str
    decision: str
    rationale: list[str]
    prospectivity: dict
    risk_label: str
    risk_score: int
    environment_state: str
    cami_verified: int
    evidence_chain: list[str]
    disclaimer: str

    def to_dict(self) -> dict:
        return asdict(self)


def decide(
    *,
    zone: str = "Kolwezi",
    mineral: str = "cuivre",
    latitude: float | None = None,
    longitude: float | None = None,
) -> DecisionReport:
    prosp = run_prospectivity(zone=zone, mineral=mineral, latitude=latitude, longitude=longitude)
    site = evaluate_site(prosp.latitude, prosp.longitude)
    risk = score_risk(
        slope_deg=None if site.terrain.risk_level == "inconnu" else site.terrain.slope_deg,
        water_distance_km=site.terrain.water_distance_km if site.terrain.risk_level != "inconnu" else None,
        density_per_km2=site.demographics.density_per_km2,
    )
    env = environmental_state(prosp.latitude, prosp.longitude)
    cami = cami_status()
    asm = asm_status()

    rationale = [
        f"Prospectivité : {prosp.prospectivity_level}"
        + (f" ({prosp.prospectivity_pct} %)" if prosp.prospectivity_pct is not None else ""),
        f"Confiance modèle : {prosp.model_confidence_pct} %",
        f"Risque global : {risk.global_score}/100 ({risk.global_label})",
        f"Environnement : {env['state']}",
        f"CAMI vérifié : {cami['verified_count']} concession(s)",
        f"ASM : {asm['status']}",
        prosp.recommendation_hint,
    ]

    decision = prosp.recommendation_hint
    if "élevé" in decision.lower():
        label = "POTENTIEL ÉLEVÉ (PRÉDICTIF)"
    elif "moyen" in decision.lower():
        label = "POTENTIEL MOYEN"
    elif "faible" in decision.lower():
        label = "POTENTIEL FAIBLE"
    elif "contraintes" in decision.lower():
        label = "ZONE À CONTRAINTES DE DONNÉES"
    else:
        label = "ZONE À ÉTUDIER DAVANTAGE"

    return DecisionReport(
        zone=prosp.zone,
        mineral=prosp.mineral,
        decision=label,
        rationale=rationale,
        prospectivity=prosp.to_dict(),
        risk_label=risk.global_label,
        risk_score=risk.global_score,
        environment_state=env["state"],
        cami_verified=int(cami["verified_count"]),
        evidence_chain=[
            "OBSERVATION SATELLITE",
            "INDICE / ANOMALIE",
            "PRÉDICTION DU MODÈLE",
            "VALIDATION TERRAIN",
            "DONNÉE GÉOLOGIQUE CONFIRMÉE",
        ],
        disclaimer=(
            "Recommandation d'aide à la décision — non une certification géologique, "
            "juridique ou financière. Potentiel élevé ≠ gisement confirmé."
        ),
    )
