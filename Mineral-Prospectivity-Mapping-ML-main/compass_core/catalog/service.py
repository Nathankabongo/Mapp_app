"""Data Catalog unifié — source de vérité pour sources, qualité et couverture."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from compass_core.catalog.classification import availability_label
from compass_core.catalog.definitions import static_definitions
from compass_core.catalog.models import DatasetRecord, QualityDimensions


def _exists(path: str) -> bool:
    if not path:
        return False
    p = Path(path)
    if p.is_dir():
        return p.exists() and any(p.iterdir())
    return p.exists()


def _favorability_present() -> bool:
    base = Path("outputs/kolwezi_sample")
    return (base / "kolwezi_woe_cu_co_favorability.npy").exists() or (
        base / "kolwezi_woe_cu_co_favorability.tif"
    ).exists()


def _cami_official_present() -> bool:
    """Export officiel uniquement sous data/rdc/official/ (jamais le GPKG DEMO)."""
    official = Path("data/rdc/official")
    if not official.exists():
        return False
    for pattern in ("cami_permits.gpkg", "cami_permits.geojson", "cami_permits.csv"):
        if (official / pattern).exists():
            return True
    return any(official.glob("cami*"))


def _refine(record: DatasetRecord) -> DatasetRecord:
    """Affine disponibilité / classe selon fichiers locaux — jamais d'invention."""
    r = deepcopy(record)
    ds = r.dataset_id

    if ds == "cami":
        if _cami_official_present():
            r.availability = "LOCAL_OK"
            r.data_class = "OFFICIAL"
            r.last_data = "Export officiel local"
            r.last_update = "fichier officiel présent"
            r.status_fr = "CONNECTÉ"
            r.quality = replace(
                r.quality,
                completeness=70.0,
                accuracy=85.0,
                recency=60.0,
                processing_quality=70.0,
            )
        elif _exists(r.local_path):
            r.availability = "DEMO"
            r.data_class = "DEMO"
            r.last_data = "Couche locale cadastre_demo"
            r.status_fr = "DÉMO"
            r.note = (
                r.note
                + " Fichier présent mais NON officiel (préfixe DEMO / cadastre fictif)."
            )
        else:
            r.availability = "NOT_CONNECTED"
            r.status_fr = "NON DISPONIBLE"

    elif ds == "cadastre_demo":
        r.availability = "DEMO" if _exists(r.local_path) else "NOT_AVAILABLE"
        r.status_fr = "DÉMO" if _exists(r.local_path) else "NON DISPONIBLE"

    elif ds == "atlas_compass":
        r.availability = "DEMO" if _exists(r.local_path) else "NOT_AVAILABLE"
        r.status_fr = "DÉMO" if _exists(r.local_path) else "NON DISPONIBLE"

    elif ds == "srtm":
        # Stack Kolwezi synthétique ≠ SRTM national
        if _exists("data/rdc/national/dem.tif") or _exists("data/rdc/national/srtm.tif"):
            r.availability = "LOCAL_OK"
            r.data_class = "OPEN"
            r.local_path = (
                "data/rdc/national/dem.tif"
                if _exists("data/rdc/national/dem.tif")
                else "data/rdc/national/srtm.tif"
            )
            r.status_fr = "LOCAL OK"
            r.reliability_note = "MNT national local"
            r.quality = replace(
                r.quality,
                completeness=80.0,
                accuracy=85.0,
                source_reliability=90.0,
                scientific_quality=85.0,
            )
        elif _exists(r.local_path):
            r.availability = "SYNTHETIC"
            r.data_class = "SYNTHETIC"
            r.status_fr = "DÉMO"
            r.last_data = "Bande élévation stack Kolwezi (synthétique)"
        else:
            r.availability = "NOT_AVAILABLE"
            r.status_fr = "NON DISPONIBLE"

    elif ds == "kolwezi_stack":
        r.availability = "SYNTHETIC" if _exists(r.local_path) else "NOT_AVAILABLE"
        r.status_fr = "SYNTHÉTIQUE" if _exists(r.local_path) else "NON DISPONIBLE"

    elif ds == "worldpop":
        if _exists("data/rdc/official/worldpop_cod.tif"):
            r.availability = "LOCAL_OK"
            r.data_class = "ESTIMATED"
            r.local_path = "data/rdc/official/worldpop_cod.tif"
            r.status_fr = "LOCAL OK"
        elif _exists(r.local_path):
            r.availability = "DEMO"
            r.data_class = "DEMO"
            r.status_fr = "DÉMO"
        else:
            r.availability = "NOT_AVAILABLE"
            r.status_fr = "NON DISPONIBLE"

    elif ds == "favorability_woe":
        if _favorability_present():
            r.availability = "DEMO"
            r.data_class = "PREDICTED"
            r.status_fr = "DÉMO"
            r.last_data = "outputs/kolwezi_sample/"
        else:
            r.availability = "NOT_AVAILABLE"
            r.status_fr = "NON DISPONIBLE"

    elif ds == "regions_national":
        r.availability = "LOCAL_OK" if _exists(r.local_path) else "NOT_AVAILABLE"
        r.status_fr = "LOCAL OK" if _exists(r.local_path) else "NON DISPONIBLE"

    elif ds == "drillholes_demo":
        r.availability = "DEMO" if _exists(r.local_path) else "NOT_AVAILABLE"
        r.status_fr = "DÉMO" if _exists(r.local_path) else "NON DISPONIBLE"

    elif ds == "geology_national":
        geo = Path("data/rdc/national/geology.gpkg")
        faults = Path("data/rdc/national/faults.gpkg")
        if geo.exists() or faults.exists():
            r.availability = "PARTIAL" if not (geo.exists() and faults.exists()) else "LOCAL_OK"
            r.data_class = "OPEN"
            r.status_fr = "PARTIEL" if r.availability == "PARTIAL" else "LOCAL OK"
        else:
            r.availability = "NOT_AVAILABLE"
            r.status_fr = "NON DISPONIBLE"

    elif ds in ("pcm_extract_rdc", "drc_mining_warehouse", "soilgrids", "hwsd", "worldclim"):
        r.availability = "NOT_CONNECTED"
        r.status_fr = "NOT_CONNECTED"

    elif ds in ("sentinel2", "sentinel1", "landsat", "usgs_mrds"):
        r.availability = "TO_CONFIGURE"
        r.status_fr = "À CONFIGURER"

    elif ds in ("osm", "esri_imagery"):
        r.availability = "CONNECTED"
        r.status_fr = "CONNECTÉ"

    elif ds in ("geochemistry", "geophysics_national"):
        r.availability = "NOT_AVAILABLE"
        r.status_fr = "NON DISPONIBLE"

    if not r.status_fr:
        r.status_fr = availability_label(r.availability)
    if not r.last_data:
        r.last_data = r.last_update
    return r


