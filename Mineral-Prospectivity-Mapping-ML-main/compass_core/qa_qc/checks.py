"""Moteur QA/QC géoscientifique — spatial, temporel, scientifique, géochimique."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class QCIssue:
    code: str
    severity: str  # error | warning | info
    message: str
    field: str = ""
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QCReport:
    dataset_id: str
    path: str
    ok: bool
    spatial: list[QCIssue] = field(default_factory=list)
    temporal: list[QCIssue] = field(default_factory=list)
    scientific: list[QCIssue] = field(default_factory=list)
    geochemical: list[QCIssue] = field(default_factory=list)
    quality_score: float = 0.0
    quality_dimensions: dict[str, float] = field(default_factory=dict)
    checked_at: str = ""
    notes: list[str] = field(default_factory=list)

    def all_issues(self) -> list[QCIssue]:
        return self.spatial + self.temporal + self.scientific + self.geochemical

    def error_count(self) -> int:
        return sum(1 for i in self.all_issues() if i.severity == "error")

    def warning_count(self) -> int:
        return sum(1 for i in self.all_issues() if i.severity == "warning")

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "path": self.path,
            "ok": self.ok,
            "spatial": [i.to_dict() for i in self.spatial],
            "temporal": [i.to_dict() for i in self.temporal],
            "scientific": [i.to_dict() for i in self.scientific],
            "geochemical": [i.to_dict() for i in self.geochemical],
            "error_count": self.error_count(),
            "warning_count": self.warning_count(),
            "quality_score": self.quality_score,
            "quality_dimensions": self.quality_dimensions,
            "checked_at": self.checked_at,
            "notes": self.notes,
        }


# Emprise approximative RDC (WGS84) pour contrôles hors-pays
RDC_BBOX = {
    "min_lon": 12.0,
    "max_lon": 32.0,
    "min_lat": -14.0,
    "max_lat": 6.0,
}


def check_coordinates(
    lon: float | None,
    lat: float | None,
    *,
    require_rdc: bool = True,
) -> list[QCIssue]:
    issues: list[QCIssue] = []
    if lon is None or lat is None:
        issues.append(
            QCIssue("COORD_MISSING", "error", "Coordonnées manquantes", "lon/lat")
        )
        return issues
    try:
        lon_f = float(lon)
        lat_f = float(lat)
    except (TypeError, ValueError):
        issues.append(
            QCIssue("COORD_INVALID", "error", f"Coordonnées non numériques: {lon},{lat}")
        )
        return issues
    if not (-180 <= lon_f <= 180 and -90 <= lat_f <= 90):
        issues.append(
            QCIssue(
                "COORD_OOR",
                "error",
                f"Coordonnées hors plage WGS84: lon={lon_f}, lat={lat_f}",
            )
        )
    elif require_rdc and not (
        RDC_BBOX["min_lon"] <= lon_f <= RDC_BBOX["max_lon"]
        and RDC_BBOX["min_lat"] <= lat_f <= RDC_BBOX["max_lat"]
    ):
        issues.append(
            QCIssue(
                "COORD_OUTSIDE_RDC",
                "warning",
                f"Point hors emprise approximative RDC: ({lat_f}, {lon_f})",
                "lon/lat",
                (lon_f, lat_f),
            )
        )
    return issues


def check_date_value(value: Any, *, field_name: str = "date") -> list[QCIssue]:
    issues: list[QCIssue] = []
    if value is None or value == "" or str(value).upper() in ("N/E", "NA", "NULL"):
        issues.append(
            QCIssue("DATE_MISSING", "info", f"Date absente ({field_name})", field_name)
        )
        return issues
    text = str(value).strip()
    parsed = None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y"):
        try:
            parsed = datetime.strptime(text[: len(fmt) + 8], fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        # Essai ISO
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            issues.append(
                QCIssue("DATE_INVALID", "warning", f"Date invalide: {text}", field_name)
            )
            return issues
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if parsed.replace(tzinfo=None) > now:
        issues.append(
            QCIssue("DATE_FUTURE", "warning", f"Date future: {text}", field_name)
        )
    age_years = (now - parsed.replace(tzinfo=None)).days / 365.25
    if age_years > 50:
        issues.append(
            QCIssue(
                "DATE_STALE",
                "info",
                f"Donnée ancienne ({age_years:.0f} ans): {text}",
                field_name,
            )
        )
    return issues


def check_numeric_scientific(
    value: Any,
    *,
    field_name: str,
    unit: str | None = None,
    detection_limit: float | None = None,
    allow_negative: bool = False,
) -> list[QCIssue]:
    issues: list[QCIssue] = []
    if value is None or value == "" or str(value).upper() in ("N/E", "NA", "NULL"):
        issues.append(
            QCIssue("VALUE_MISSING", "warning", f"Valeur manquante ({field_name})", field_name)
        )
        return issues
    try:
        num = float(value)
    except (TypeError, ValueError):
        issues.append(
            QCIssue(
                "VALUE_NON_NUMERIC",
                "error",
                f"Valeur non numérique ({field_name}): {value}",
                field_name,
            )
        )
        return issues
    if not allow_negative and num < 0:
        issues.append(
            QCIssue(
                "VALUE_NEGATIVE",
                "warning",
                f"Valeur négative ({field_name}): {num}",
                field_name,
                num,
            )
        )
    if detection_limit is not None and 0 < num < detection_limit:
        issues.append(
            QCIssue(
                "BELOW_LOD",
                "info",
                f"Valeur sous limite de détection ({num} < {detection_limit})",
                field_name,
                num,
            )
        )
    if unit is None or str(unit).strip() == "":
        issues.append(
            QCIssue("UNIT_MISSING", "warning", f"Unité absente ({field_name})", "unit")
        )
    return issues


def check_geochemical_batch(rows: list[dict[str, Any]]) -> list[QCIssue]:
    """Contrôles géochimiques de base (standards, blancs, duplicatas) si colonnes présentes."""
    issues: list[QCIssue] = []
    if not rows:
        issues.append(
            QCIssue("GEOCHEM_EMPTY", "error", "Aucun échantillon géochimique fourni")
        )
        return issues

    sample_types = [str(r.get("sample_type", r.get("type", ""))).lower() for r in rows]
    has_blank = any("blank" in t or "blanc" in t for t in sample_types)
    has_standard = any("std" in t or "standard" in t or "crm" in t for t in sample_types)
    has_dup = any("dup" in t or "duplicate" in t or "replicat" in t for t in sample_types)

    if not has_blank:
        issues.append(
            QCIssue(
                "GEOCHEM_NO_BLANK",
                "warning",
                "Aucun blanc (blank) détecté dans le lot — QA/QC incomplet",
            )
        )
    if not has_standard:
        issues.append(
            QCIssue(
                "GEOCHEM_NO_STANDARD",
                "warning",
                "Aucun standard/CRM détecté dans le lot — biais non contrôlable",
            )
        )
    if not has_dup:
        issues.append(
            QCIssue(
                "GEOCHEM_NO_DUP",
                "info",
                "Aucun duplicata détecté — précision analytique non estimable",
            )
        )

    # Doublons spatiaux approximatifs
    seen: dict[tuple[float, float], int] = {}
    for i, r in enumerate(rows):
        try:
            lon = round(float(r.get("lon", r.get("x", r.get("longitude")))), 5)
            lat = round(float(r.get("lat", r.get("y", r.get("latitude")))), 5)
        except (TypeError, ValueError):
            continue
        key = (lon, lat)
        if key in seen:
            issues.append(
                QCIssue(
                    "GEOCHEM_SPATIAL_DUP",
                    "info",
                    f"Points quasi-identiques lignes {seen[key]} et {i}",
                    "lon/lat",
                    key,
                )
            )
        else:
            seen[key] = i
    return issues


def check_vector_file(path: str | Path) -> tuple[list[QCIssue], list[QCIssue], list[QCIssue]]:
    """QC spatial/temporel/scientifique sur GPKG/GeoJSON/SHP si geopandas dispo."""
    spatial: list[QCIssue] = []
    temporal: list[QCIssue] = []
    scientific: list[QCIssue] = []
    p = Path(path)
    if not p.exists():
        spatial.append(QCIssue("FILE_MISSING", "error", f"Fichier introuvable: {p}"))
        return spatial, temporal, scientific

    try:
        import geopandas as gpd
    except ImportError:
        scientific.append(
            QCIssue(
                "GEOPANDAS_MISSING",
                "warning",
                "geopandas indisponible — QC vectoriel limité à l'existence du fichier",
            )
        )
        return spatial, temporal, scientific

    try:
        gdf = gpd.read_file(p)
    except Exception as exc:  # noqa: BLE001 — QC doit capturer tout échec lecture
        spatial.append(QCIssue("READ_FAIL", "error", f"Lecture impossible: {exc}"))
        return spatial, temporal, scientific

    if gdf.empty:
        scientific.append(QCIssue("EMPTY_LAYER", "error", "Couche vide"))
        return spatial, temporal, scientific

    if gdf.crs is None:
        spatial.append(
            QCIssue("CRS_MISSING", "error", "CRS absent — reprojection impossible")
        )
    else:
        try:
            epsg = gdf.crs.to_epsg()
            if epsg is None:
                spatial.append(
                    QCIssue("CRS_UNKNOWN", "warning", f"CRS non EPSG: {gdf.crs}")
                )
        except Exception:  # noqa: BLE001
            spatial.append(QCIssue("CRS_PARSE", "warning", "Impossible de lire l'EPSG"))

    # Géométries invalides
    try:
        invalid = ~gdf.geometry.is_valid
        n_inv = int(invalid.sum())
        if n_inv:
            spatial.append(
                QCIssue(
                    "GEOM_INVALID",
                    "error",
                    f"{n_inv} géométrie(s) invalide(s)",
                    "geometry",
                    n_inv,
                )
            )
    except Exception:  # noqa: BLE001
        spatial.append(QCIssue("GEOM_CHECK_FAIL", "warning", "Contrôle géométrie échoué"))

    null_geom = gdf.geometry.isna().sum()
    if null_geom:
        spatial.append(
            QCIssue(
                "GEOM_NULL",
                "error",
                f"{int(null_geom)} géométrie(s) nulle(s)",
                "geometry",
            )
        )

    # Doublons géométriques
    try:
        wkt = gdf.geometry.to_wkt()
        n_dup = int(wkt.duplicated().sum())
        if n_dup:
            spatial.append(
                QCIssue(
                    "GEOM_DUP",
                    "warning",
                    f"{n_dup} géométrie(s) dupliquée(s)",
                    "geometry",
                    n_dup,
                )
            )
    except Exception:  # noqa: BLE001
        pass

    # Hors RDC (centroïdes en 4326)
    try:
        gdf4326 = gdf.to_crs(4326) if gdf.crs and gdf.crs.to_epsg() != 4326 else gdf
        cents = gdf4326.geometry.centroid
        outside = 0
        for pt in cents:
            if pt is None or pt.is_empty:
                continue
            if not (
                RDC_BBOX["min_lon"] <= pt.x <= RDC_BBOX["max_lon"]
                and RDC_BBOX["min_lat"] <= pt.y <= RDC_BBOX["max_lat"]
            ):
                outside += 1
        if outside:
            spatial.append(
                QCIssue(
                    "FEATURES_OUTSIDE_RDC",
                    "warning",
                    f"{outside} entité(s) hors emprise RDC approximative",
                    value=outside,
                )
            )
    except Exception:  # noqa: BLE001
        spatial.append(
            QCIssue("RDC_BOUNDS_CHECK_FAIL", "info", "Contrôle emprise RDC non effectué")
        )

    # Colonnes dates
    for col in gdf.columns:
        cl = col.lower()
        if "date" in cl or cl in ("annee", "year", "updated", "published"):
            sample = gdf[col].dropna().head(20)
            for val in sample:
                temporal.extend(check_date_value(val, field_name=col))

    # Colonnes numériques suspectes
    for col in gdf.select_dtypes(include="number").columns:
        series = gdf[col]
        if series.isna().all():
            scientific.append(
                QCIssue("COL_ALL_NA", "warning", f"Colonne entièrement NA: {col}", col)
            )
        elif (series == 0).all():
            scientific.append(
                QCIssue("COL_ALL_ZERO", "info", f"Colonne entièrement à 0: {col}", col)
            )

    return spatial, temporal, scientific


def check_raster_file(path: str | Path) -> tuple[list[QCIssue], list[QCIssue]]:
    spatial: list[QCIssue] = []
    scientific: list[QCIssue] = []
    p = Path(path)
    if not p.exists():
        spatial.append(QCIssue("FILE_MISSING", "error", f"Raster introuvable: {p}"))
        return spatial, scientific

    try:
        from compass_core.data.gdal_compat import import_gdal

        gdal = import_gdal()
        ds = gdal.Open(str(p))
        if ds is None:
            spatial.append(QCIssue("RASTER_OPEN_FAIL", "error", f"GDAL Open échoué: {p}"))
            return spatial, scientific
        if ds.RasterCount < 1:
            scientific.append(QCIssue("RASTER_NO_BAND", "error", "Aucune bande"))
        gt = ds.GetGeoTransform()
        if gt is None:
            spatial.append(QCIssue("GEOTRANSFORM_MISSING", "error", "GeoTransform absent"))
        proj = ds.GetProjection()
        if not proj:
            spatial.append(QCIssue("CRS_MISSING", "warning", "Projection raster absente"))
        # Nodata / stats bande 1
        band = ds.GetRasterBand(1)
        arr = band.ReadAsArray()
        if arr is None:
            scientific.append(QCIssue("RASTER_EMPTY", "error", "Bande 1 vide"))
        else:
            import numpy as np

            if np.all(np.isnan(arr.astype(float))):
                scientific.append(QCIssue("RASTER_ALL_NAN", "error", "Bande entièrement NaN"))
        ds = None
    except ImportError:
        scientific.append(
            QCIssue(
                "GDAL_MISSING",
                "warning",
                "GDAL indisponible — QC raster limité à l'existence du fichier",
            )
        )
    except Exception as exc:  # noqa: BLE001
        scientific.append(QCIssue("RASTER_QC_FAIL", "warning", f"QC raster: {exc}"))
    return spatial, scientific


def score_from_issues(
    *,
    base: float = 80.0,
    errors: int = 0,
    warnings: int = 0,
    infos: int = 0,
    file_missing: bool = False,
) -> dict[str, float]:
    """Calcule dimensions qualité à partir des issues QC."""
    if file_missing:
        return {
            "completeness": 0.0,
            "accuracy": 0.0,
            "consistency": 0.0,
            "recency": 0.0,
            "spatial_resolution": 0.0,
            "source_reliability": 0.0,
            "scientific_quality": 0.0,
            "processing_quality": 0.0,
            "global_score": 0.0,
        }
    penalty = errors * 15 + warnings * 5 + infos * 1
    global_score = max(0.0, min(100.0, base - penalty))
    consistency = max(0.0, 100.0 - errors * 20 - warnings * 8)
    accuracy = max(0.0, 100.0 - errors * 18 - warnings * 6)
    scientific = max(0.0, 90.0 - errors * 12 - warnings * 5)
    return {
        "completeness": round(min(100.0, base), 1),
        "accuracy": round(accuracy, 1),
        "consistency": round(consistency, 1),
        "recency": 50.0,
        "spatial_resolution": 50.0,
        "source_reliability": round(max(20.0, 90.0 - errors * 10), 1),
        "scientific_quality": round(scientific, 1),
        "processing_quality": round(global_score, 1),
        "global_score": round(global_score, 1),
    }
