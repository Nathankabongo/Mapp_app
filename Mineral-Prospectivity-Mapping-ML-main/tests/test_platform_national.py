"""Tests plateforme nationale — vérité des données et scoring."""

from pathlib import Path

from compass_core.analysis.site_evaluation import evaluate_site
from compass_core.constants import UNAVAILABLE
from compass_core.io.cadastral import lookup_permit
from compass_core.models.prospectivity import classify_score
from compass_core.models.risk import score_risk
from compass_core.validation.data_quality import system_health


def test_cadastral_lookup_never_invents_status() -> None:
    hit = lookup_permit(0.0, 0.0)
    assert hit["official"] == "Non"
    assert UNAVAILABLE in hit["status_label"] or hit["data_class"] in {"unavailable", "demo", "open", "official"}


def test_evaluate_site_does_not_fabricate_permit_in_empty_ocean() -> None:
    report = evaluate_site(0.0, 0.0)
    assert UNAVAILABLE in report.cadastral_status or "non officiel" in report.cadastral_status.lower() or "demo" in report.cadastral_status.lower()
    assert "Zone libre" not in report.cadastral_status
    assert "consultation CAMI requise" not in report.cadastral_status


def test_favorability_out_of_bounds_is_unavailable() -> None:
    info = classify_score(0.87, in_bounds=False)
    assert info["score_pct"] is None
    assert "prédictif" in str(info["disclaimer"]).lower() or "predictif" in str(info["disclaimer"]).lower() or "Indice" in str(info["disclaimer"])


def test_risk_rules_slope() -> None:
    high = score_risk(slope_deg=30.0, water_distance_km=5.0, density_per_km2=10.0)
    assert high.geotech == "élevé"
    assert any("pente" in m.lower() for m in high.messages)
    assert "réglementaire" in high.disclaimer or "reglementaire" in high.disclaimer


def test_system_health_keys() -> None:
    health = system_health()
    assert "last_sync" in health
    assert "missing" in health
    assert health["offline_note"]


def test_risk_config_exists() -> None:
    assert Path("config/risk_rules.json").exists()
