"""Utilitaires géométriques légers."""

from __future__ import annotations

from shapely.geometry import Point, mapping


def point_geojson(latitude: float, longitude: float, props: dict | None = None) -> dict:
    return {
        "type": "Feature",
        "geometry": mapping(Point(longitude, latitude)),
        "properties": props or {},
    }
