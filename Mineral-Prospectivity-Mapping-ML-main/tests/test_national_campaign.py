"""Tests campagne nationale — Minerai × Zone × N/E."""

from compass_core.exploration.campaign import run_campaign
from compass_core.minerals.zone_knowledge import (
    default_mineral_for_zone,
    list_all_provinces,
    minerals_for_zone,
    normalize_province_name,
)
from compass_core.prospectivity.prediction import run_prospectivity


def test_all_rdc_provinces_listed() -> None:
    provinces = list_all_provinces()
    assert "Lualaba" in provinces
    assert "Sud-Kivu" in provinces
    assert "Nord-Kivu" in provinces
    assert "Kasaï-Oriental" in provinces
    assert "Kinshasa" in provinces
    assert len(provinces) >= 25


def test_minerals_contextual_lualaba_vs_sud_kivu() -> None:
    lua = {m.mineral for m in minerals_for_zone("Lualaba")}
    sk = {m.mineral for m in minerals_for_zone("Sud-Kivu")}
    assert "cuivre" in lua
    assert "cobalt" in lua
    assert "or" in sk
    assert "étain" in sk or "coltan" in sk
    assert "cuivre" not in sk  # pas proposé par défaut hors Copperbelt KB


def test_normalize_kasai_alias() -> None:
    assert normalize_province_name("Kasaï Oriental") == "Kasaï-Oriental"


def test_prospectivity_ne_outside_kolwezi() -> None:
    # Sud-Kivu or — documenté mais pas de raster
    r = run_prospectivity(zone="Twangiza", mineral="or", province="Sud-Kivu")
    assert r.prospectivity_pct is None
    assert r.prospectivity_level == "N/E"
    assert r.status == "N/E"
    assert r.ne_guidance is not None
    assert r.ne_guidance["prospectivity"] == "N/E"


def test_prospectivity_ne_not_zero() -> None:
    r = run_prospectivity(latitude=-2.95, longitude=28.65, mineral="or", province="Sud-Kivu")
    assert r.prospectivity_pct is not 0  # noqa: E714 — must be None, not 0
    assert r.prospectivity_pct is None


def test_campaign_national_sud_kivu_no_fake_targets() -> None:
    camp = run_campaign(province="Sud-Kivu", mineral="or", max_targets=5)
    assert camp.province == "Sud-Kivu"
    assert camp.targets == []
    assert camp.prospectivity["status"] == "N/E"
    assert camp.zone_context["available_minerals"]
    assert camp.prospectivity["prospectivity_pct"] is None


def test_campaign_kolwezi_cuivre_still_works() -> None:
    camp = run_campaign(zone="Kolwezi", province="Lualaba", mineral="cuivre", max_targets=5)
    assert camp.prospectivity["status"] in {"evaluated", "N/E"}
    # Si raster présent et in_bounds → evaluated + targets possibles
    if camp.prospectivity["status"] == "evaluated":
        assert camp.prospectivity["prospectivity_pct"] is not None
        assert camp.prospectivity["prospectivity_pct"] > 0 or camp.prospectivity["prospectivity_pct"] == 0.0
        # 0.0 autorisé seulement si vraiment calculé (favorabilité nulle réelle)
    assert default_mineral_for_zone("Lualaba") in {"cuivre", "cobalt"}
