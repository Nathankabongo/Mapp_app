"""Contrôles QA/QC spatiaux."""

from __future__ import annotations

from pathlib import Path

from compass_core.qa_qc.scores import QCIssue

# Emprise approximative RDC (WGS84)
RDC_BBOX = (-13.5, 12.0, 5.5, 31.5)  # min_lat, max_lat, min_lon, max_lon


def check_wgs84_point(lat: float, lon: float) -> list[QCIssue]:
    issues: list[QCIssue] = []
    if not (-90 <= lat <= 90):
        issues.append(
            QCIssue("COORD_LAT_INVALID", "error", f"Latitude invalide: {lat}", "latitude")
        )
    if not (-180 <= lon <= 180):
        issues.append(
            QCIssue("COORD_LON_INVALID", "error", f"Longitude invalide: {lon}", "longitude")
        )
    min_lat, max_lat, min_lon, max_lon = RDC_BBOX
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
            issues.append(
                QCIssue(
                    "COORD_OUTSIDE_RDC",
                    "warning",
                    f"Point hors emprise approximative RDC ({lat:.4f}, {lon:.4f})",
                    "geometry",
                )
            )
    return issues


def check_geodataframe_spatial(gdf, *, expect_crs: str | None = "EPSG:4326") -> tuple[list[QCIssue], dict]:
    """Contrôle spatial GeoDataFrame (geopandas optionnel)."""
    issues: list[QCIssue] = []
    stats = {
        "n_features": 0,
        "n_invalid_geom": 0,
        "n_empty_geom": 0,
        "n_null_geom": 0,
        "n_outside_rdc": 0,
        "n_duplicate_geom": 0,
        "crs": None,
    }
    if gdf is None:
        issues.append(QCIssue("GDF_NONE", "error", "GeoDataFrame absent"))
        return issues, stats

    stats["n_features"] = len(gdf)
    stats["crs"] = str(gdf.crs) if gdf.crs else None

    if gdf.crs is None:
        issues.append(QCIssue("CRS_MISSING", "error", "CRS manquant", "crs"))
    elif expect_crs and str(gdf.crs).upper() not in {
        expect_crs.upper(),
        expect_crs.replace("EPSG:", "").upper(),
        f"EPSG:{expect_crs}" if expect_crs.isdigit() else expect_crs.upper(),
    }:
        # Tolérer UTM Kolwezi pour couches pilote
        crs_s = str(gdf.crs).upper()
        if "32733" not in crs_s and "4326" not in crs_s:
            issues.append(
                QCIssue(
                    "CRS_UNEXPECTED",
                    "warning",
                    f"CRS={gdf.crs} (attendu {expect_crs} ou EPSG:32733 pilote)",
                    "crs",
                )
            )

    if "geometry" not in gdf.columns and gdf.geometry is None:
        issues.append(QCIssue("GEOM_COLUMN_MISSING", "error", "Colonne geometry absente"))
        return issues, stats

    null_mask = gdf.geometry.isna()
    stats["n_null_geom"] = int(null_mask.sum())
    if stats["n_null_geom"]:
        issues.append(
            QCIssue(
                "GEOM_NULL",
                "error",
                f"{stats['n_null_geom']} géométrie(s) nulle(s)",
                "geometry",
            )
        )

    try:
        empty = gdf.geometry.is_empty.fillna(False)
        stats["n_empty_geom"] = int(empty.sum())
        if stats["n_empty_geom"]:
            issues.append(
                QCIssue(
                    "GEOM_EMPTY",
                    "error",
                    f"{stats['n_empty_geom']} géométrie(s) vide(s)",
                    "geometry",
                )
            )
    except Exception:  # noqa: BLE001 — backends géométriques variables
        pass

    try:
        valid = gdf.geometry.is_valid
        invalid = (~valid.fillna(False)) & gdf.geometry.notna()
        stats["n_invalid_geom"] = int(invalid.sum())
        if stats["n_invalid_geom"]:
            issues.append(
                QCIssue(
                    "GEOM_INVALID",
                    "error",
                    f"{stats['n_invalid_geom']} géométrie(s) invalide(s)",
                    "geometry",
                )
            )
    except Exception:  # noqa: BLE001
        pass

    # Doublons spatiaux (WKT)
    try:
        wkt = gdf.geometry.to_wkt()
        dup = wkt.duplicated(keep=False) & wkt.notna()
        stats["n_duplicate_geom"] = int(dup.sum())
        if stats["n_duplicate_geom"]:
            issues.append(
                QCIssue(
                    "GEOM_DUPLICATE",
                    "warning",
                    f"{stats['n_duplicate_geom']} géométrie(s) dupliquée(s)",
                    "geometry",
                )
            )
    except Exception:  # noqa: BLE001
        pass

    # Hors RDC (centroïdes en 4326)
    try:
        work = gdf
        if gdf.crs and "4326" not in str(gdf.crs):
            work = gdf.to_crs(epsg=4326)
        cents = work.geometry.centroid
        min_lat, max_lat, min_lon, max_lon = RDC_BBOX
        outside = 0
        for y, x in zip(cents.y, cents.x, strict=False):
            if y != y or x != x:  # NaN
                continue
            if not (min_lat <= float(y) <= max_lat and min_lon <= float(x) <= max_lon):
                outside += 1
        stats["n_outside_rdc"] = outside
        if outside:
            issues.append(
                QCIssue(
                    "GEOM_OUTSIDE_RDC",
                    "warning",
                    f"{outside} entité(s) hors emprise RDC approximative",
                    "geometry",
                )
            )
    except Exception:  # noqa: BLE001
        pass

    return issues, stats


def check_vector_file(path: str | Path, *, expect_crs: str | None = "EPSG:4326") -> tuple[list[QCIssue], dict]:
    path = Path(path)
    issues: list[QCIssue] = []
    if not path.exists():
        issues.append(QCIssue("FILE_MISSING", "error", f"Fichier absent: {path}"))
        return issues, {"path": str(path), "exists": False}
    try:
        import geopandas as gpd

        gdf = gpd.read_file(path)
    except ImportError:
        issues.append(
            QCIssue(
                "GEOPANDAS_MISSING",
                "warning",
                "geopandas indisponible — contrôle spatial limité",
            )
        )
        return issues, {"path": str(path), "exists": True, "checked": False}
    except Exception as exc:  # noqa: BLE001
        issues.append(QCIssue("FILE_READ_ERROR", "error", f"Lecture impossible: {exc}"))
        return issues, {"path": str(path), "exists": True, "error": str(exc)}

    spat_issues, stats = check_geodataframe_spatial(gdf, expect_crs=expect_crs)
    stats["path"] = str(path)
    stats["exists"] = True
    stats["checked"] = True
    return issues + spat_issues, stats
