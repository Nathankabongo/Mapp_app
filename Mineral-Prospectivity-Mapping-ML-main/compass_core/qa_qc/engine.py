"""QA/QC Engine — orchestration sur le Data Catalog et fichiers locaux."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from compass_core.catalog.service import build_catalog, get_dataset
from compass_core.qa_qc.checks import (
    QCIssue,
    QCReport,
    check_geochemical_batch,
    check_raster_file,
    check_vector_file,
    score_from_issues,
)


VECTOR_SUFFIXES = {".gpkg", ".geojson", ".json", ".shp", ".csv"}
RASTER_SUFFIXES = {".tif", ".tiff", ".ntf", ".img"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_qa_qc_on_path(
    path: str | Path,
    *,
    dataset_id: str = "adhoc",
    geochem_rows: list[dict] | None = None,
) -> QCReport:
    """Exécute QC sur un fichier local."""
    p = Path(path)
    spatial: list[QCIssue] = []
    temporal: list[QCIssue] = []
    scientific: list[QCIssue] = []
    geochemical: list[QCIssue] = []
    notes: list[str] = []

    if not p.exists():
        spatial.append(QCIssue("FILE_MISSING", "error", f"Introuvable: {p}"))
        dims = score_from_issues(file_missing=True)
        return QCReport(
            dataset_id=dataset_id,
            path=str(p),
            ok=False,
            spatial=spatial,
            quality_score=0.0,
            quality_dimensions=dims,
            checked_at=_now(),
            notes=["Fichier absent — score 0"],
        )

    if p.is_dir():
        # QC agrégé sur enfants vector/raster
        children = list(p.rglob("*"))
        files = [c for c in children if c.is_file() and c.suffix.lower() in VECTOR_SUFFIXES | RASTER_SUFFIXES]
        if not files:
            scientific.append(
                QCIssue("DIR_EMPTY_DATA", "warning", f"Aucun fichier SIG dans {p}")
            )
        for child in files[:20]:
            sub = run_qa_qc_on_path(child, dataset_id=f"{dataset_id}:{child.name}")
            spatial.extend(sub.spatial)
            temporal.extend(sub.temporal)
            scientific.extend(sub.scientific)
            geochemical.extend(sub.geochemical)
        notes.append(f"Répertoire: {len(files)} fichier(s) SIG scanné(s) (max 20)")
    else:
        suffix = p.suffix.lower()
        if suffix in VECTOR_SUFFIXES:
            sp, tp, sc = check_vector_file(p)
            spatial, temporal, scientific = sp, tp, sc
        elif suffix in RASTER_SUFFIXES:
            sp, sc = check_raster_file(p)
            spatial, scientific = sp, sc
        elif suffix == ".npy":
            try:
                import numpy as np

                arr = np.load(p, allow_pickle=False)
                if arr.size == 0:
                    scientific.append(QCIssue("NPY_EMPTY", "error", "Array vide"))
                notes.append(f"shape={getattr(arr, 'shape', None)} dtype={arr.dtype}")
            except Exception as exc:  # noqa: BLE001
                scientific.append(QCIssue("NPY_LOAD_FAIL", "error", str(exc)))
        else:
            notes.append(f"Extension {suffix} — QC générique (existence OK)")

    if geochem_rows is not None:
        geochemical.extend(check_geochemical_batch(geochem_rows))

    errors = sum(1 for i in spatial + temporal + scientific + geochemical if i.severity == "error")
    warnings = sum(
        1 for i in spatial + temporal + scientific + geochemical if i.severity == "warning"
    )
    infos = sum(1 for i in spatial + temporal + scientific + geochemical if i.severity == "info")
    dims = score_from_issues(errors=errors, warnings=warnings, infos=infos)
    return QCReport(
        dataset_id=dataset_id,
        path=str(p),
        ok=errors == 0,
        spatial=spatial,
        temporal=temporal,
        scientific=scientific,
        geochemical=geochemical,
        quality_score=float(dims["global_score"]),
        quality_dimensions=dims,
        checked_at=_now(),
        notes=notes,
    )


def run_qa_qc_dataset(dataset_id: str) -> QCReport:
    """QC d'un dataset du catalogue (chemin local si présent)."""
    record = get_dataset(dataset_id)
    if record is None:
        return QCReport(
            dataset_id=dataset_id,
            path="",
            ok=False,
            scientific=[QCIssue("UNKNOWN_DATASET", "error", f"Dataset inconnu: {dataset_id}")],
            quality_score=0.0,
            quality_dimensions=score_from_issues(file_missing=True),
            checked_at=_now(),
            notes=["Dataset absent du Data Catalog"],
        )
    if not record.local_path:
        return QCReport(
            dataset_id=dataset_id,
            path="",
            ok=True,
            scientific=[
                QCIssue(
                    "NO_LOCAL_FILE",
                    "info",
                    f"Pas de fichier local — disponibilité={record.availability}",
                )
            ],
            quality_score=record.quality.global_score(),
            quality_dimensions=record.quality.to_dict(),
            checked_at=_now(),
            notes=[
                "QC métadonnées uniquement (NOT_CONNECTED / à configurer).",
                record.note,
            ],
        )
    report = run_qa_qc_on_path(record.local_path, dataset_id=dataset_id)
    # Fusionne score catalogue (fiabilité source) avec QC fichier
    cat_q = record.quality.global_score()
    report.quality_score = round(0.5 * report.quality_score + 0.5 * cat_q, 1)
    report.notes.append(f"data_class={record.data_class}")
    report.notes.append(f"evidence_level={record.evidence_level}")
    return report


def run_qa_qc_catalog(*, only_local: bool = True) -> dict:
    """QC sur tous les datasets (ou ceux avec fichier local)."""
    reports = []
    for r in build_catalog():
        if only_local and not r.local_path:
            continue
        if only_local and r.local_path and not Path(r.local_path).exists():
            # Toujours reporter les chemins attendus manquants
            reports.append(run_qa_qc_dataset(r.dataset_id).to_dict())
            continue
        reports.append(run_qa_qc_dataset(r.dataset_id).to_dict())

    errors = sum(rep["error_count"] for rep in reports)
    warnings = sum(rep["warning_count"] for rep in reports)
    ok_n = sum(1 for rep in reports if rep["ok"])
    return {
        "checked_at": _now(),
        "datasets_checked": len(reports),
        "ok_count": ok_n,
        "total_errors": errors,
        "total_warnings": warnings,
        "reports": reports,
        "disclaimer": (
            "QA/QC contrôle intégrité spatiale/temporelle/scientifique des fichiers locaux. "
            "Il ne valide pas un gisement ni un permis CAMI."
        ),
    }


def data_quality_score_for_dataset(dataset_id: str) -> dict:
    """Score qualité distinct de la prospectivité."""
    record = get_dataset(dataset_id)
    report = run_qa_qc_dataset(dataset_id)
    return {
        "dataset_id": dataset_id,
        "name": record.name if record else dataset_id,
        "data_class": record.data_class if record else "UNAVAILABLE",
        "catalog_quality": record.quality.to_dict() if record else {},
        "qc_quality": report.quality_dimensions,
        "data_quality_score": report.quality_score,
        "prospectivity_score": "N/E",
        "note": "Data Quality Score ≠ Prospectivity Score",
        "qc_ok": report.ok,
        "errors": report.error_count(),
        "warnings": report.warning_count(),
    }
