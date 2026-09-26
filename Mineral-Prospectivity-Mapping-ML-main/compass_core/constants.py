"""Classes de vérité étendues — transparence scientifique."""

from __future__ import annotations

UNAVAILABLE = "Information non disponible dans les sources utilisées."

DATA_CLASSES = {
    "official": "DONNÉE OFFICIELLE",
    "open": "DONNÉE OPEN DATA",
    "historical": "DONNÉE HISTORIQUE",
    "estimated": "DONNÉE ESTIMÉE",
    "modeled": "DONNÉE MODÉLISÉE",
    "experimental": "DONNÉE EXPÉRIMENTALE",
    "computed": "DONNÉE CALCULÉE",
    "demo": "DONNÉE DE DÉMONSTRATION",
    "imported": "DONNÉE IMPORTÉE",
    "observation": "OBSERVATION SATELLITE",
    "anomaly": "INDICE / ANOMALIE",
    "prediction": "PRÉDICTION DU MODÈLE",
    "field": "À VALIDER SUR LE TERRAIN",
    "confirmed": "DONNÉE GÉOLOGIQUE CONFIRMÉE",
}

# Chaîne de crédibilité (télédétection → terrain)
EVIDENCE_CHAIN = (
    ("observation", "OBSERVATION SATELLITE"),
    ("anomaly", "INDICE / ANOMALIE"),
    ("prediction", "PRÉDICTION DU MODÈLE"),
    ("field", "VALIDATION TERRAIN"),
    ("confirmed", "DONNÉE GÉOLOGIQUE CONFIRMÉE"),
)

CONFIDENCE_STARS = {
    5: "★★★★★ Très haute",
    4: "★★★★☆ Haute",
    3: "★★★☆☆ Moyenne",
    2: "★★☆☆☆ Faible",
    1: "★☆☆☆☆ Très faible",
}

FAVORABILITY_BANDS = (
    (0.0, 0.2, "Très faible"),
    (0.2, 0.4, "Faible"),
    (0.4, 0.6, "Moyenne"),
    (0.6, 0.8, "Forte"),
    (0.8, 1.01, "Très forte"),
)

PROSPECTIVITY_LABELS = {
    "très faible": "TRÈS FAIBLE",
    "tres faible": "TRÈS FAIBLE",
    "faible": "FAIBLE",
    "moyenne": "MOYENNE",
    "modérée": "MOYENNE",
    "forte": "FORTE",
    "élevée": "FORTE",
    "très forte": "TRÈS FORTE",
    "tres forte": "TRÈS FORTE",
    "très élevée": "TRÈS FORTE",
}

# Chaîne d'exploration étendue (transparence scientifique)
EXPLORATION_TRUTH_CHAIN = (
    ("observation", "OBSERVATION"),
    ("measured", "DONNÉE MESURÉE"),
    ("interpolated", "INTERPOLATION"),
    ("estimated", "ESTIMATION"),
    ("prediction", "PRÉDICTION IA"),
    ("modeled", "MODÈLE GÉOLOGIQUE"),
    ("hypothesis", "HYPOTHÈSE"),
    ("field", "VALIDATION TERRAIN"),
)

DATA_CLASSES.update(
    {
        "measured": "DONNÉE MESURÉE",
        "interpolated": "INTERPOLATION",
        "hypothesis": "HYPOTHÈSE",
    }
)

ROLES = ("ADMIN", "ANALYSTE", "GÉOLOGUE", "OPÉRATEUR", "LECTEUR")

TARGET_MINERALS = (
    "cuivre",
    "cobalt",
    "lithium",
    "or",
    "coltan",
    "nickel",
    "manganèse",
    "terres rares",
)