def build_catalog() -> list[DatasetRecord]:
    """Construit le catalogue vivant (statuts locaux, jamais inventés)."""
    return [_refine(r) for r in static_definitions()]


def get_dataset(dataset_id: str) -> DatasetRecord | None:
    for r in build_catalog():
        if r.dataset_id == dataset_id:
            return r
    return None


def catalog_as_dicts() -> list[dict]:
    return [r.to_dict() for r in build_catalog()]


def catalog_by_category() -> dict[str, list[DatasetRecord]]:
    grouped: dict[str, list[DatasetRecord]] = {}
    for r in build_catalog():
        grouped.setdefault(r.category, []).append(r)
    return grouped


def legacy_source_catalog() -> list[dict]:
    """Compat page 13_Donnees_sources (SOURCE_CATALOG)."""
    return [r.to_legacy_source_row() for r in build_catalog()]


def hub_registry_dicts() -> list[dict]:
    """Compat Data API Hub /api/sources."""
    return catalog_as_dicts()


def coverage_domains() -> dict[str, list[str]]:
    """Mapping domaine métier → dataset_ids pour Data Coverage."""
    return {
        "Geology": ["geology_national", "kolwezi_stack"],
        "Satellite": ["sentinel2", "sentinel1", "landsat", "esri_imagery"],
        "Soil": ["soilgrids", "hwsd"],
        "Climate": ["worldclim"],
        "DEM": ["srtm"],
        "Geochemistry": ["geochemistry"],
        "Geophysics": ["geophysics_national", "kolwezi_stack"],
        "Occurrences": ["atlas_compass", "usgs_mrds"],
        "Cadastre": ["cami", "cadastre_demo"],
        "Population": ["worldpop"],
        "Infrastructure": ["osm"],
        "Prospectivity": ["favorability_woe"],
        "PCM": ["pcm_extract_rdc"],
        "DRC_Mining": ["drc_mining_warehouse"],
        "Drillholes": ["drillholes_demo"],
    }


