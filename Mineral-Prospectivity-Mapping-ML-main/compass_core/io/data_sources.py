"""Orchestration des flux de données spatiales (WMS, XYZ, rasters) avec fallback local."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

NATIONAL_DIR = Path("data/rdc/national")
REGIONS_PATH = NATIONAL_DIR / "regions.json"


@dataclass(frozen=True)
class TileSource:
    """Source de tuiles XYZ pour fond de carte."""

    id: str
    label: str
    url: str
    attribution: str


@dataclass(frozen=True)
class RemoteDataSource:
    """Référence à une source de données distante + fallback local."""

    id: str
    label: str
    url: str
    local_fallback: str
    description: str


# Registre des fonds de carte
TILE_SOURCES: dict[str, TileSource] = {
    "osm": TileSource(
        id="osm",
        label="OpenStreetMap",
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attribution="© OpenStreetMap",
    ),
    "esri_satellite": TileSource(
        id="esri_satellite",
        label="ESRI World Imagery",
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attribution="© Esri",
    ),
    "opentopo": TileSource(
        id="opentopo",
        label="OpenTopoMap (terrain)",
        url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attribution="© OpenStreetMap, © OpenTopoMap (CC-BY-SA)",
    ),
}

# Registre des sources métier (offline-first)
REMOTE_SOURCES: dict[str, RemoteDataSource] = {
    "cami_cadastre": RemoteDataSource(
        id="cami_cadastre",
        label="Cadastre minier CAMI",
        url="https://rdc.mines-rdc.cd/",
        local_fallback="data/rdc/atlas/cadastre_permis.gpkg",
        description="Permis de recherche et concessions minières",
    ),
    "usgs_mrds": RemoteDataSource(
        id="usgs_mrds",
        label="USGS MRDS — Gisements",
        url="https://mrdata.usgs.gov/mrds/",
        local_fallback="data/rdc/atlas/",
        description="Mineral Resources Data System",
    ),
    "usgs_srtm": RemoteDataSource(
        id="usgs_srtm",
        label="USGS SRTM 30m (MNT)",
        url="https://earthexplorer.usgs.gov/",
        local_fallback="data/rdc/kolwezi/stack_multiphysics.tif",
        description="Modèle numérique de terrain",
    ),
    "worldpop": RemoteDataSource(
        id="worldpop",
        label="WorldPop RDC",
        url="https://www.worldpop.org/geodata/country?iso=COD",
        local_fallback="data/rdc/atlas/population_density.npy",
        description="Densité de population 100m",
    ),
}


def load_regions(path: Path = REGIONS_PATH) -> dict:
    """Charge le référentiel national provinces / bassins miniers."""
    if not path.exists():
        return {
            "map_default": {"latitude": -4.0375, "longitude": 21.7587, "zoom": 5},
            "provinces": [],
            "mining_basins": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_local_path(source_id: str) -> Path | None:
    """Retourne le chemin local de fallback pour une source."""
    source = REMOTE_SOURCES.get(source_id)
    if source is None:
        return None
    path = Path(source.local_fallback)
    return path if path.exists() else None


def list_available_sources() -> list[dict[str, str]]:
    """Liste les sources avec statut local disponible."""
    rows = []
    for source in REMOTE_SOURCES.values():
        local = Path(source.local_fallback)
        available = local.exists()
        rows.append(
            {
                "id": source.id,
                "label": source.label,
                "remote": source.url,
                "local": source.local_fallback,
                "status": "local OK" if available else "remote only",
            }
        )
    return rows
