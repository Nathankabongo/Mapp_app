"""Score de risque configurable — indicateur, pas expertise de terrain."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

DEFAULT_RULES = {
    "geotech_slope_high_deg": 25.0,
    "geotech_slope_mid_deg": 15.0,
    "hydro_sensitive_m": 500.0,
    "hydro_moderate_m": 2000.0,
    "social_high_density": 200.0,
    "social_mid_density": 50.0,
}

RULES_PATH = Path("config/risk_rules.json")


def load_rules(path: Path = RULES_PATH) -> dict:
    if path.exists():
        try:
            return {**DEFAULT_RULES, **json.loads(path.read_text(encoding="utf-8"))}
        except json.JSONDecodeError:
            return dict(DEFAULT_RULES)
    return dict(DEFAULT_RULES)


@dataclass
class RiskBreakdown:
    geotech: str
    hydro: str
    environmental: str
    social: str
    infrastructure: str
    global_score: int
    global_label: str
    messages: list[str]
    disclaimer: str


def _band(value: float, low: str, mid: str, high: str, mid_th: float, high_th: float) -> str:
    if value >= high_th:
        return high
    if value >= mid_th:
        return mid
    return low


def score_risk(
    *,
    slope_deg: float | None,
    water_distance_km: float | None,
    density_per_km2: float | None,
    rules: dict | None = None,
) -> RiskBreakdown:
    rules = rules or load_rules()
    messages: list[str] = []
    points = 0
    n = 0

    geotech = "inconnu"
    if slope_deg is not None:
        n += 1
        high = float(rules["geotech_slope_high_deg"])
        mid = float(rules["geotech_slope_mid_deg"])
        if slope_deg >= high:
            geotech = "élevé"
            points += 80
            messages.append(f"SI pente ≥ {high:.0f}° ALORS risque géotechnique élevé.")
        elif slope_deg >= mid:
            geotech = "moyen"
            points += 45
        else:
            geotech = "faible"
            points += 15

    hydro = "inconnu"
    if water_distance_km is not None and water_distance_km < 90:
        n += 1
        dist_m = water_distance_km * 1000
        sens = float(rules["hydro_sensitive_m"])
        mod = float(rules["hydro_moderate_m"])
        if dist_m < sens:
            hydro = "élevé"
            points += 75
            messages.append(
                f"SI distance rivière < {sens:.0f} m ALORS zone sensible hydrographique."
            )
        elif dist_m < mod:
            hydro = "moyen"
            points += 40
        else:
            hydro = "faible"
            points += 15

    social = "inconnu"
    if density_per_km2 is not None:
        n += 1
        if density_per_km2 >= float(rules["social_high_density"]):
            social = "élevé"
            points += 70
        elif density_per_km2 >= float(rules["social_mid_density"]):
            social = "moyen"
            points += 40
        else:
            social = "faible"
            points += 15

    environmental = hydro if hydro != "inconnu" else "inconnu"
    infrastructure = "inconnu"
    global_score = int(round(points / n)) if n else 0
    if global_score >= 65:
        label = "ÉLEVÉ"
    elif global_score >= 40:
        label = "MOYEN"
    elif n:
        label = "FAIBLE"
    else:
        label = "NON ÉVALUÉ"

    return RiskBreakdown(
        geotech=geotech,
        hydro=hydro,
        environmental=environmental,
        social=social,
        infrastructure=infrastructure,
        global_score=global_score,
        global_label=label,
        messages=messages,
        disclaimer=(
            "Indicateurs d'aide à la décision, non un diagnostic réglementaire "
            "ni une expertise de terrain."
        ),
    )
