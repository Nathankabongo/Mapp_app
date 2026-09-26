"""Catalogue et registre de l'atlas minier RDC."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ATLAS_DIR = Path("data/rdc/atlas")
CATALOG_PATH = ATLAS_DIR / "catalog.json"


@dataclass(frozen=True)
class MineralLayerMeta:
    """Métadonnées d'une couche minérale."""

    code: str
    label: str
    filename: str
    color: str
    provinces: tuple[str, ...]
    geological_belt: str
    description: str
    data_source: str
    reference_deposits: tuple[str, ...] = ()
    icon: str = "circle"


@dataclass
class AtlasInventory:
    """Inventaire des couches atlas disponibles."""

    layers: dict[str, MineralLayerMeta] = field(default_factory=dict)
    catalog_path: Path = CATALOG_PATH

    def available_codes(self) -> list[str]:
        return list(self.layers.keys())

    def layer_file_exists(self, code: str) -> bool:
        meta = self.layers.get(code)
        if meta is None:
            return False
        return (ATLAS_DIR / meta.filename).exists()


def load_catalog(catalog_path: Path = CATALOG_PATH) -> AtlasInventory:
    """Charge le catalogue JSON de l'atlas."""
    if not catalog_path.exists():
        return AtlasInventory(layers=_fallback_layers())

    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    layers: dict[str, MineralLayerMeta] = {}
    for entry in data.get("layers", []):
        meta = MineralLayerMeta(
            code=entry["code"],
            label=entry["label"],
            filename=entry["filename"],
            color=entry["color"],
            provinces=tuple(entry.get("provinces", [])),
            geological_belt=entry.get("geological_belt", ""),
            description=entry.get("description", ""),
            data_source=entry.get("data_source", ""),
            reference_deposits=tuple(entry.get("reference_deposits", [])),
            icon=entry.get("icon", "circle"),
        )
        layers[meta.code] = meta
    return AtlasInventory(layers=layers, catalog_path=catalog_path)


def _fallback_layers() -> dict[str, MineralLayerMeta]:
    defaults = {
        "cu_co": ("Cuivre-Cobalt", "deposits_cu_co.gpkg", "#1B6B4A", "Ceinture cuprifère"),
        "li": ("Lithium", "deposits_li.gpkg", "#7C3AED", "Manono"),
        "au": ("Or", "deposits_au.gpkg", "#D97706", "Est RDC"),
        "coltan": ("Coltan (3T)", "deposits_coltan.gpkg", "#2563EB", "Kivu"),
        "diamond": ("Diamant", "deposits_diamond.gpkg", "#0891B2", "Kasaï"),
    }
    return {
        code: MineralLayerMeta(
            code=code,
            label=label,
            filename=filename,
            color=color,
            provinces=(),
            geological_belt=belt,
            description="",
            data_source="atlas_demo",
        )
        for code, (label, filename, color, belt) in defaults.items()
    }


def save_catalog(inventory: AtlasInventory, catalog_path: Path = CATALOG_PATH) -> None:
    """Sauvegarde le catalogue (métadonnées uniquement)."""
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    layers = []
    for meta in inventory.layers.values():
        layers.append(
            {
                "code": meta.code,
                "label": meta.label,
                "filename": meta.filename,
                "color": meta.color,
                "icon": meta.icon,
                "provinces": list(meta.provinces),
                "geological_belt": meta.geological_belt,
                "description": meta.description,
                "data_source": meta.data_source,
                "reference_deposits": list(meta.reference_deposits),
            }
        )
    payload = {
        "version": "1.0",
        "title": "Atlas minier RDC — CriticalMineralsCompass",
        "layers": layers,
    }
    catalog_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
