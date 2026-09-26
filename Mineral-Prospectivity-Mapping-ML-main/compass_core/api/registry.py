"""Registre des sources — façade vers le Data Catalog unifié."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from compass_core.catalog.service import build_catalog, catalog_by_category, hub_registry_dicts

SourceStatus = Literal["CONNECTÉ", "DISPONIBLE", "À CONFIGURER", "NON DISPONIBLE", "DÉMO", "NOT_CONNECTED", "SYNTHÉTIQUE", "LOCAL OK", "PARTIEL"]


@dataclass(frozen=True)
class DataSourceMeta:
    """Compatibilité Hub / tests — champs historiques conservés."""

    id: str
    name: str
    category: str
    provider: str
    url: str
    data_type: str
    format: str
    resolution: str
    coverage: str
    frequency: str
    last_data: str
    api_available: str
    licence: str
    access_method: str
    status: str
    reliability: str
    local_path: str = ""
    note: str = ""
    data_class: str = ""
    evidence_level: str = ""
    quality_score: float = 0.0


def build_registry() -> list[DataSourceMeta]:
    """Construit le registre depuis le Data Catalog unique."""
    out: list[DataSourceMeta] = []
    for r in build_catalog():
        d = r.to_dict()
        out.append(
            DataSourceMeta(
                id=r.dataset_id,
                name=r.name,
                category=r.category,
                provider=r.organization,
                url=r.official_url,
                data_type=r.data_type,
                format=r.format,
                resolution=r.resolution,
                coverage=r.coverage,
                frequency=r.frequency,
                last_data=d.get("last_data") or r.last_update,
                api_available=r.api_available,
                licence=r.license,
                access_method=r.access_method,
                status=d.get("status") or r.availability,
                reliability=r.reliability_note,
                local_path=r.local_path,
                note=r.note,
                data_class=r.data_class,
                evidence_level=r.evidence_level,
                quality_score=float(d.get("quality_score") or 0),
            )
        )
    return out


def registry_as_dicts() -> list[dict]:
    return hub_registry_dicts()


def sources_by_category() -> dict[str, list[DataSourceMeta]]:
    grouped: dict[str, list[DataSourceMeta]] = {}
    for s in build_registry():
        grouped.setdefault(s.category, []).append(s)
    return grouped


# Réexport pour introspection
catalog_categories = catalog_by_category
