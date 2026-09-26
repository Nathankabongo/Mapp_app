"""Tests pipeline exploration + forages + NBD."""

from compass_core.constants import EXPLORATION_TRUTH_CHAIN, ROLES
from compass_core.drillholes.store import drillhole_count, load_demo_drillholes
from compass_core.drilling.next_best_drillhole import next_best_drillhole
from compass_core.exploration.campaign import run_campaign
from compass_core.modelling.model3d import build_scene
from compass_core.modelling.rbf import rbf_status


def test_roles_still_defined() -> None:
    assert "GÉOLOGUE" in ROLES


def test_truth_chain() -> None:
    assert len(EXPLORATION_TRUTH_CHAIN) >= 7


def test_campaign_kolwezi_cuivre_targets() -> None:
    camp = run_campaign(zone="Kolwezi", mineral="cuivre", max_targets=8)
    assert camp.country == "RDC"
    assert camp.mineral == "cuivre"
    assert "prédiction" in camp.disclaimer.lower() or "IA" in camp.disclaimer
    # Raster Kolwezi présent → au moins une cible attendue
    assert isinstance(camp.targets, list)
    if camp.targets:
        t0 = camp.targets[0]
        assert t0["target_id"].startswith("CIBLE-")
        assert t0["data_class"] == "prediction"
        assert t0["prospectivity_score"] >= 0
        assert "assay" not in t0  # pas de teneur inventée sur cible


def test_campaign_lithium_no_fake_raster_targets() -> None:
    camp = run_campaign(zone="Kolwezi", mineral="lithium", max_targets=5)
    # Pas de raster Li → 0 cible inventée
    assert camp.targets == []


def test_demo_drillholes() -> None:
    info = drillhole_count()
    holes = load_demo_drillholes()
    assert info["count"] == len(holes)
    if holes:
        assert all(h.hole_id.startswith("DEMO-") for h in holes)
        # Aucune teneur mesurée inventée dans le jeu démo
        for h in holes:
            for iv in h.intervals:
                assert iv.assay_value is None


def test_scene_3d() -> None:
    scene = build_scene(load_demo_drillholes())
    assert scene["version"].startswith("V1")
    assert "drillholes" in scene["layers_available"]


def test_next_best_drillhole() -> None:
    camp = run_campaign(zone="Kolwezi", mineral="cuivre", max_targets=5)
    nbd = next_best_drillhole(targets=camp.targets, existing_holes=0)
    if camp.targets:
        assert nbd["status"] == "PROPOSITION"
        assert "géologue" in nbd["disclaimer"].lower()
    else:
        assert nbd["status"] == "NON DISPONIBLE"


def test_rbf_status() -> None:
    st = rbf_status()
    assert "status" in st
