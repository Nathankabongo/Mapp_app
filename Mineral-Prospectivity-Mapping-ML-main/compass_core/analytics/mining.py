"""Agrégats miniers pour tableaux et KPI."""

from __future__ import annotations

import pandas as pd

from compass_core.analysis.mineral_layers import STATUS_LABELS, load_all_layers
from compass_core.analysis.atlas_catalog import load_catalog


def sites_table(province: str | None = None) -> pd.DataFrame:
    catalog = load_catalog()
    rows: list[dict] = []
    for code, gdf in load_all_layers(province=province).items():
        meta = catalog.layers.get(code)
        wgs = gdf.to_crs(epsg=4326)
        for _, row in wgs.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            src = str(row.get("source", "atlas"))
            rows.append(
                {
                    "Site": row.get("name", meta.label if meta else code),
                    "Province": row.get("province", ""),
                    "Territoire": row.get("territoire", ""),
                    "Minerai": meta.label if meta else code,
                    "code": code,
                    "Statut": STATUS_LABELS.get(str(row.get("status", "")), row.get("status", "")),
                    "status_code": row.get("status", ""),
                    "Latitude": round(float(geom.y), 5),
                    "Longitude": round(float(geom.x), 5),
                    "Source": src,
                    "Type": row.get("deposit_type", ""),
                    "Formation": row.get("geological_formation", ""),
                    "data_class": "demo" if "demo" in src else "historical",
                }
            )
    return pd.DataFrame(rows)


def top_commodities(n: int = 5) -> list[tuple[str, int]]:
    df = sites_table()
    if df.empty:
        return []
    counts = df["Minerai"].value_counts().head(n)
    return list(zip(counts.index.tolist(), counts.tolist()))


def top_provinces(n: int = 5) -> list[tuple[str, int]]:
    df = sites_table()
    if df.empty:
        return []
    counts = df["Province"].replace("", pd.NA).dropna().value_counts().head(n)
    return list(zip(counts.index.tolist(), counts.tolist()))
