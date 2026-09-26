"""Chargement des couches selon les filtres de session."""

from __future__ import annotations

from compass_core.analysis.atlas_catalog import load_catalog
from compass_core.analysis.mineral_layers import load_all_layers
from compass_core.analysis.national import filter_layers_by_commodities, map_view_for_selection


def load_workspace(filters: dict):
    province = filters.get("province", "Toute la RDC")
    province_filter = None if province == "Toute la RDC" else province
    catalog = load_catalog()
    layers_raw = load_all_layers(catalog.available_codes(), province=province_filter)
    layers = filter_layers_by_commodities(layers_raw, filters.get("minerai") or [])
    statut = filters.get("statut", "Tous")
    if statut and statut != "Tous":
        filtered = {}
        for code, gdf in layers.items():
            if "status" in gdf.columns:
                sub = gdf[gdf["status"] == statut]
                if not sub.empty:
                    filtered[code] = sub
            else:
                filtered[code] = gdf
        layers = filtered
    territoire = (filters.get("territoire") or "").strip()
    if territoire:
        filtered = {}
        for code, gdf in layers.items():
            if "territoire" in gdf.columns:
                sub = gdf[gdf["territoire"].astype(str).str.contains(territoire, case=False, na=False)]
                if not sub.empty:
                    filtered[code] = sub
            else:
                filtered[code] = gdf
        layers = filtered
    center, zoom = map_view_for_selection(province)
    return layers, list(layers.keys()) or catalog.available_codes(), center, zoom
