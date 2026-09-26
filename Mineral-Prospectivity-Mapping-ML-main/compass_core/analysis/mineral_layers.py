"""Couches cartographiques multi-minéraux RDC (atlas)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import Point, box

from compass_core.analysis.atlas_catalog import (
    ATLAS_DIR,
    AtlasInventory,
    MineralLayerMeta,
    load_catalog,
)
from compass_core.analysis.coordinates import wgs84_to_utm, utm_to_wgs84

# Rétrocompatibilité — alimenté depuis le catalogue
MINERAL_LAYERS: dict[str, dict[str, str]] = {}


def _sync_mineral_layers_dict(inventory: AtlasInventory) -> None:
    MINERAL_LAYERS.clear()
    for code, meta in inventory.layers.items():
        MINERAL_LAYERS[code] = {
            "label": meta.label,
            "region": meta.geological_belt,
            "filename": meta.filename,
            "color": meta.color,
        }


# Gisements de référence (lat, lon) — positions approximatives publiques
REFERENCE_DEPOSITS: dict[str, list[dict]] = {
    "cu_co": [
        {"name": "Tenke-Fungurume", "lat": -10.595, "lon": 26.178, "province": "Lualaba", "status": "exploitation", "deposit_type": "stratiforme", "formation": "Groupe de Roan"},
        {"name": "Mutanda", "lat": -10.781, "lon": 26.437, "province": "Lualaba", "status": "exploitation", "deposit_type": "stratiforme", "formation": "R.A.T."},
        {"name": "Kamoto", "lat": -10.850, "lon": 25.483, "province": "Lualaba", "status": "exploitation", "deposit_type": "filons", "formation": "Mines de Kambove"},
        {"name": "Kolwezi centre", "lat": -10.716, "lon": 25.465, "province": "Lualaba", "status": "recherche", "deposit_type": "stratiforme", "formation": "Dilala"},
        {"name": "Kipushi", "lat": -11.761, "lon": 27.233, "province": "Haut-Katanga", "status": "exploitation", "deposit_type": "filons", "formation": "Zn-Pb-Cu"},
    ],
    "li": [
        {"name": "Manono-Kitotolo", "lat": -7.283, "lon": 27.400, "province": "Tanganyika", "status": "recherche", "deposit_type": "pegmatite", "formation": "Pegmatite LCT"},
        {"name": "Mobambo", "lat": -7.150, "lon": 27.550, "province": "Tanganyika", "status": "prospect", "deposit_type": "pegmatite", "formation": "Pegmatite"},
    ],
    "au": [
        {"name": "Kibali", "lat": 3.120, "lon": 29.450, "province": "Haut-Uélé", "status": "exploitation", "deposit_type": "filons", "formation": "Birimien"},
        {"name": "Mongbwalu", "lat": 2.170, "lon": 30.980, "province": "Ituri", "status": "artisanal", "deposit_type": "filons", "formation": "Archéen"},
        {"name": "Kamituga", "lat": -3.080, "lon": 28.170, "province": "Sud-Kivu", "status": "artisanal", "deposit_type": "filons", "formation": "Kibaran"},
        {"name": "Durba", "lat": 3.117, "lon": 28.983, "province": "Haut-Uélé", "status": "exploitation", "deposit_type": "filons", "formation": "Greenstone"},
    ],
    "coltan": [
        {"name": "Rubaya", "lat": -1.550, "lon": 28.950, "province": "Nord-Kivu", "status": "artisanal", "deposit_type": "pegmatite", "formation": "Pegmatite 3T"},
        {"name": "Numbi", "lat": -1.783, "lon": 28.617, "province": "Sud-Kivu", "status": "artisanal", "deposit_type": "alluvionnaire", "formation": "Placers"},
        {"name": "Kalehe", "lat": -2.500, "lon": 28.750, "province": "Sud-Kivu", "status": "recherche", "deposit_type": "pegmatite", "formation": "Pegmatite"},
    ],
    "diamond": [
        {"name": "Mbuji-Mayi", "lat": -6.150, "lon": 23.600, "province": "Kasaï Oriental", "status": "exploitation", "deposit_type": "kimberlite", "formation": "Kimberlite"},
        {"name": "Tshikapa", "lat": -6.417, "lon": 20.800, "province": "Kasaï", "status": "artisanal", "deposit_type": "alluvionnaire", "formation": "Placers"},
        {"name": "Bakwanga (MIBA)", "lat": -6.133, "lon": 23.583, "province": "Kasaï Oriental", "status": "exploitation", "deposit_type": "kimberlite", "formation": "Kimberlite"},
    ],
}

STATUS_LABELS = {
    "exploitation": "En exploitation",
    "recherche": "Permis de recherche",
    "artisanal": "Orpaillage artisanal",
    "prospect": "Prospect",
    "abandonne": "Abandonné",
}


@dataclass
class NearbyDeposit:
    """Gisement connu à proximité du point ciblé."""

    commodity: str
    label: str
    distance_km: float
    value: int
    latitude: float
    longitude: float
    name: str = ""
    province: str = ""
    status: str = ""
    deposit_type: str = ""


def get_catalog() -> AtlasInventory:
    """Charge le catalogue et synchronise MINERAL_LAYERS."""
    inventory = load_catalog()
    _sync_mineral_layers_dict(inventory)
    return inventory


def layer_path(commodity: str, atlas_dir: Path = ATLAS_DIR) -> Path:
    """Chemin du fichier GeoPackage pour une commodité."""
    _ensure_mineral_layers_synced()
    inventory = load_catalog()
    meta = inventory.layers[commodity]
    return atlas_dir / meta.filename


def load_mineral_layer(commodity: str, atlas_dir: Path = ATLAS_DIR) -> gpd.GeoDataFrame | None:
    """Charge une couche vectorielle si elle existe."""
    path = layer_path(commodity, atlas_dir)
    if not path.exists():
        fallback = Path("data/rdc/kolwezi/deposits_cu_co.gpkg")
        if commodity == "cu_co" and fallback.exists():
            return gpd.read_file(fallback)
        return None
    return gpd.read_file(path)


def load_all_layers(
    commodities: list[str] | None = None,
    atlas_dir: Path = ATLAS_DIR,
    *,
    province: str | None = None,
) -> dict[str, gpd.GeoDataFrame]:
    """Charge toutes les couches minérales disponibles, avec filtre provincial optionnel."""
    _ensure_mineral_layers_synced()
    inventory = load_catalog()
    keys = commodities or inventory.available_codes()
    layers: dict[str, gpd.GeoDataFrame] = {}
    for code in keys:
        gdf = load_mineral_layer(code, atlas_dir)
        if gdf is None:
            continue
        if province and "province" in gdf.columns:
            filtered = gdf[gdf["province"].str.lower() == province.lower()]
            if not filtered.empty:
                layers[code] = filtered
        else:
            layers[code] = gdf
    return layers


def find_nearby_deposits(
    latitude: float,
    longitude: float,
    *,
    layers: dict[str, gpd.GeoDataFrame] | None = None,
    radius_km: float = 25.0,
    atlas_dir: Path = ATLAS_DIR,
) -> list[NearbyDeposit]:
    """Liste les gisements connus dans un rayon autour du point."""
    _ensure_mineral_layers_synced()
    inventory = load_catalog()
    if layers is None:
        layers = load_all_layers(atlas_dir=atlas_dir)

    utm_x, utm_y = wgs84_to_utm(latitude, longitude)
    radius_m = radius_km * 1000
    results: list[NearbyDeposit] = []

    for commodity, gdf in layers.items():
        if gdf.empty:
            continue
        meta = inventory.layers[commodity]
        projected = gdf.to_crs(epsg=32733)
        for _, row in projected.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            dist_m = float(np.hypot(geom.x - utm_x, geom.y - utm_y))
            if dist_m <= radius_m:
                lat, lon = utm_to_wgs84(geom.x, geom.y)
                results.append(
                    NearbyDeposit(
                        commodity=commodity,
                        label=meta.label,
                        distance_km=dist_m / 1000,
                        value=int(row.get("Value", 1)),
                        latitude=lat,
                        longitude=lon,
                        name=str(row.get("name", "")),
                        province=str(row.get("province", "")),
                        status=str(row.get("status", "")),
                        deposit_type=str(row.get("deposit_type", "")),
                    )
                )

    results.sort(key=lambda deposit: deposit.distance_km)
    return results


def _build_deposit_records(
    commodity: str,
    meta: MineralLayerMeta,
    rng: np.random.Generator,
    *,
    points_per_layer: int,
) -> list[dict]:
    """Construit des enregistrements : gisements nommés + points aléatoires."""
    records: list[dict] = []
    refs = REFERENCE_DEPOSITS.get(commodity, [])

    for ref in refs:
        x, y = wgs84_to_utm(ref["lat"], ref["lon"])
        records.append(
            {
                "geometry": Point(x, y),
                "name": ref["name"],
                "Value": 1,
                "commodity": commodity,
                "province": ref.get("province", ""),
                "status": ref.get("status", "prospect"),
                "deposit_type": ref.get("deposit_type", ""),
                "geological_formation": ref.get("formation", ""),
                "source": "reference_public",
                "cami_ref": f"REF-{commodity.upper()}-{len(records)+1:03d}",
            }
        )

    remaining = max(0, points_per_layer - len(records))
    if refs:
        center_lat = float(np.mean([r["lat"] for r in refs]))
        center_lon = float(np.mean([r["lon"] for r in refs]))
    else:
        center_lat, center_lon = -4.0, 24.0
    center_x, center_y = wgs84_to_utm(center_lat, center_lon)

    for i in range(remaining):
        offset_x = rng.normal(0, 25000)
        offset_y = rng.normal(0, 25000)
        x, y = center_x + offset_x, center_y + offset_y
        value = int(rng.random() > 0.35)
        statuses = list(STATUS_LABELS.keys())
        records.append(
            {
                "geometry": Point(x, y),
                "name": f"{meta.label} prospect {i+1}",
                "Value": value,
                "commodity": commodity,
                "province": meta.provinces[0] if meta.provinces else "",
                "status": rng.choice(statuses),
                "deposit_type": rng.choice(["stratiforme", "pegmatite", "filons", "alluvionnaire"]),
                "geological_formation": meta.geological_belt,
                "source": "atlas_demo",
                "cami_ref": f"DEMO-{commodity.upper()}-{i+1:03d}",
            }
        )
    return records


def generate_cadastre_layer(
    atlas_dir: Path,
    layers: dict[str, gpd.GeoDataFrame],
    *,
    seed: int = 42,
) -> Path:
    """Génère une couche polygonale de permis miniers (démonstration, non CAMI)."""
    rng = np.random.default_rng(seed)
    catalog_path = atlas_dir / "catalog.json"
    filename = "cadastre_permis.gpkg"
    if catalog_path.exists():
        cadastre_meta = json.loads(catalog_path.read_text()).get("cadastre", {})
        filename = cadastre_meta.get("filename", filename)

    records: list[dict] = []
    status_cycle = ["recherche", "exploitation", "recherche", "prospect"]

    for code, gdf in layers.items():
        if gdf.empty:
            continue
        wgs = gdf.to_crs(epsg=4326)
        for idx, row in wgs.iterrows():
            if row.geometry is None:
                continue
            lat, lon = row.geometry.y, row.geometry.x
            half = 0.08 + rng.random() * 0.15
            poly = box(lon - half, lat - half, lon + half, lat + half)
            records.append(
                {
                    "geometry": poly,
                    "numero_permis": f"DEMO-{code.upper()}-{idx:04d}",
                    "statut": status_cycle[idx % len(status_cycle)],
                    "commodity": code,
                    "titulaire": "",
                    "province": row.get("province", ""),
                    "source": "cadastre_demo",
                    "data_class": "demo",
                    "official": False,
                }
            )

    gdf_out = gpd.GeoDataFrame(records, crs="EPSG:4326")
    out = atlas_dir / filename
    gdf_out.to_file(out, driver="GPKG")
    return out


def generate_atlas_layers(
    atlas_dir: str | Path = ATLAS_DIR,
    *,
    points_per_layer: int = 30,
    seed: int = 42,
    include_cadastre: bool = True,
) -> dict[str, Path]:
    """
    Génère les couches GeoPackage de l'atlas multi-minéraux RDC.

    Inclut gisements de référence nommés + points synthétiques + cadastre démo.
    """
    atlas_path = Path(atlas_dir)
    atlas_path.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    inventory = get_catalog()
    created: dict[str, Path] = {}
    loaded_layers: dict[str, gpd.GeoDataFrame] = {}

    for code, meta in inventory.layers.items():
        records = _build_deposit_records(code, meta, rng, points_per_layer=points_per_layer)
        gdf = gpd.GeoDataFrame(records, crs="EPSG:32733")
        out = atlas_path / meta.filename
        gdf.to_file(out, driver="GPKG")
        created[code] = out
        loaded_layers[code] = gdf

    if include_cadastre:
        cadastre_path = generate_cadastre_layer(atlas_path, loaded_layers, seed=seed)
        created["cadastre"] = cadastre_path

    return created


def load_cadastre(atlas_dir: Path = ATLAS_DIR) -> gpd.GeoDataFrame | None:
    """Charge la couche cadastrale CAMI si disponible."""
    catalog_file = atlas_dir / "catalog.json"
    if not catalog_file.exists():
        return None
    cadastre_meta = json.loads(catalog_file.read_text()).get("cadastre", {})
    path = atlas_dir / cadastre_meta.get("filename", "cadastre_permis.gpkg")
    if not path.exists():
        return None
    return gpd.read_file(path)


def list_provinces(atlas_dir: Path = ATLAS_DIR) -> list[str]:
    """Liste les provinces présentes dans l'atlas."""
    provinces: set[str] = set()
    for gdf in load_all_layers(atlas_dir=atlas_dir).values():
        if "province" in gdf.columns:
            provinces.update(gdf["province"].dropna().unique())
    return sorted(provinces)


# Initialise MINERAL_LAYERS à la première utilisation (évite effets de bord à l'import)
def _ensure_mineral_layers_synced() -> None:
    if not MINERAL_LAYERS:
        _sync_mineral_layers_dict(load_catalog())
