"""Import / export forages (CSV)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from compass_core.drillholes.models import Collar, Drillhole, Interval, SurveyStation


REQUIRED_COLLAR = ("hole_id", "x", "y", "z", "depth_m")


def load_collars_csv(path: str | Path) -> list[Collar]:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLLAR if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes collar manquantes : {missing}")
    collars = []
    for _, row in df.iterrows():
        collars.append(
            Collar(
                hole_id=str(row["hole_id"]),
                x=float(row["x"]),
                y=float(row["y"]),
                z=float(row["z"]),
                azimuth=float(row["azimuth"]) if "azimuth" in df.columns and pd.notna(row.get("azimuth")) else 0.0,
                dip=float(row["dip"]) if "dip" in df.columns and pd.notna(row.get("dip")) else -90.0,
                depth_m=float(row["depth_m"]),
                crs=str(row["crs"]) if "crs" in df.columns else "EPSG:4326",
                data_class=str(row["data_class"]) if "data_class" in df.columns else "imported",
                source=str(row["source"]) if "source" in df.columns else str(path),
            )
        )
    return collars


def load_intervals_csv(path: str | Path) -> list[Interval]:
    df = pd.read_csv(path)
    for col in ("hole_id", "from_m", "to_m"):
        if col not in df.columns:
            raise ValueError(f"Colonne intervalle manquante : {col}")
    out = []
    for _, row in df.iterrows():
        assay_val = None
        assay_el = None
        assay_unit = None
        assay_class = "unavailable"
        if "assay_value" in df.columns and pd.notna(row.get("assay_value")):
            assay_val = float(row["assay_value"])
            assay_el = str(row["assay_element"]) if "assay_element" in df.columns else None
            assay_unit = str(row["assay_unit"]) if "assay_unit" in df.columns else "%"
            assay_class = str(row["assay_data_class"]) if "assay_data_class" in df.columns else "measured"
        out.append(
            Interval(
                hole_id=str(row["hole_id"]),
                from_m=float(row["from_m"]),
                to_m=float(row["to_m"]),
                lithology=str(row["lithology"]) if "lithology" in df.columns and pd.notna(row.get("lithology")) else "",
                alteration=str(row["alteration"]) if "alteration" in df.columns and pd.notna(row.get("alteration")) else "",
                mineralization=str(row["mineralization"]) if "mineralization" in df.columns and pd.notna(row.get("mineralization")) else "",
                assay_element=assay_el,
                assay_value=assay_val,
                assay_unit=assay_unit,
                assay_data_class=assay_class,
            )
        )
    return out


def assemble_drillholes(
    collars: list[Collar],
    intervals: list[Interval] | None = None,
    surveys: list[SurveyStation] | None = None,
) -> list[Drillhole]:
    intervals = intervals or []
    surveys = surveys or []
    by_hole: dict[str, Drillhole] = {
        c.hole_id: Drillhole(collar=c) for c in collars
    }
    for iv in intervals:
        if iv.hole_id in by_hole:
            by_hole[iv.hole_id].intervals.append(iv)
    for sv in surveys:
        if sv.hole_id in by_hole:
            by_hole[sv.hole_id].surveys.append(sv)
    return list(by_hole.values())
