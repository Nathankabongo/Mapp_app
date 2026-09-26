"""Tests du générateur de données d'exemple."""

from pathlib import Path

from compass_core.data.sample_generator import (
    check_dataset_inventory,
    generate_kolwezi_sample_dataset,
)


def test_generate_kolwezi_sample_dataset(tmp_path: Path) -> None:
    report = generate_kolwezi_sample_dataset(tmp_path, rows=32, cols=32, n_deposits=20, seed=7)
    assert report.raster_path.exists()
    assert report.deposits_path.exists()
    assert report.training_path.exists()
    assert report.testing_path.exists()
    assert report.metadata_path.exists()
    assert report.n_deposits == 20


def test_check_dataset_inventory(tmp_path: Path) -> None:
    before = check_dataset_inventory(tmp_path)
    assert all(not present for _, _, present in before)

    generate_kolwezi_sample_dataset(tmp_path, rows=24, cols=24, n_deposits=12, seed=1)
    after = check_dataset_inventory(tmp_path)
    core = [present for label, _, present in after if "Raster" in label or "Gisements" in label]
    assert all(core)
