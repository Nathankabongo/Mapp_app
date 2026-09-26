"""Profils minéraux configurables — pas de minerais codés en dur dans les modèles."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

PROFILES_DIR = Path("config/mineral_profiles")


@dataclass
class MineralProfile:
    mineral: str
    code: str
    aliases: list[str] = field(default_factory=list)
    display_name: str = ""
    geological_context: str = ""
    favorable_lithologies: list[str] = field(default_factory=list)
    alteration_signatures: list[str] = field(default_factory=list)
    geochemical_elements: list[str] = field(default_factory=list)
    geophysical_signatures: list[str] = field(default_factory=list)
    remote_sensing_indicators: list[str] = field(default_factory=list)
    known_deposit_types: list[str] = field(default_factory=list)
    exploration_indicators: list[str] = field(default_factory=list)
    atlas_layer: str | None = None
    raster_commodity: str | None = None
    economic_parameters: dict = field(default_factory=dict)
    source_file: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def supports_raster_targets(self) -> bool:
        return bool(self.raster_commodity)


def _normalize(name: str) -> str:
    return name.strip().lower().replace("_", " ").replace("-", " ")


@lru_cache(maxsize=1)
def list_profiles(profiles_dir: str | None = None) -> tuple[MineralProfile, ...]:
    root = Path(profiles_dir) if profiles_dir else PROFILES_DIR
    if not root.exists():
        return ()
    out: list[MineralProfile] = []
    for path in sorted(root.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        out.append(
            MineralProfile(
                mineral=str(raw.get("mineral", path.stem)),
                code=str(raw.get("code", path.stem[:3])),
                aliases=[str(a) for a in raw.get("aliases", [])],
                display_name=str(raw.get("display_name") or raw.get("mineral") or path.stem),
                geological_context=str(raw.get("geological_context", "")),
                favorable_lithologies=list(raw.get("favorable_lithologies") or []),
                alteration_signatures=list(raw.get("alteration_signatures") or []),
                geochemical_elements=list(raw.get("geochemical_elements") or []),
                geophysical_signatures=list(raw.get("geophysical_signatures") or []),
                remote_sensing_indicators=list(raw.get("remote_sensing_indicators") or []),
                known_deposit_types=list(raw.get("known_deposit_types") or []),
                exploration_indicators=list(raw.get("exploration_indicators") or []),
                atlas_layer=raw.get("atlas_layer"),
                raster_commodity=raw.get("raster_commodity"),
                economic_parameters=dict(raw.get("economic_parameters") or {}),
                source_file=str(path),
            )
        )
    return tuple(out)


def get_profile(mineral: str, profiles_dir: str | None = None) -> MineralProfile | None:
    """Résout un minerai via nom / alias / code."""
    key = _normalize(mineral)
    for profile in list_profiles(profiles_dir):
        candidates = {_normalize(profile.mineral), _normalize(profile.code), _normalize(profile.display_name)}
        candidates.update(_normalize(a) for a in profile.aliases)
        # cu_co special
        if profile.atlas_layer:
            candidates.add(_normalize(profile.atlas_layer))
        if key in candidates:
            return profile
        # fuzzy: "cuivre / cobalt"
        if any(key.replace(" ", "") == c.replace(" ", "") for c in candidates):
            return profile
    return None


def mineral_supports_raster(mineral: str) -> bool:
    profile = get_profile(mineral)
    if profile is None:
        # rétrocompat : cuivre/cobalt historiques
        return _normalize(mineral) in {
            "cuivre",
            "cobalt",
            "cu",
            "co",
            "cu co",
            "cuivre / cobalt",
            "copper",
        }
    return profile.supports_raster_targets()


def list_mineral_names() -> list[str]:
    names = [p.mineral for p in list_profiles()]
    return names or ["cuivre", "cobalt", "lithium", "or", "coltan", "nickel", "manganèse", "terres rares"]
