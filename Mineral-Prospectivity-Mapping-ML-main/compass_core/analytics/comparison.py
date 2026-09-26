"""Comparaison de zones (jusqu'à 5)."""

from __future__ import annotations

import pandas as pd

from compass_core.analysis.site_evaluation import evaluate_site
from compass_core.constants import UNAVAILABLE
from compass_core.models.prospectivity import classify_score
from compass_core.models.risk import score_risk


def compare_points(points: list[dict]) -> pd.DataFrame:
    """
    points: [{name, lat, lon, commodity}]
    """
    columns = ["Indicateur"]
    series: dict[str, list] = {"Indicateur": []}
    reports = []
    names = []
    for p in points[:5]:
        name = p["name"]
        names.append(name)
        columns.append(name)
        reports.append(
            evaluate_site(
                float(p["lat"]),
                float(p["lon"]),
                commodity=str(p.get("commodity", "cu_co")),
            )
        )

    def add(label: str, values: list) -> None:
        series["Indicateur"].append(label)
        for name, value in zip(names, values):
            series.setdefault(name, []).append(value)

    add("Latitude", [f"{p['lat']:.4f}" for p in points[:5]])
    add("Longitude", [f"{p['lon']:.4f}" for p in points[:5]])
    add("Secteur", [r.sector_name for r in reports])
    favs = []
    for r in reports:
        info = classify_score(r.favorability.score, in_bounds=r.favorability.in_bounds)
        favs.append(
            f"{info['score_pct']} % — {info['level']}" if info["score_pct"] is not None else UNAVAILABLE
        )
    add("Favorabilité IA", favs)
    add("Minerai (modèle)", [r.mineral_prediction for r in reports])
    risks = []
    for r in reports:
        br = score_risk(
            slope_deg=r.terrain.slope_deg if r.terrain.soil_type != "Données indisponibles" else None,
            water_distance_km=r.terrain.water_distance_km,
            density_per_km2=r.demographics.density_per_km2,
        )
        risks.append(f"{br.global_score}/100 ({br.global_label})")
    add("Risque global", risks)
    add("Population (buffer)", [f"{r.demographics.population_estimate:,}" for r in reports])
    add("Cadastre", [r.cadastral_status for r in reports])
    add("Couverture données", [r.data_coverage for r in reports])
    add("Gisement le plus proche", [r._deposits_summary() for r in reports])
    return pd.DataFrame(series)
