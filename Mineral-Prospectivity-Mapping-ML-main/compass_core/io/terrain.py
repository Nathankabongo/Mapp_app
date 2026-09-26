"""MNT / relief — fichiers locaux."""

from __future__ import annotations

from pathlib import Path

DEM_CANDIDATES = (
    Path("data/rdc/national/dem_srtm.tif"),
    Path("data/rdc/kolwezi/stack_multiphysics.tif"),
)


def resolve_dem_path() -> Path | None:
    for path in DEM_CANDIDATES:
        if path.exists():
            return path
    return None
