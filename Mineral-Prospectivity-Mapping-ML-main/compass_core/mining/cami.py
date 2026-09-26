"""Connecteur CAMI — import uniquement, jamais d'invention."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from compass_core.api.connectors import CamiConnector
from compass_core.constants import UNAVAILABLE


OFFICIAL_PATHS = (
    Path("data/rdc/official/cami_permits.gpkg"),
    Path("data/rdc/official/cami_permits.geojson"),
    Path("data/rdc/official/cami_permits.csv"),
)


def verified_concession_count() -> int:
    """Toujours 0 tant qu'aucun export CAMI officiel n'est chargé."""
    for p in OFFICIAL_PATHS:
        if p.exists() and p.suffix in {".gpkg", ".geojson"}:
            try:
                gdf = gpd.read_file(p)
                return len(gdf)
            except Exception:
                return 0
        if p.exists() and p.suffix == ".csv":
            try:
                import pandas as pd

                return len(pd.read_csv(p))
            except Exception:
                return 0
    return 0


def cami_status() -> dict:
    probe = CamiConnector().probe()
    return {
        "status": probe.status,
        "message": probe.message,
        "verified_count": verified_concession_count(),
        "data_class": probe.data_class,
        "path": probe.path,
        "note": "Concessions vérifiées = 0 sans export CAMI officiel.",
    }


def import_cami_file(path: str | Path) -> dict:
    """Valide un fichier importé — ne crée pas de permis fictifs."""
    p = Path(path)
    if not p.exists():
        return {"ok": False, "message": UNAVAILABLE}
    dest_dir = Path("data/rdc/official")
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Copie logique : l'appelant place le fichier ; ici on lit et compte
    try:
        if p.suffix.lower() in {".gpkg", ".geojson", ".shp"}:
            gdf = gpd.read_file(p)
            return {
                "ok": True,
                "count": len(gdf),
                "crs": str(gdf.crs),
                "columns": list(gdf.columns),
                "data_class": "official" if "cami" in p.name.lower() or "official" in str(p) else "imported",
                "message": f"{len(gdf)} entités lues — à placer sous data/rdc/official/ pour compter comme vérifiées.",
            }
        if p.suffix.lower() == ".csv":
            import pandas as pd

            df = pd.read_csv(p)
            return {"ok": True, "count": len(df), "columns": list(df.columns), "data_class": "imported"}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}
    return {"ok": False, "message": "Format non supporté"}
