"""Orchestration de la fiche d'évaluation site (aide à la décision 360°)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from compass_core.analysis.coordinates import make_geo_point
from compass_core.analysis.demographics import (
    DemographicsAssessment,
    estimate_population_in_buffer,
    load_or_create_population_grid,
)
from compass_core.analysis.favorability import (
    FavorabilityHit,
    HotspotZone,
    extract_hotspots,
    load_geogrid,
    predict_commodity_label,
    query_favorability,
)
from compass_core.analysis.mineral_layers import (
    MINERAL_LAYERS,
    NearbyDeposit,
    find_nearby_deposits,
    load_all_layers,
)
from compass_core.analysis.terrain import TerrainAssessment, analyze_terrain, load_dem_band


DEFAULT_FAVORABILITY_PATHS = (
    "outputs/kolwezi_sample/kolwezi_woe_cu_co_favorability.tif",
    "outputs/kolwezi_sample/kolwezi_woe_cu_co_favorability.npy",
    "outputs/live_demo/kolwezi_woe_cu_co_favorability.npy",
)

DEFAULT_RASTER = "data/rdc/kolwezi/stack_multiphysics.tif"


@dataclass
class SiteEvaluationReport:
    """Fiche synthétique d'évaluation d'un site GPS."""

    point: object  # GeoPoint
    favorability: FavorabilityHit
    mineral_prediction: str
    terrain: TerrainAssessment
    demographics: DemographicsAssessment
    cadastral_status: str
    nearby_deposits: list[NearbyDeposit] = field(default_factory=list)
    hotspots: list[HotspotZone] = field(default_factory=list)
    sector_name: str = "Kolwezi"
    data_coverage: str = "complète"

    def to_summary_rows(self) -> list[tuple[str, str]]:
        """Retourne les lignes du tableau récapitulatif."""
        point = self.point
        fav = self.favorability
        ter = self.terrain
        demo = self.demographics
        return [
            (
                "Coordonnées",
                f"Lat {point.latitude:.4f}, Lon {point.longitude:.4f} ({self.sector_name})",
            ),
            (
                "Minerai prédit (IA)",
                f"**{self.mineral_prediction}** — Favorabilité **{fav.score:.0%}**",
            ),
            (
                "Données sol & relief",
                f"Pente {ter.slope_deg:.1f}°, relief {_relief_label(ter.slope_deg, ter.elevation_m)} — {ter.soil_type}",
            ),
            (
                "Alerte sécurité / risque",
                ter.risk_message,
            ),
            (
                f"Démographie (rayon {demo.radius_km:.0f} km)",
                f"~{demo.population_estimate:,} hab. ({demo.density_class}) — {demo.implantation_advice}",
            ),
            (
                "Statut cadastral (CAMI)",
                self.cadastral_status,
            ),
            (
                "Gisements connus à proximité",
                self._deposits_summary(),
            ),
        ]

    def _deposits_summary(self) -> str:
        if not self.nearby_deposits:
            return "Aucun gisement répertorié dans le rayon"
        top = self.nearby_deposits[:3]
        parts = []
        for d in top:
            label = d.name or d.label
            parts.append(f"{label} ({d.label}) à {d.distance_km:.1f} km")
        return " · ".join(parts)


def resolve_favorability_path(paths: tuple[str, ...] = DEFAULT_FAVORABILITY_PATHS) -> Path | None:
    """Trouve la première carte de favorabilité disponible."""
    for candidate in paths:
        path = Path(candidate)
        if path.exists():
            return path
    return None


def _infer_cadastral_status(latitude: float, longitude: float) -> str:
    """Statut cadastral uniquement si un polygone local contient le point."""
    from compass_core.constants import UNAVAILABLE
    from compass_core.io.cadastral import lookup_permit

    hit = lookup_permit(latitude, longitude)
    if hit["data_class"] == "unavailable":
        return UNAVAILABLE
    bits = [hit["status_label"], hit["numero"], hit["source"]]
    label = " — ".join(b for b in bits if b)
    suffix = "" if hit["official"] == "Oui" else " [non officiel / couche locale]"
    return f"{label}{suffix}"


def _relief_label(slope_deg: float, elevation_m: float) -> str:
    if slope_deg < 5:
        return "Plaine"
    if slope_deg < 15:
        return "Plateau"
    return "Escarpé"


def _infer_sector(latitude: float, longitude: float) -> str:
    from compass_core.analysis.national import locate_province

    province, basin = locate_province(latitude, longitude)
    return f"{province} — {basin}"


def evaluate_site(
    latitude: float,
    longitude: float,
    *,
    favorability_path: str | Path | None = None,
    raster_path: str | Path = DEFAULT_RASTER,
    commodity: str = "cu_co",
    hotspot_threshold: float = 0.85,
    demographics_radius_km: float = 10.0,
    deposit_search_km: float = 25.0,
) -> SiteEvaluationReport:
    """
    Génère la fiche d'évaluation complète pour un point GPS.

    Combine favorabilité IA, couches minérales, terrain et démographie.
    """
    point = make_geo_point(latitude, longitude)
    sector = _infer_sector(latitude, longitude)

    fav_path = Path(favorability_path) if favorability_path else resolve_favorability_path()
    favorability: FavorabilityHit
    hotspots: list[HotspotZone] = []
    mineral_prediction = "Non évalué (hors zone IA)"

    if fav_path is not None:
        fav_grid = load_geogrid(fav_path)
        favorability = query_favorability(
            fav_grid, latitude=latitude, longitude=longitude, commodity=commodity
        )
        mineral_prediction = predict_commodity_label(favorability.score, commodity)
        if favorability.in_bounds:
            hotspots = extract_hotspots(
                fav_grid,
                center_utm_x=point.utm_x,
                center_utm_y=point.utm_y,
                threshold=hotspot_threshold,
            )
    else:
        favorability = FavorabilityHit(
            score=0.0,
            row=-1,
            col=-1,
            utm_x=point.utm_x,
            utm_y=point.utm_y,
            latitude=latitude,
            longitude=longitude,
            in_bounds=False,
            predicted_commodity=commodity,
        )

    terrain = TerrainAssessment(
        elevation_m=0.0,
        slope_deg=0.0,
        soil_type="Données indisponibles",
        geology="—",
        water_distance_km=99.0,
        risk_level="inconnu",
        risk_message="Raster multiphysique non disponible.",
        slope_alert=False,
        flood_risk=False,
    )
    demographics = DemographicsAssessment(
        radius_km=demographics_radius_km,
        population_estimate=0,
        density_per_km2=0.0,
        social_impact="inconnu",
        implantation_advice="Générez le dataset Kolwezi.",
        density_class="inconnu",
    )
    coverage = "partielle"
    raster = Path(raster_path)
    if raster.exists():
        dem = load_dem_band(raster)
        terrain = analyze_terrain(dem, utm_x=point.utm_x, utm_y=point.utm_y)
        pop_grid = load_or_create_population_grid(raster)
        demographics = estimate_population_in_buffer(
            pop_grid,
            utm_x=point.utm_x,
            utm_y=point.utm_y,
            radius_km=demographics_radius_km,
        )
        coverage = "complète" if fav_path is not None else "partielle (hors zone IA)"

    layers = load_all_layers()
    nearby = find_nearby_deposits(
        latitude,
        longitude,
        layers=layers,
        radius_km=deposit_search_km,
    )

    return SiteEvaluationReport(
        point=point,
        favorability=favorability,
        mineral_prediction=mineral_prediction,
        terrain=terrain,
        demographics=demographics,
        cadastral_status=_infer_cadastral_status(latitude, longitude),
        nearby_deposits=nearby,
        hotspots=hotspots,
        sector_name=sector,
        data_coverage=coverage,
    )
