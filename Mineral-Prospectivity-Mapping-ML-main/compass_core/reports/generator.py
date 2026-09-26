"""Generation de rapports (PDF, CSV, GeoJSON, GPKG, Excel)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from shapely.geometry import Point

from compass_core.analysis.site_evaluation import SiteEvaluationReport
from compass_core.constants import UNAVAILABLE
from compass_core.models.prospectivity import classify_score
from compass_core.models.risk import score_risk


def report_payload(report: SiteEvaluationReport, *, author: str = "Analyste") -> dict:
    fav = classify_score(report.favorability.score, in_bounds=report.favorability.in_bounds)
    risk = score_risk(
        slope_deg=report.terrain.slope_deg
        if report.terrain.risk_level != "inconnu"
        else None,
        water_distance_km=report.terrain.water_distance_km,
        density_per_km2=report.demographics.density_per_km2,
    )
    return {
        "title": "CriticalMineralsCompass RDC — Rapport d'analyse",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "author": author,
        "latitude": report.point.latitude,
        "longitude": report.point.longitude,
        "secteur": report.sector_name,
        "favorabilite": fav,
        "prediction": report.mineral_prediction,
        "cadastre": report.cadastral_status,
        "terrain": {
            "elevation_m": report.terrain.elevation_m,
            "slope_deg": report.terrain.slope_deg,
            "water_km": report.terrain.water_distance_km,
            "message": report.terrain.risk_message,
        },
        "demographie": {
            "population": report.demographics.population_estimate,
            "densite": report.demographics.density_per_km2,
            "rayon_km": report.demographics.radius_km,
        },
        "risque": {
            "score": risk.global_score,
            "label": risk.global_label,
            "disclaimer": risk.disclaimer,
        },
        "couverture": report.data_coverage,
        "recommandation": (
            "Croiser avec données CAMI officielles, cartes géologiques et visite de terrain. "
            "L'indice IA n'est pas une découverte confirmée."
        ),
    }


def export_csv(payload: dict, path: Path) -> Path:
    rows = [
        {"champ": k, "valeur": v}
        for k, v in payload.items()
        if not isinstance(v, dict)
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def export_excel(payload: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    flat = {k: str(v) for k, v in payload.items()}
    pd.DataFrame([flat]).to_excel(path, index=False)
    return path


def export_geojson(report: SiteEvaluationReport, path: Path) -> Path:
    import geopandas as gpd

    gdf = gpd.GeoDataFrame(
        [
            {
                "secteur": report.sector_name,
                "favorabilite": report.favorability.score if report.favorability.in_bounds else None,
                "cadastre": report.cadastral_status,
                "geometry": Point(report.point.longitude, report.point.latitude),
            }
        ],
        crs="EPSG:4326",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, driver="GeoJSON")
    return path


def export_gpkg(report: SiteEvaluationReport, path: Path) -> Path:
    import geopandas as gpd

    gdf = gpd.GeoDataFrame(
        [
            {
                "secteur": report.sector_name,
                "geometry": Point(report.point.longitude, report.point.latitude),
            }
        ],
        crs="EPSG:4326",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, driver="GPKG")
    return path


def export_pdf(payload: dict, path: Path) -> Path | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        return None

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "CriticalMineralsCompass RDC")
    y -= 18
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, "Plateforme nationale d'intelligence minière et géospatiale")
    y -= 22
    pdf.drawString(50, y, f"Date UTC : {payload.get('generated_utc', '')}")
    y -= 14
    pdf.drawString(50, y, f"Auteur : {payload.get('author', '')}")
    y -= 24
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "1. Résumé exécutif")
    y -= 16
    pdf.setFont("Helvetica", 9)
    for line in [
        f"Localisation : {payload.get('secteur')} ({payload.get('latitude')}, {payload.get('longitude')})",
        f"Favorabilité : {payload.get('favorabilite')}",
        f"Cadastre : {payload.get('cadastre', UNAVAILABLE)}",
        f"Risque : {payload.get('risque')}",
        f"Couverture : {payload.get('couverture')}",
        str(payload.get("recommandation", "")),
        "Sources : atlas local, modèle IA si emprise, MNT si disponible.",
        "Niveau de confiance : voir page Données & sources.",
    ]:
        for chunk in _wrap(str(line), 95):
            if y < 60:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 9)
            pdf.drawString(50, y, chunk)
            y -= 12
    pdf.save()
    return path


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if len(trial) > width:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]
