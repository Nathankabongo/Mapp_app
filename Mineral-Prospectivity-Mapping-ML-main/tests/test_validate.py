"""Tests de validation de configuration."""

from pathlib import Path

from compass_core.config.validate import validate_config

CONFIG_DEMO = Path(__file__).resolve().parents[1] / "config" / "config_demo.json"
CONFIG_KOLWEZI = Path(__file__).resolve().parents[1] / "config" / "config_rdc_kolwezi.json"


def test_validate_demo_config() -> None:
    report = validate_config(CONFIG_DEMO)
    assert report.valid
    assert report.config is not None
    assert report.config.model.name == "woe"


def test_validate_kolwezi_warns_missing_files() -> None:
    report = validate_config(CONFIG_KOLWEZI, check_files=True)
    assert report.valid
    assert len(report.warnings) >= 1
