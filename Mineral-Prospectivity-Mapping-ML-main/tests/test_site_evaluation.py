"""Tests du module d'aide à la décision (ciblage GPS)."""

from pathlib import Path

import pytest

from compass_core.analysis.coordinates import make_geo_point, wgs84_to_utm
from compass_core.analysis.favorability import load_geogrid, query_favorability
from compass_core.analysis.mineral_layers import generate_atlas_layers
from compass_core.analysis.site_evaluation import evaluate_site, resolve_favorability_path


def test_wgs84_utm_roundtrip() -> None:
    lat, lon = -10.716, 25.465
    x, y = wgs84_to_utm(lat, lon)
    point = make_geo_point(lat, lon)
    assert abs(point.utm_x - x) < 1
    assert abs(point.utm_y - y) < 1


def test_query_favorability_on_sample() -> None:
    fav_path = resolve_favorability_path()
    if fav_path is None:
        pytest.skip("Carte de favorabilité non générée")
    grid = load_geogrid(fav_path)
    hit = query_favorability(grid, latitude=-10.716, longitude=25.465)
    assert hit.in_bounds
    assert 0.0 <= hit.score <= 1.0


def test_evaluate_site_kolwezi() -> None:
    if resolve_favorability_path() is None:
        pytest.skip("Carte de favorabilité non générée")
    if not Path("data/rdc/kolwezi/stack_multiphysics.tif").exists():
        pytest.skip("Raster Kolwezi non généré")

    report = evaluate_site(-10.716, 25.465, demographics_radius_km=10)
    assert report.favorability.in_bounds
    assert len(report.to_summary_rows()) >= 6
    assert report.data_coverage == "complète"


def test_generate_atlas_layers(tmp_path: Path) -> None:
    created = generate_atlas_layers(tmp_path, points_per_layer=5, seed=1)
    assert len(created) == 6
    assert "cadastre" in created
    for path in created.values():
        assert path.exists()
