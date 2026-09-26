"""Modèles du Data Catalog unifié."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class QualityDimensions:
    """Dimensions du Data Quality Score (0–100 chacune)."""

    completeness: float = 0.0
    accuracy: float = 0.0
    consistency: float = 0.0
    recency: float = 0.0
    spatial_resolution: float = 0.0
    source_reliability: float = 0.0
    scientific_quality: float = 0.0
    processing_quality: float = 0.0

    def global_score(self) -> float:
        vals = [
            self.completeness,
            self.accuracy,
            self.consistency,
            self.recency,
            self.spatial_resolution,
            self.source_reliability,
            self.scientific_quality,
            self.processing_quality,
        ]
        return round(sum(vals) / len(vals), 1)

    def to_dict(self) -> dict[str, float]:
        d = asdict(self)
        d["global_score"] = self.global_score()
        return d


@dataclass
class DatasetRecord:
    """Fiche catalogue d'un dataset — source de vérité unique."""

    dataset_id: str
    name: str
    description: str
    source: str
    organization: str
    official_url: str
    license: str
    data_type: str
    format: str
    coverage: str
    resolution: str
    coordinate_reference_system: str
    category: str
    data_class: str  # OFFICIAL / OPEN / DEMO / …
    evidence_level: str  # OBSERVATION / INTERPRETATION / …
    availability: str  # CONNECTED / DEMO / NOT_CONNECTED / …
    acquisition_date: str = "N/E"
    publication_date: str = "N/E"
    last_update: str = "N/E"
    local_path: str = ""
    api_available: str = "Non"
    access_method: str = ""
    frequency: str = "N/E"
    reliability_note: str = ""
    note: str = ""
    processing_history: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    quality: QualityDimensions = field(default_factory=QualityDimensions)
    # Compat UI Hub
    last_data: str = ""
    status_fr: str = ""

    def to_dict(self) -> dict[str, Any]:
        from compass_core.catalog.classification import (
            availability_label,
            data_class_label,
            evidence_level_label,
        )

        d = asdict(self)
        d["quality"] = self.quality.to_dict()
        d["quality_score"] = self.quality.global_score()
        d["data_class_label"] = data_class_label(self.data_class)
        d["evidence_level_label"] = evidence_level_label(self.evidence_level)
        d["availability_label"] = availability_label(self.availability)
        d["local_exists"] = bool(self.local_path) and _path_exists(self.local_path)
        # Alias legacy pour DataSourceMeta / Hub
        d["id"] = self.dataset_id
        d["provider"] = self.organization
        d["url"] = self.official_url
        d["licence"] = self.license
        d["status"] = self.status_fr or availability_label(self.availability)
        d["reliability"] = self.reliability_note
        d["last_data"] = self.last_data or self.last_update
        return d

    def to_legacy_source_row(self) -> dict[str, Any]:
        """Format page Données & sources (SOURCE_CATALOG)."""
        from compass_core.catalog.classification import data_class_label

        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "source": self.official_url or self.source,
            "date": self.acquisition_date,
            "resolution": self.resolution,
            "crs": self.coordinate_reference_system,
            "format": self.format,
            "updated": self.last_update,
            "quality": f"{self.quality.global_score()}/100 — {self.reliability_note}",
            "availability": self.availability,
            "data_class": self.data_class.lower()
            if self.data_class
            in ("OFFICIAL", "OPEN", "DEMO", "MODELED", "ESTIMATED", "HISTORICAL")
            else "demo",
            "data_class_canonical": self.data_class,
            "data_class_label": data_class_label(self.data_class),
            "evidence_level": self.evidence_level,
            "official": "Oui" if self.data_class == "OFFICIAL" else "Non",
            "verifiable": self.reliability_note,
            "confidence": max(1, min(5, int(round(self.quality.source_reliability / 20)))),
            "dataset_id": self.dataset_id,
            "local_path": self.local_path,
            "note": self.note,
        }


def _path_exists(path: str) -> bool:
    from pathlib import Path

    p = Path(path)
    return p.exists()
