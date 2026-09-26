"""Qualité système — façade catalogue + QA/QC (compatibilité UI)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from compass_core.catalog.classification import data_class_label
from compass_core.catalog.service import (
    average_catalog_quality,
    build_catalog,
    legacy_source_catalog,
    national_data_coverage,
)
from compass_core.constants import DATA_CLASSES, UNAVAILABLE
from compass_core.io.data_sources import REMOTE_SOURCES, TILE_SOURCES, list_available_sources
from compass_core.analysis.atlas_catalog import CATALOG_PATH, load_catalog
from compass_core.analysis.mineral_layers import load_cadastre
from compass_core.analysis.site_evaluation import resolve_favorability_path
from compass_core.io.terrain import resolve_dem_path
from compass_core.qa_qc.engine import run_qa_qc_catalog


# Alias dynamique — page 13 lit SOURCE_CATALOG
def _source_catalog() -> list[dict]:
    return legacy_source_catalog()


# Conservé comme nom historique ; contenu = catalogue unifié
SOURCE_CATALOG = None  # type: ignore[assignment]  # remplacé à l'import via __getattr__


def __getattr__(name: str):
    if name == "SOURCE_CATALOG":
        return legacy_source_catalog()
    raise AttributeError(name)


def system_health() -> dict:
    catalog = load_catalog()
    cadastre = load_cadastre()
    sources = list_available_sources()
    local_ok = sum(1 for s in sources if s["status"] == "local OK")
    fav = resolve_favorability_path()
    dem = resolve_dem_path()
    missing = []
    if cadastre is None:
        missing.append("cadastre officiel CAMI")
    if fav is None:
        missing.append("raster de favorabilité")
    if dem is None:
        missing.append("MNT national")
    if not CATALOG_PATH.exists():
        missing.append("catalogue atlas")

    unified = build_catalog()
    demo_n = sum(1 for r in unified if r.data_class in ("DEMO", "SYNTHETIC"))
    official_n = sum(1 for r in unified if r.data_class == "OFFICIAL" and r.availability == "LOCAL_OK")
    coverage = national_data_coverage()
    avg_q = average_catalog_quality()

    return {
        "last_sync": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "active_sources": local_ok,
        "registered_sources": len(unified),
        "remote_legacy": len(REMOTE_SOURCES) + len(TILE_SOURCES),
        "layers_catalogued": len(catalog.layers),
        "missing": missing,
        "quality": "partielle — mixte démo / open data" if missing else "locale opérationnelle",
        "data_quality_score": avg_q.global_score(),
        "data_quality_dimensions": avg_q.to_dict(),
        "demo_or_synthetic_datasets": demo_n,
        "official_local_datasets": official_n,
        "national_coverage_pct": coverage["overall_coverage_pct"],
        "offline_note": (
            "Source temporairement indisponible. Utilisation de la dernière donnée locale disponible."
        ),
        "disclaimer": (
            "Data Quality Score ≠ Prospectivity. DEMO/SYNTHETIC ne sont pas des données officielles."
        ),
    }


def class_label(key: str) -> str:
    """Label classe — accepte legacy ou canonique."""
    if key in DATA_CLASSES:
        return DATA_CLASSES[key]
    return data_class_label(key)


def run_system_qa_qc() -> dict:
    """Lance QA/QC catalogue (fichiers locaux)."""
    return run_qa_qc_catalog(only_local=True)


def catalog_summary() -> dict:
    rows = legacy_source_catalog()
    return {
        "count": len(rows),
        "by_class": _count_by(rows, "data_class_canonical"),
        "by_availability": _count_by(rows, "availability"),
        "unavailable": UNAVAILABLE,
        "catalog_path_exists": Path(CATALOG_PATH).exists() if CATALOG_PATH else False,
    }


def _count_by(rows: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        k = str(r.get(key) or "N/E")
        out[k] = out.get(k, 0) + 1
    return out
