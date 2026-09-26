"""Data Catalog unifié CriticalMineralsCompass."""

from __future__ import annotations

from compass_core.catalog.classification import (
    AVAILABILITY_LABELS,
    DATA_CLASS_LABELS,
    EVIDENCE_LEVEL_LABELS,
    availability_label,
    canonicalize_data_class,
    data_class_label,
    evidence_level_label,
)
from compass_core.catalog.models import DatasetRecord, QualityDimensions
from compass_core.catalog.service import (
    build_catalog,
    catalog_as_dicts,
    catalog_by_category,
    domain_coverage_score,
    get_dataset,
    hub_registry_dicts,
    legacy_source_catalog,
    national_data_coverage,
)

__all__ = [
    "AVAILABILITY_LABELS",
    "DATA_CLASS_LABELS",
    "EVIDENCE_LEVEL_LABELS",
    "DatasetRecord",
    "QualityDimensions",
    "availability_label",
    "build_catalog",
    "canonicalize_data_class",
    "catalog_as_dicts",
    "catalog_by_category",
    "data_class_label",
    "domain_coverage_score",
    "evidence_level_label",
    "get_dataset",
    "hub_registry_dicts",
    "legacy_source_catalog",
    "national_data_coverage",
]
