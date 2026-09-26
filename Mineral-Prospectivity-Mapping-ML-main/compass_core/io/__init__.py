"""Compass IO — orchestration des flux spatiaux."""

from compass_core.io.data_sources import (
    REMOTE_SOURCES,
    TILE_SOURCES,
    load_regions,
    resolve_local_path,
)

__all__ = [
    "REMOTE_SOURCES",
    "TILE_SOURCES",
    "load_regions",
    "resolve_local_path",
]
