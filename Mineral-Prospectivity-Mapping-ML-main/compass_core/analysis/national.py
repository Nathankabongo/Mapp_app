"""Module national — KPIs, provinces, filtres territoriaux RDC."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np

from compass_core.analysis.favorability import load_geogrid
from compass_core.analysis.mineral_layers import load_all_layers, load_cadastre
from compass_core.analysis.site_evaluation import resolve_favorability_path
from compass_core.io.data_sources import load_regions

COMMODITY_FILTER_MAP: dict[str, list[str]] = {
    "Cu-Co": ["cu_co"],
    "Lithium": ["li"],
    "Or (Au)": ["au"],
    "3T (Coltan)": ["coltan"],
    "Diamant": ["diamond"],
    "Germanium": ["cu_co"],
}


@dataclass
class NationalKPIs:
    """Indicateurs nationaux du dashboard exécutif."""

    total_sites: int
    mineral_occurrences: int
    high_favorability: int
    active_permits: int
    active_projects: int
    risk_alerts: int
    province_filter: str


def locate_province(latitude: float, longitude: float) -> tuple[str, str]:
    """Identifie province et bassin minier à partir de coordonnées."""
    from compass_core.minerals.zone_knowledge import normalize_province_name

    regions = load_regions()
    province = "RDC"
    for entry in regions.get("provinces", []):
        min_lon, min_lat, max_lon, max_lat = entry["bbox"]
        if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
            province = normalize_province_name(entry["name"])
            break

    basin = "National"
    for basin_entry in regions.get("mining_basins", []):
        codes = [normalize_province_name(p) for p in basin_entry.get("provinces", [])]
        if province in codes:
            basin = basin_entry["label"]
            break
    return province, basin


def map_view_for_selection(
    province: str,
    regions: dict | None = None,
) -> tuple[tuple[float, float], int]:
    """Centre et zoom carte selon province ou vue nationale."""
    regions = regions or load_regions()
    default = regions.get("map_default", {})
    center = (default.get("latitude", -4.0375), default.get("longitude", 21.7587))
    zoom = default.get("zoom", 5)

    if province and province != "Toute la RDC":
        for basin in regions.get("mining_basins", []):
            if province in basin.get("provinces", []):
                c = basin.get("center", center)
                return (c[0], c[1]), basin.get("zoom", 7)
        for entry in regions.get("provinces", []):
            if entry["name"] == province:
                bbox = entry["bbox"]
                center = ((bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2)
                return center, 7
    return center, zoom


def filter_layers_by_commodities(
    layers: dict[str, gpd.GeoDataFrame],
    commodity_labels: list[str],
) -> dict[str, gpd.GeoDataFrame]:
    """Filtre les couches selon les libellés multi-substances."""
    if not commodity_labels:
        return layers
    codes: set[str] = set()
    for label in commodity_labels:
        codes.update(COMMODITY_FILTER_MAP.get(label, []))
    return {k: v for k, v in layers.items() if k in codes}


def compute_national_kpis(
    *,
    province: str = "Toute la RDC",
    commodity_labels: list[str] | None = None,
    atlas_dir: Path = Path("data/rdc/atlas"),
) -> NationalKPIs:
    """Calcule les 4 KPIs du header dashboard."""
    province_filter = None if province == "Toute la RDC" else province
    layers = load_all_layers(atlas_dir=atlas_dir, province=province_filter)
    if commodity_labels:
        layers = filter_layers_by_commodities(layers, commodity_labels)

    total_sites = sum(len(gdf) for gdf in layers.values())
    mineral_occurrences = total_sites

    high_fav = 0
    fav_path = resolve_favorability_path()
    if fav_path is not None:
        try:
            grid = load_geogrid(fav_path)
            high_fav = int((grid.values >= 0.85).sum())
        except Exception:
            high_fav = sum(
                int((gdf.get("Value", 1) == 1).sum()) for gdf in layers.values() if "Value" in gdf.columns
            )
    else:
        high_fav = sum(
            int((gdf.get("Value", 1) == 1).sum()) for gdf in layers.values() if "Value" in gdf.columns
        )

    active_permits = 0
    cadastre = load_cadastre(atlas_dir)
    if cadastre is not None and not cadastre.empty:
        active = cadastre[cadastre["statut"].isin(["exploitation", "recherche", "PE", "PR"])]
        if province_filter and "province" in active.columns:
            active = active[active["province"] == province_filter]
        active_permits = len(active)

    active_projects = 0
    for gdf in layers.values():
        if "status" in gdf.columns:
            active_projects += int(gdf["status"].isin(["exploitation", "recherche"]).sum())

    risk_alerts = 0
    for gdf in layers.values():
        if "status" in gdf.columns:
            risk_alerts += int(gdf["status"].isin(["artisanal", "abandonne"]).sum())

    return NationalKPIs(
        total_sites=total_sites,
        mineral_occurrences=mineral_occurrences,
        high_favorability=high_fav,
        active_permits=active_permits,
        active_projects=active_projects,
        risk_alerts=risk_alerts,
        province_filter=province,
    )


def list_province_options() -> list[str]:
    """Options du sélecteur provincial — toutes les provinces RDC."""
    from compass_core.minerals.zone_knowledge import list_all_provinces

    return ["Toute la RDC", *list_all_provinces()]


def commodity_filter_options() -> list[str]:
    """Libellés du filtre multi-substances."""
    return list(COMMODITY_FILTER_MAP.keys())


def primary_commodity_code(commodity_labels: list[str]) -> str:
    """Retourne le code couche principal pour l'évaluation IA."""
    for label in commodity_labels:
        codes = COMMODITY_FILTER_MAP.get(label)
        if codes:
            return codes[0]
    return "cu_co"
