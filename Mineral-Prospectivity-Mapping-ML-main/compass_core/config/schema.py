"""Schéma de configuration JSON pour CriticalMineralsCompass."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SUPPORTED_MODELS = ("rf", "svm", "ann", "cnn", "woe")
SUPPORTED_COMMODITIES = ("cu_co", "li", "au", "diamond", "coltan", "custom")
SUPPORTED_REGIONS = ("kolwezi", "manono", "custom")


@dataclass
class DataPaths:
    """Chemins des jeux de données géospatiales."""

    raster: str
    samples: str
    training: str
    testing: str
    output_dir: str = "outputs"


@dataclass
class RegionContext:
    """Contexte géologique et administratif RDC."""

    name: str = "kolwezi"
    crs: str = "EPSG:32733"
    commodity: str = "cu_co"
    province: str = "Lualaba"
    description: str = "Ceinture cuprifère — zone pilote Kolwezi"


@dataclass
class ModelConfig:
    """Hyperparamètres et réglages du modèle."""

    name: str = "rf"
    random_seed: int = 42
    cv_folds: int = 5
    grid_search: bool = True
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportConfig:
    """Options d'export SIG et rapports."""

    geotiff: bool = True
    geopackage: bool = True
    pdf_report: bool = False
    mask_nodata: bool = True


@dataclass
class CompassConfig:
    """Configuration complète d'une exécution CriticalMineralsCompass."""

    project_name: str
    data: DataPaths
    region: RegionContext = field(default_factory=RegionContext)
    model: ModelConfig = field(default_factory=ModelConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    provenance_id: str | None = None

    def validate(self) -> None:
        if self.model.name not in SUPPORTED_MODELS:
            raise ValueError(
                f"Modèle '{self.model.name}' non supporté. "
                f"Choix : {', '.join(SUPPORTED_MODELS)}"
            )
        if self.region.commodity not in SUPPORTED_COMMODITIES:
            raise ValueError(
                f"Commodité '{self.region.commodity}' non supportée. "
                f"Choix : {', '.join(SUPPORTED_COMMODITIES)}"
            )


def load_config(path: str | Path) -> CompassConfig:
    """Charge une configuration depuis un fichier JSON."""
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = json.load(handle)

    data = DataPaths(**raw["data"])
    region = RegionContext(**raw.get("region", {}))
    model = ModelConfig(**raw.get("model", {}))
    export = ExportConfig(**raw.get("export", {}))

    config = CompassConfig(
        project_name=raw.get("project_name", "critical-minerals-compass"),
        data=data,
        region=region,
        model=model,
        export=export,
        provenance_id=raw.get("provenance_id"),
    )
    config.validate()
    return config
