"""Score de confiance du modèle — distinct du score de prospectivité."""

from __future__ import annotations

from dataclasses import dataclass

from compass_core.prospectivity.features import FeatureAvailability


@dataclass
class ConfidenceReport:
    prospectivity_pct: float | None
    prospectivity_level: str
    model_confidence_pct: float
    available: list[str]
    missing: list[str]
    evidence_stage: str
    disclaimer: str


def compute_model_confidence(features: FeatureAvailability, *, in_bounds: bool) -> float:
    """Confiance basée sur couverture des données + emprise — pas inventée."""
    if not in_bounds:
        return 0.0
    base = 35.0 + features.coverage_ratio * 50.0
    if features.cadastre_official:
        base += 5.0
    if features.geochemistry:
        base += 5.0
    return round(min(92.0, base), 1)


def build_confidence_report(
    *,
    prospectivity_pct: float | None,
    prospectivity_level: str,
    features: FeatureAvailability,
    in_bounds: bool,
) -> ConfidenceReport:
    conf = compute_model_confidence(features, in_bounds=in_bounds)
    stage = "PRÉDICTION DU MODÈLE" if in_bounds and prospectivity_pct is not None else "DONNÉE NON DISPONIBLE"
    return ConfidenceReport(
        prospectivity_pct=prospectivity_pct,
        prospectivity_level=prospectivity_level,
        model_confidence_pct=conf,
        available=features.available_list(),
        missing=features.missing_list(),
        evidence_stage=stage,
        disclaimer=(
            "Potentiel élevé ≠ gisement confirmé. "
            "Chaîne : Observation satellite → Indice/anomalie → Prédiction modèle → "
            "Validation terrain → Donnée géologique confirmée."
        ),
    )
