"""Traçabilité des exécutions (provenance)."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class ProvenanceRecord:
    """Enregistrement complet d'une exécution CriticalMineralsCompass."""

    run_id: str
    timestamp_utc: str
    project_name: str
    model_name: str
    random_seed: int
    region: dict[str, Any]
    data_paths: dict[str, str]
    hyperparameters: dict[str, Any]
    metrics: dict[str, float] = field(default_factory=dict)
    output_files: list[str] = field(default_factory=list)
    software_version: str = "0.1.0"
    
    # Intégration SGN-C
    analysis_id: str = field(init=False)
    dataset_version: str = "BNDG-KAT-2026-04"
    validation_status: str = "Pending"
    
    def __post_init__(self):
        self.analysis_id = f"CMP-{datetime.now(UTC).strftime('%Y')}-{self.run_id[:8].upper()}"

    @classmethod
    def create(
        cls,
        *,
        project_name: str,
        model_name: str,
        random_seed: int,
        region: dict[str, Any],
        data_paths: dict[str, str],
        hyperparameters: dict[str, Any],
        dataset_version: str = "BNDG-KAT-2026-04"
    ) -> ProvenanceRecord:
        return cls(
            run_id=str(uuid.uuid4()),
            timestamp_utc=datetime.now(UTC).isoformat(),
            project_name=project_name,
            model_name=model_name,
            random_seed=random_seed,
            region=region,
            data_paths=data_paths,
            hyperparameters=hyperparameters,
            dataset_version=dataset_version,
        )


def save_provenance(record: ProvenanceRecord, output_dir: str | Path) -> Path:
    """Écrit ``provenance.json`` dans le répertoire de sortie."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "provenance.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(asdict(record), handle, indent=2, ensure_ascii=False)
    return path
