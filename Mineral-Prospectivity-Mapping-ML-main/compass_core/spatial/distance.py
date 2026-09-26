"""Distances spatiales (haversine + shapely)."""

from __future__ import annotations

import math

import geopandas as gpd
from shapely.geometry import Point


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def nearest_feature_km(
    latitude: float,
    longitude: float,
    gdf: gpd.GeoDataFrame | None,
    *,
    name_field: str = "name",
) -> tuple[float | None, str]:
    """Distance km au plus proche objet. None si couche absente."""
    if gdf is None or gdf.empty:
        return None, ""
    wgs = gdf.to_crs(epsg=4326)
    point = Point(longitude, latitude)
    best = None
    label = ""
    for _, row in wgs.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        nearest = geom if geom.geom_type == "Point" else geom.representative_point()
        dist = haversine_km(latitude, longitude, nearest.y, nearest.x)
        if best is None or dist < best:
            best = dist
            label = str(row.get(name_field, "") or "")
    return best, label
