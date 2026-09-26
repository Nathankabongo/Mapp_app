"""Catalogue de couches cartographiques (activation UI)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LayerSpec:
    id: str
    label: str
    group: str
    status: str  # available | missing | demo | remote
    path: str | None = None
    data_class: str = "unavailable"
    note: str = ""


def inventory_layers() -> list[LayerSpec]:
    atlas = Path("data/rdc/atlas")
    national = Path("data/rdc/national")
    kolwezi = Path("data/rdc/kolwezi")
    fav = Path("outputs/kolwezi_sample/kolwezi_woe_cu_co_favorability.tif")
    if not fav.exists():
        fav = Path("outputs/kolwezi_sample/kolwezi_woe_cu_co_favorability.npy")

    def exists(p: Path) -> bool:
        return p.exists()

    return [
        LayerSpec("imagery", "Imagerie satellite", "BASE", "remote", None, "observation", "Tuiles ESRI / OSM"),
        LayerSpec("geology", "Géologie", "GÉOLOGIE", "missing" if not (national / "geology.gpkg").exists() else "available", str(national / "geology.gpkg"), "open"),
        LayerSpec("geophysics", "Géophysique", "GÉOLOGIE", "demo" if exists(kolwezi / "stack_multiphysics.tif") else "missing", str(kolwezi / "stack_multiphysics.tif"), "demo", "Stack multiphysique Kolwezi"),
        LayerSpec("geochem", "Géochimie", "GÉOLOGIE", "missing", None, "unavailable"),
        LayerSpec("prospect_cu", "Prospectivité cuivre", "ANALYTIQUE", "available" if fav.exists() else "missing", str(fav) if fav.exists() else None, "prediction"),
        LayerSpec("prospect_co", "Prospectivité cobalt", "ANALYTIQUE", "missing", None, "unavailable", "Pas de raster dédié"),
        LayerSpec("prospect_li", "Prospectivité lithium", "ANALYTIQUE", "missing", None, "unavailable"),
        LayerSpec("concessions", "Concessions", "MINIER", "demo" if exists(atlas / "cadastre_permis.gpkg") else "missing", str(atlas / "cadastre_permis.gpkg"), "demo"),
        LayerSpec("asm", "Exploitation artisanale (ASM)", "MINIER", "missing", None, "unavailable"),
        LayerSpec("roads", "Routes", "INFRA", "remote", None, "open", "Via tuiles OSM"),
        LayerSpec("settlements", "Villages / villes", "SOCIAL", "missing", None, "unavailable"),
        LayerSpec("hydro", "Cours d'eau", "ENV", "remote", None, "open", "Via tuiles OSM"),
        LayerSpec("forest", "Forêts", "ENV", "missing", None, "unavailable"),
        LayerSpec("protected", "Aires protégées", "ENV", "missing", None, "unavailable"),
        LayerSpec("risk", "Zones à risque", "ANALYTIQUE", "available", "config/risk_rules.json", "computed"),
        LayerSpec("sites", "Sites / occurrences", "MINIER", "demo" if exists(atlas / "deposits_cu_co.gpkg") else "missing", str(atlas / "deposits_cu_co.gpkg"), "historical"),
    ]
