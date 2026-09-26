"""Analyse démographique et impact social (zone tampon)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from compass_core.analysis.favorability import GeoGrid, utm_to_pixel


@dataclass
class DemographicsAssessment:
    """Estimation de population dans une zone tampon."""

    radius_km: float
    population_estimate: int
    density_per_km2: float
    social_impact: str
    implantation_advice: str
    density_class: str


def generate_synthetic_population_grid(
    reference: GeoGrid,
    *,
    seed: int = 42,
) -> GeoGrid:
    """
    Génère un raster de densité de population synthétique (hab/km²).

    Simule WorldPop / LandScan en attendant l'intégration de données réelles.
    """
    rng = np.random.default_rng(seed)
    rows, cols = reference.rows, reference.cols
  # Plus dense près des axes (centre de la grille)
    row_idx = np.arange(rows)[:, None]
    col_idx = np.arange(cols)[None, :]
    center_row, center_col = rows / 2, cols / 2
    dist = np.hypot(row_idx - center_row, col_idx - center_col)
    dist_norm = dist / max(center_row, center_col)
    base = rng.gamma(2.0, 80.0, size=(rows, cols))
    density = base * (1.8 - dist_norm)
    density = np.clip(density, 5, 2500)
    return GeoGrid(values=density.astype(np.float32), geo_transform=reference.geo_transform)


def estimate_population_in_buffer(
    population_grid: GeoGrid,
    *,
    utm_x: float,
    utm_y: float,
    radius_km: float = 10.0,
) -> DemographicsAssessment:
    """Calcule la population estimée dans un cercle autour du point."""
    row, col, in_bounds = utm_to_pixel(utm_x, utm_y, population_grid)
    if not in_bounds:
        return DemographicsAssessment(
            radius_km=radius_km,
            population_estimate=0,
            density_per_km2=0.0,
            social_impact="inconnu",
            implantation_advice="Hors zone de données démographiques.",
            density_class="inconnu",
        )

    radius_px_x = int(radius_km * 1000 / population_grid.pixel_size_x)
    radius_px_y = int(radius_km * 1000 / population_grid.pixel_size_y)
    row_min = max(0, row - radius_px_y)
    row_max = min(population_grid.rows, row + radius_px_y + 1)
    col_min = max(0, col - radius_px_x)
    col_max = min(population_grid.cols, col + radius_px_x + 1)

    patch = population_grid.values[row_min:row_max, col_min:col_max]
    rr, cc = np.ogrid[row_min:row_max, col_min:col_max]
    dist_px = np.hypot(rr - row, cc - col)
    mask = dist_px <= max(radius_px_x, radius_px_y)

    pixel_area_km2 = (population_grid.pixel_size_x * population_grid.pixel_size_y) / 1_000_000
    densities = patch[mask]
    population = int(densities.sum() * pixel_area_km2)
    area_km2 = mask.sum() * pixel_area_km2
    mean_density = population / area_km2 if area_km2 > 0 else 0.0

    if mean_density < 50:
        density_class = "faible"
        social_impact = "Faible densité — impact social limité"
        advice = "Zone favorable pour infrastructures lourdes et base-vie."
    elif mean_density < 200:
        density_class = "modérée"
        social_impact = "Densité modérée — consultation communautaire recommandée"
        advice = "Prévoir dialogue avec les autorités locales et chefferies."
    else:
        density_class = "élevée"
        social_impact = "Forte densité — RSE et indemnisation nécessaires"
        advice = (
            "Alerte : plans de responsabilité sociétale (RSE), "
            "réinstallation et gestion de l'orpaillage artisanal requis."
        )

    return DemographicsAssessment(
        radius_km=radius_km,
        population_estimate=population,
        density_per_km2=float(mean_density),
        social_impact=social_impact,
        implantation_advice=advice,
        density_class=density_class,
    )


def load_or_create_population_grid(
    raster_path: str | Path,
    cache_path: str | Path = "data/rdc/atlas/population_density.npy",
) -> GeoGrid:
    """Charge ou génère le raster de densité de population."""
    from compass_core.analysis.terrain import load_dem_band

    cache = Path(cache_path)
    dem = load_dem_band(raster_path)
    if cache.exists():
        values = np.load(cache)
        return GeoGrid(values=values, geo_transform=dem.geo_transform)
    grid = generate_synthetic_population_grid(dem)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache, grid.values)
    return grid
