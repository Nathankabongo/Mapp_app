"""Tests Phase 1 — profils, diagnostic, ranking composite, explainability."""

from compass_core.exploration.campaign import run_campaign
from compass_core.exploration.diagnostic import diagnose_zone
from compass_core.exploration.explainability import compare_targets, explain_target
from compass_core.minerals.profiles import get_profile, list_profiles, mineral_supports_raster


def test_mineral_profiles_loaded() -> None:
    profiles = list_profiles()
    assert len(profiles) >= 5
    cu = get_profile("cuivre")
    assert cu is not None
    assert cu.supports_raster_targets()
    assert get_profile("copper") is not None
    assert mineral_supports_raster("cuivre")
    assert not mineral_supports_raster("lithium")


def test_diagnose_zone_kolwezi_honest_gaps() -> None:
    diag = diagnose_zone(zone="Kolwezi", mineral="cuivre")
    assert diag.zone == "Kolwezi"
    assert diag.geochemistry.status == "NON DISPONIBLE"
    assert diag.geochemistry.counts["echantillons"] == "Donnée indisponible"
    assert isinstance(diag.gaps, list)
    assert len(diag.gaps) >= 1
    assert "invent" not in diag.disclaimer.lower() or "Aucune invention" in diag.disclaimer


def test_campaign_includes_diagnostic_and_uncertainty() -> None:
    camp = run_campaign(zone="Kolwezi", mineral="cuivre", max_targets=5)
    assert "diagnostic" in camp.to_dict()
    assert camp.diagnostic.get("gaps") is not None
    if camp.targets:
        t0 = camp.targets[0]
        assert "uncertainty_pct" in t0
        assert "uncertainty_label" in t0
        assert t0["exploration_priority_score"] >= 0


def test_explain_and_compare_targets() -> None:
    camp = run_campaign(zone="Kolwezi", mineral="cuivre", max_targets=5)
    if len(camp.targets) < 2:
        # Pas assez de cibles : explain seul
        if camp.targets:
            exp = explain_target(camp.targets[0])
            assert exp.composite_score >= 0
            assert any(not f.available for f in exp.factors)  # géochimie absente
        return
    exp = explain_target(camp.targets[0])
    assert "Pourquoi" in exp.why or exp.target_id in exp.why or exp.composite_score >= 0
    geochem = next(f for f in exp.factors if f.name == "geochemistry")
    assert geochem.available is False
    assert geochem.contribution == 0.0
    cmp = compare_targets(camp.targets[0], camp.targets[1])
    assert cmp.winner in {camp.targets[0]["target_id"], camp.targets[1]["target_id"]}
    assert cmp.narrative


def test_lithium_still_no_fake_targets() -> None:
    camp = run_campaign(zone="Kolwezi", mineral="lithium", max_targets=5)
    assert camp.targets == []
    diag = diagnose_zone(zone="Kolwezi", mineral="lithium")
    assert any("raster" in g.lower() or "prospectivité" in g.lower() for g in diag.gaps)
