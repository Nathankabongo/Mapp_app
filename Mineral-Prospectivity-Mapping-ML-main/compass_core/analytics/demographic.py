"""Indicateurs demographiques."""

from compass_core.analysis.demographics import DemographicsAssessment, estimate_population_in_buffer

SOCIAL_LEVELS = {
    "faible": "Faible",
    "modérée": "Modéré",
    "élevée": "Élevé",
    "inconnu": "Non évalué",
}


def social_impact_label(assessment: DemographicsAssessment) -> str:
    mapping = {
        "faible": "Faible",
        "modérée": "Modéré",
        "élevée": "Très élevé",
        "inconnu": "Non évalué",
    }
    return mapping.get(assessment.density_class, "Non évalué")
