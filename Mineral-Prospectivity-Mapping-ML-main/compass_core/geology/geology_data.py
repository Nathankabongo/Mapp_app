"""Données géologiques locales."""

from __future__ import annotations

from pathlib import Path

from compass_core.constants import UNAVAILABLE
from compass_core.io.geological import load_faults, load_geology


def geology_summary(latitude: float, longitude: float) -> dict:
    gdf = load_geology()
    faults = load_faults()
    return {
        "latitude": latitude,
        "longitude": longitude,
        "formations": "couche locale" if gdf is not None else UNAVAILABLE,
        "faults": "couche locale" if faults is not None else UNAVAILABLE,
        "lithology": UNAVAILABLE,
        "data_class": "open" if gdf is not None else "unavailable",
        "path_geology": str(Path("data/rdc/national/geology.gpkg")) if (Path("data/rdc/national/geology.gpkg").exists()) else None,
    }
