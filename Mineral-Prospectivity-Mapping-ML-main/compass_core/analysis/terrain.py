"""Analyse du relief, des sols et des risques géotechniques."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from compass_core.analysis.favorability import GeoGrid, utm_to_pixel
from compass_core.data.gdal_compat import import_gdal


SLOPE_CRITICAL_DEG = 25.0
SLOPE_MODERATE_DEG = 15.0
WATER_SENSITIVE_KM = 0.5  # 500 m — seuil contamination hydrique


@dataclass
class TerrainAssessment:
    """Diagnostic sol / relief pour un point ciblé."""

    elevation_m: float
    slope_deg: float
    soil_type: str
    geology: str
    water_distance_km: float
    risk_level: str
    risk_message: str
    slope_alert: bool
    flood_risk: bool


def load_dem_band(raster_path: str | Path, *, band_index: int = 8) -> GeoGrid:
    """Charge la bande MNT (élévation) depuis le raster multiphysique."""
    gdal = import_gdal()
    dataset = gdal.Open(str(raster_path))
    if dataset is None:
        raise FileNotFoundError(f"Raster introuvable : {raster_path}")

    if band_index > dataset.RasterCount:
        band_index = dataset.RasterCount

    values = dataset.GetRasterBand(band_index).ReadAsArray().astype(np.float32)
    return GeoGrid(values=values, geo_transform=dataset.GetGeoTransform())


def compute_slope_grid(dem: GeoGrid) -> np.ndarray:
    """Calcule la pente (degrés) à partir du MNT."""
    dy, dx = np.gradient(dem.values, dem.pixel_size_y, dem.pixel_size_x)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    return np.degrees(slope_rad)


def _estimate_water_distance(dem: GeoGrid, row: int, col: int) -> float:
    """Estime la distance au drainage le plus proche (vallées = altitudes basses locales)."""
    values = dem.values
    threshold = np.percentile(values, 20)
    low_mask = values <= threshold
    if not low_mask.any():
        return 99.0

    low_rows, low_cols = np.where(low_mask)
    distances = np.hypot(low_rows - row, low_cols - col) * dem.pixel_size_x
    return float(distances.min() / 1000)


def _soil_from_slope_and_elevation(slope_deg: float, elevation_m: float) -> tuple[str, str]:
    if elevation_m > 1200 and slope_deg > 20:
        return "Ferralitique sur socle altéré", "Roches métamorphiques / altération profonde"
    if slope_deg < 8:
        return "Ferralitique sur roches sédimentaires", "Sédiments du Katanga (Cu-Co)"
    if slope_deg < 18:
        return "Sol ferrugineux tropicaux", "Formation latéritique"
    return "Sol peu évolué sur versant", "Pente active — érosion modérée"


def analyze_terrain(
    dem: GeoGrid,
    *,
    utm_x: float,
    utm_y: float,
) -> TerrainAssessment:
    """Évalue le relief et les risques géotechniques à un point."""
    row, col, in_bounds = utm_to_pixel(utm_x, utm_y, dem)
    if not in_bounds:
        return TerrainAssessment(
            elevation_m=0.0,
            slope_deg=0.0,
            soil_type="Hors emprise des données",
            geology="—",
            water_distance_km=99.0,
            risk_level="inconnu",
            risk_message="Point hors de la zone couverte par le MNT.",
            slope_alert=False,
            flood_risk=False,
        )

    slope_grid = compute_slope_grid(dem)
    elevation = float(dem.values[row, col])
    slope = float(slope_grid[row, col])
    water_km = _estimate_water_distance(dem, row, col)
    soil, geology = _soil_from_slope_and_elevation(slope, elevation)

    slope_alert = slope >= SLOPE_CRITICAL_DEG
    water_sensitive = water_km < WATER_SENSITIVE_KM
    flood_risk = water_km < 1.0 and slope < 5

    if slope_alert:
        risk_level = "élevé"
        risk_message = (
            f"Risque élevé d'instabilité géotechnique / glissement de terrain "
            f"(pente {slope:.1f}° > {SLOPE_CRITICAL_DEG:.0f}°)."
        )
    elif water_sensitive:
        risk_level = "modéré"
        risk_message = (
            f"Zone sensible : cours d'eau à {water_km * 1000:.0f} m — "
            "risque de contamination hydrique."
        )
    elif flood_risk:
        risk_level = "modéré"
        risk_message = (
            f"Zone proche d'un cours d'eau ({water_km:.1f} km) — "
            "risque d'inondation et de contamination des nappes."
        )
    elif slope >= SLOPE_MODERATE_DEG:
        risk_level = "modéré"
        risk_message = (
            f"Pente modérée ({slope:.1f}°) — surveillance des talus de déblais recommandée."
        )
    else:
        risk_level = "faible"
        risk_message = (
            f"Faible risque de glissement — cours d'eau à {water_km:.1f} km."
        )

    return TerrainAssessment(
        elevation_m=elevation,
        slope_deg=slope,
        soil_type=soil,
        geology=geology,
        water_distance_km=water_km,
        risk_level=risk_level,
        risk_message=risk_message,
        slope_alert=slope_alert,
        flood_risk=flood_risk,
    )
