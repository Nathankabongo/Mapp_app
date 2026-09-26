"""Tests de l'atlas minier multi-minéraux."""

from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

from compass_core.analysis.atlas_catalog import load_catalog
from compass_core.analysis.atlas_import import import_cami_layer, normalize_gdf
from compass_core.analysis.mineral_layers import (
    REFERENCE_DEPOSITS,
    find_nearby_deposits,
    generate_atlas_layers,
    list_provinces,
)


def test_catalog_loads() -> None:
    catalog = load_catalog()
    assert "cu_co" in catalog.layers
    assert catalog.layers["cu_co"].label == "Cuivre-Cobalt"


def test_generate_atlas_enriched(tmp_path: Path) -> None:
    created = generate_atlas_layers(tmp_path, points_per_layer=10, seed=1)
    assert "cu_co" in created
    assert "cadastre" in created
    gdf = gpd.read_file(created["cu_co"])
    assert "name" in gdf.columns
    assert "province" in gdf.columns
    assert "status" in gdf.columns
    assert len(gdf) >= len(REFERENCE_DEPOSITS["cu_co"])


def test_import_cami_layer(tmp_path: Path) -> None:
    generate_atlas_layers(tmp_path, points_per_layer=5, seed=2)
    source = tmp_path / "external.gpkg"
    ext = gpd.GeoDataFrame(
        {
            "nom": ["Gisement test"],
            "Province": ["Lualaba"],
            "statut": ["recherche"],
            "geometry": [Point(25.5, -10.7)],
        },
        crs="EPSG:4326",
    )
    ext.to_file(source, driver="GPKG")
    report = import_cami_layer(source, "cu_co", output_dir=tmp_path, overwrite=True)
    assert report.success
    assert report.feature_count == 1


def test_find_nearby_named_deposits(tmp_path: Path) -> None:
    generate_atlas_layers(tmp_path, points_per_layer=10, seed=3)
    nearby = find_nearby_deposits(-10.595, 26.178, radius_km=50, atlas_dir=tmp_path)
    names = [d.name for d in nearby]
    assert any("Tenke" in n for n in names)


def test_list_provinces(tmp_path: Path) -> None:
    generate_atlas_layers(tmp_path, points_per_layer=8, seed=4)
    provinces = list_provinces(tmp_path)
    assert "Lualaba" in provinces
