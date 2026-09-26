"""Classification scientifique des données — transparence obligatoire."""

from __future__ import annotations

from typing import Literal

# Classes canoniques (mission nationale)
DataClass = Literal[
    "OFFICIAL",
    "OPEN",
    "THIRD_PARTY",
    "DEMO",
    "SYNTHETIC",
    "MODELED",
    "DERIVED",
    "PREDICTED",
    "HISTORICAL",
    "ESTIMATED",
    "UNAVAILABLE",
]

DATA_CLASS_LABELS: dict[str, str] = {
    "OFFICIAL": "DONNÉE OFFICIELLE",
    "OPEN": "DONNÉE OPEN DATA",
    "THIRD_PARTY": "DONNÉE TIERS",
    "DEMO": "DONNÉE DE DÉMONSTRATION",
    "SYNTHETIC": "DONNÉE SYNTHÉTIQUE",
    "MODELED": "DONNÉE MODÉLISÉE",
    "DERIVED": "DONNÉE DÉRIVÉE",
    "PREDICTED": "PRÉDICTION / MODÈLE",
    "HISTORICAL": "DONNÉE HISTORIQUE",
    "ESTIMATED": "DONNÉE ESTIMÉE",
    "UNAVAILABLE": "NON DISPONIBLE",
}

# Niveau épistémologique (Observation → Décision)
EvidenceLevel = Literal[
    "OBSERVATION",
    "INTERPRETATION",
    "PREDICTION",
    "DECISION",
    "VALIDATION",
]

EVIDENCE_LEVEL_LABELS: dict[str, str] = {
    "OBSERVATION": "Niveau 1 — Observation",
    "INTERPRETATION": "Niveau 2 — Interprétation",
    "PREDICTION": "Niveau 3 — Prédiction",
    "DECISION": "Niveau 4 — Décision",
    "VALIDATION": "Niveau 5 — Validation",
}

# Disponibilité opérationnelle
AvailabilityStatus = Literal[
    "CONNECTED",
    "LOCAL_OK",
    "PARTIAL",
    "TO_CONFIGURE",
    "NOT_CONNECTED",
    "NOT_AVAILABLE",
    "DEMO",
    "SYNTHETIC",
]

AVAILABILITY_LABELS: dict[str, str] = {
    "CONNECTED": "CONNECTÉ",
    "LOCAL_OK": "LOCAL OK",
    "PARTIAL": "PARTIEL",
    "TO_CONFIGURE": "À CONFIGURER",
    "NOT_CONNECTED": "NOT_CONNECTED",
    "NOT_AVAILABLE": "NON DISPONIBLE",
    "DEMO": "DÉMO",
    "SYNTHETIC": "SYNTHÉTIQUE",
}

# Mapping legacy → canonique (compatibilité UI existante)
_LEGACY_TO_CANONICAL: dict[str, str] = {
    "official": "OFFICIAL",
    "open": "OPEN",
    "historical": "HISTORICAL",
    "estimated": "ESTIMATED",
    "modeled": "MODELED",
    "experimental": "DERIVED",
    "computed": "DERIVED",
    "demo": "DEMO",
    "imported": "THIRD_PARTY",
    "observation": "OPEN",
    "anomaly": "DERIVED",
    "prediction": "PREDICTED",
    "field": "OFFICIAL",
    "confirmed": "OFFICIAL",
    "measured": "OFFICIAL",
    "interpolated": "DERIVED",
    "hypothesis": "MODELED",
    "unavailable": "UNAVAILABLE",
}


def canonicalize_data_class(value: str | None) -> str:
    """Normalise une classe legacy ou canonique."""
    if not value:
        return "UNAVAILABLE"
    key = value.strip()
    upper = key.upper().replace(" ", "_").replace("-", "_")
    if upper in DATA_CLASS_LABELS:
        return upper
    return _LEGACY_TO_CANONICAL.get(key.lower(), "UNAVAILABLE")


def data_class_label(value: str | None) -> str:
    return DATA_CLASS_LABELS.get(canonicalize_data_class(value), str(value or "—"))


def evidence_level_label(value: str | None) -> str:
    if not value:
        return EVIDENCE_LEVEL_LABELS["OBSERVATION"]
    key = value.strip().upper()
    return EVIDENCE_LEVEL_LABELS.get(key, value)


def availability_label(value: str | None) -> str:
    if not value:
        return AVAILABILITY_LABELS["NOT_AVAILABLE"]
    key = value.strip().upper().replace(" ", "_").replace("-", "_")
    # Accents FR historiques
    aliases = {
        "CONNECTÉ": "CONNECTED",
        "CONNECTE": "CONNECTED",
        "DISPONIBLE": "LOCAL_OK",
        "À_CONFIGURER": "TO_CONFIGURE",
        "A_CONFIGURER": "TO_CONFIGURE",
        "NON_DISPONIBLE": "NOT_AVAILABLE",
        "DÉMO": "DEMO",
        "DEMO": "DEMO",
    }
    key = aliases.get(key, key)
    return AVAILABILITY_LABELS.get(key, value)