def domain_coverage_score(domain: str, records: list[DatasetRecord] | None = None) -> dict:
    """Score de couverture 0–100 + état pour un domaine."""
    catalog = records or build_catalog()
    by_id = {r.dataset_id: r for r in catalog}
    ids = coverage_domains().get(domain, [])
    if not ids:
        return {
            "domain": domain,
            "score_pct": 0.0,
            "status": "NOT_EVALUATED",
            "datasets": [],
            "reason": "Domaine inconnu",
        }

    active = []
    scores = []
    for did in ids:
        r = by_id.get(did)
        if r is None:
            continue
        q = r.quality.global_score()
        # Disponibilité module le score
        avail = r.availability
        if avail in ("NOT_AVAILABLE", "NOT_CONNECTED", "TO_CONFIGURE"):
            contrib = 0.0 if avail != "TO_CONFIGURE" else min(10.0, q * 0.1)
        elif avail in ("DEMO", "SYNTHETIC"):
            contrib = min(40.0, q * 0.5)
        elif avail == "PARTIAL":
            contrib = min(70.0, q * 0.8)
        elif avail in ("CONNECTED", "LOCAL_OK"):
            contrib = min(100.0, max(q, 50.0))
        else:
            contrib = q * 0.3
        scores.append(contrib)
        active.append(
            {
                "dataset_id": r.dataset_id,
                "name": r.name,
                "availability": r.availability,
                "data_class": r.data_class,
                "quality_score": q,
                "contribution_pct": round(contrib, 1),
            }
        )

    score = round(sum(scores) / len(scores), 1) if scores else 0.0
    if score <= 0:
        status = "NOT_AVAILABLE"
    elif score < 25:
        status = "DATA_INSUFFICIENT"
    elif score < 55:
        status = "DATA_PARTIAL"
    elif any(a["availability"] in ("DEMO", "SYNTHETIC") for a in active) and score < 70:
        status = "DATA_PARTIAL"
    else:
        status = "DATA_AVAILABLE"

    # Prospectivité : MODEL_AVAILABLE seulement si raster présent
    if domain == "Prospectivity":
        if _favorability_present():
            status = "MODEL_AVAILABLE"
        else:
            status = "MODEL_UNAVAILABLE"
            score = 0.0

    return {
        "domain": domain,
        "score_pct": score,
        "status": status,
        "datasets": active,
    }


def national_data_coverage() -> dict:
    """Carte nationale de couverture par domaine."""
    catalog = build_catalog()
    domains = [domain_coverage_score(d, catalog) for d in coverage_domains()]
    overall = round(sum(d["score_pct"] for d in domains) / len(domains), 1) if domains else 0.0
    return {
        "country": "COD",
        "overall_coverage_pct": overall,
        "domains": domains,
        "disclaimer": (
            "Couverture basée sur datasets locaux et connecteurs documentés. "
            "DEMO/SYNTHETIC ne comptent pas comme données officielles. "
            "Prospectivity hors Kolwezi Cu-Co = N/E."
        ),
        "catalog_version": "1.0",
        "dataset_count": len(catalog),
    }


def average_catalog_quality() -> QualityDimensions:
    """Moyenne des dimensions sur le catalogue (santé système)."""
    rows = build_catalog()
    if not rows:
        return QualityDimensions()
    keys = [
        "completeness",
        "accuracy",
        "consistency",
        "recency",
        "spatial_resolution",
        "source_reliability",
        "scientific_quality",
        "processing_quality",
    ]
    agg = {k: 0.0 for k in keys}
    for r in rows:
        qd = r.quality.to_dict()
        for k in keys:
            agg[k] += float(qd[k])
    n = float(len(rows))
    return QualityDimensions(**{k: round(v / n, 1) for k, v in agg.items()})
