"""Tests moteur prospectivité / CAMI / registre."""

from compass_core.api.registry import build_registry
from compass_core.constants import EVIDENCE_CHAIN
from compass_core.mining.cami import verified_concession_count
from compass_core.prospectivity.prediction import run_prospectivity
from compass_core.decision.engine import decide
from compass_core.gis.crs import resolve_metric_crs, crs_strategy_doc


def test_verified_concessions_zero_without_official() -> None:
    assert verified_concession_count() == 0


def test_registry_has_categories() -> None:
    reg = build_registry()
    assert len(reg) >= 8
    cats = {s.category for s in reg}
    assert "IMAGERIE SATELLITE" in cats
    assert any(s.id == "cami" for s in reg)


def test_evidence_chain() -> None:
    assert len(EVIDENCE_CHAIN) == 5
    assert EVIDENCE_CHAIN[0][0] == "observation"
    assert EVIDENCE_CHAIN[-1][0] == "confirmed"


def test_crs_auto_zone() -> None:
    # Kolwezi ~25.5E → UTM 35S
    crs = resolve_metric_crs(-10.7, 25.5)
    assert crs.epsg == 32735
    # Kinshasa ~15E → UTM 33S
    crs_w = resolve_metric_crs(-4.3, 15.3)
    assert crs_w.epsg == 32733
    assert "4326" in crs_strategy_doc()


def test_prospectivity_kolwezi_cuivre() -> None:
    r = run_prospectivity(zone="Kolwezi", mineral="cuivre")
    assert r.country == "RDC"
    assert r.disclaimer
    # Si raster présent : in_bounds possible ; sinon score None
    if r.in_bounds:
        assert r.prospectivity_pct is not None
        assert r.model_confidence_pct > 0
    else:
        assert r.prospectivity_pct is None
        assert "non évalué" in r.prospectivity_level.lower() or "hors" in r.prospectivity_level.lower()


def test_prospectivity_wrong_mineral_no_fake_score() -> None:
    r = run_prospectivity(zone="Kolwezi", mineral="lithium")
    # Ne doit pas renvoyer un faux score Cu-Co pour le lithium
    if r.raster_path is None:
        assert r.prospectivity_pct is None


def test_decision_report() -> None:
    d = decide(zone="Kolwezi", mineral="cuivre")
    assert d.decision
    assert d.cami_verified == 0
    assert len(d.evidence_chain) == 5
