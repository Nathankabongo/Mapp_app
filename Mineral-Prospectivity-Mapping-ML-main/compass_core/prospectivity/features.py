"""Feature engineering prospectivité — inventaire des couches disponibles."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from compass_core.analysis.site_evaluation import resolve_favorability_path


@dataclass
class FeatureAvailability:
    geology: bool = False
    structures: bool = False
    geophysics: bool = False
    geochemistry: bool = False
    remote_sensing: bool = False
    mineral_indices: bool = False
    occurrences: bool = False
    mining_history: bool = False
    topography: bool = False
    cadastre_official: bool = False
    details: dict[str, str] = field(default_factory=dict)

    def available_list(self) -> list[str]:
        mapping = {
            "geology": "Géologie",
            "structures": "Structures / failles",
            "geophysics": "Géophysique",
            "geochemistry": "Géochimie",
            "remote_sensing": "Télédétection / Sentinel",
            "mineral_indices": "Indices minéraux",
            "occurrences": "Occurrences minières",
            "mining_history": "Historique minier",
            "topography": "Topographie / MNT",
            "cadastre_official": "Cadastre CAMI officiel",
        }
        return [label for key, label in mapping.items() if getattr(self, key)]

    def missing_list(self) -> list[str]:
        mapping = {
            "geology": "Géologie détaillée",
            "structures": "Structures / failles",
            "geophysics": "Géophysique",
            "geochemistry": "Géochimie détaillée",
            "remote_sensing": "Sentinel-2 / scène locale",
            "mineral_indices": "Indices spectraux",
            "occurrences": "Occurrences minières",
            "mining_history": "Historique minier",
            "topography": "MNT",
            "cadastre_official": "Validation / cadastre officiel",
            "field": "Validation terrain",
        }
        missing = [label for key, label in mapping.items() if key != "field" and not getattr(self, key, False)]
        missing.append("Validation terrain")
        return missing

    @property
    def coverage_ratio(self) -> float:
        flags = [
            self.geology,
            self.structures,
            self.geophysics,
            self.geochemistry,
            self.remote_sensing,
            self.mineral_indices,
            self.occurrences,
            self.mining_history,
            self.topography,
            self.cadastre_official,
        ]
        return sum(1 for f in flags if f) / len(flags)


def assess_features(*, province: str | None = None, mineral: str = "cuivre") -> FeatureAvailability:
    """Évalue la disponibilité réelle des couches — jamais inventée."""
    fa = FeatureAvailability()
    if Path("data/rdc/national/geology.gpkg").exists():
        fa.geology = True
        fa.details["geology"] = "data/rdc/national/geology.gpkg"
    if Path("data/rdc/national/faults.gpkg").exists():
        fa.structures = True
    stack = Path("data/rdc/kolwezi/stack_multiphysics.tif")
    if stack.exists():
        fa.geophysics = True
        fa.topography = True
        fa.details["geophysics"] = str(stack)
        fa.details["topography"] = "bande MNT du stack Kolwezi"
    atlas = Path("data/rdc/atlas")
    if (atlas / "deposits_cu_co.gpkg").exists() and mineral.lower() in {"cuivre", "cobalt", "cu", "co", "cu_co"}:
        fa.occurrences = True
        fa.mineral_indices = True
        fa.mining_history = True
        fa.details["occurrences"] = "atlas deposits_cu_co"
    elif mineral.lower() in {"lithium", "li"} and (atlas / "deposits_li.gpkg").exists():
        fa.occurrences = True
        fa.mineral_indices = True
    elif mineral.lower() in {"or", "au", "gold"} and (atlas / "deposits_au.gpkg").exists():
        fa.occurrences = True
        fa.mineral_indices = True
    # Télédétection : connectée en tuiles mais pas de scène locale = pas True pour analyse
    if Path("data/rdc/satellite").exists() and any(Path("data/rdc/satellite").glob("*")):
        fa.remote_sensing = True
    if Path("data/rdc/official/cami_permits.gpkg").exists():
        fa.cadastre_official = True
    if resolve_favorability_path() is not None:
        fa.details["model_raster"] = str(resolve_favorability_path())
    _ = province
    return fa
