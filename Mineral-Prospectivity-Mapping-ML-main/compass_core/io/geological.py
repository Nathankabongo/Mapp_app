"""Couches geologiques — fichiers locaux uniquement."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

GEOLOGY_CANDIDATES = (
    Path("data/rdc/national/geology.gpkg"),
    Path("data/rdc/national/faults.gpkg"),
)


def load_geology() -> gpd.GeoDataFrame | None:
    path = Path("data/rdc/national/geology.gpkg")
    if not path.exists():
        return None
    return gpd.read_file(path)


def load_faults() -> gpd.GeoDataFrame | None:
    path = Path("data/rdc/national/faults.gpkg")
    if not path.exists():
        return None
    return gpd.read_file(path)
