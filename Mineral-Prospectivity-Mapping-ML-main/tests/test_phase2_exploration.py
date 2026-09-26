"""Tests Phase 2 — incertitude, smart sampling, planner, historique, forages."""

from pathlib import Path

from compass_core.constants import UNAVAILABLE
from compass_core.drillholes.intelligence import enrich_hole, link_targets_to_drillholes
from compass_core.drillholes.store import load_demo_drillholes
from compass_core.exploration.campaign import run_campaign
from compass_core.exploration.history import list_campaigns, save_campaign, update_target_outcome
from compass_core.exploration.planning import plan_for_target
from compass_core.exploration.smart_sampling import recommend_samples
from compass_core.exploration.uncertainty_map import build_uncertainty_map


def test_uncertainty_map_kolwezi() -> None:
    report = build_uncertainty_map(zone="Kolwezi", mineral="cuivre", max_cells=36)
    assert report.cells or report.raster_path is None
    assert "pas une carte de réserves" in report.disclaimer.lower()


def test_smart_sampling_returns_justified_points() -> None:
    plan = recommend_samples(zone="Kolwezi", mineral="cuivre", n_points=12)
    assert plan.recommended_count == len(plan.points)
    if plan.points:
        p0 = plan.points[0]
        assert p0["sample_id"].startswith("SMP-")
        assert p0["priority"] in {"P1", "P2", "P3"}
        assert p0["justification"]
        assert plan.expected_uncertainty_reduction_pct is not None


def test_planner_never_auto_drills_on_low_confidence() -> None:
    weak = {
        "target_id": "CIBLE-99",
        "prospectivity_score": 92,
        "confidence_pct": 35,
        "uncertainty_pct": 65,
        "uncertainty_label": "élevée",
        "data_quality": 40,
        "latitude": -10.7,
        "longitude": 25.4,
        "constraints": ["Donnée manquante : géochimie"],
    }
    plan = plan_for_target(weak, diagnostic_gaps=["Faible densité géochimique"])
    block = plan["CIBLE-99"]
    assert "NON RECOMMANDÉ" in block["drill_decision"]
    assert len(block["phases"]) == 5
    assert block["phases"][-1]["name"].lower().startswith("forage")


def test_campaign_history_roundtrip(tmp_path: Path) -> None:
    camp = run_campaign(zone="Kolwezi", mineral="cuivre", max_targets=3)
    entry = save_campaign(camp.to_dict(), history_dir=tmp_path, status="ouverte")
    assert entry.path
    assert (tmp_path / "index.json").exists()
    items = list_campaigns(history_dir=tmp_path)
    assert any(i["campaign_id"] == entry.campaign_id for i in items)
    if camp.targets:
        tid = camp.targets[0]["target_id"]
        updated = update_target_outcome(entry.campaign_id, tid, "approfondir", history_dir=tmp_path)
        assert updated is not None
        assert updated["outcomes"][tid] == "approfondir"


def test_drillhole_intelligence_links() -> None:
    holes = load_demo_drillholes()
    assert holes
    detail = enrich_hole(holes[0])
    assert detail["has_assays"] is False
    for a in detail["assays"]:
        assert a["value"] is None or a["value"] == UNAVAILABLE or isinstance(a["value"], (int, float))

    camp = run_campaign(zone="Kolwezi", mineral="cuivre", max_targets=5)
    tree = link_targets_to_drillholes(camp.targets, radius_km=50.0)
    assert "targets" in tree
    assert tree["disclaimer"]
