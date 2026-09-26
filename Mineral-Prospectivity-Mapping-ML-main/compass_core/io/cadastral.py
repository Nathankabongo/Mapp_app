"""Cadastre — chargement local uniquement, jamais d'invention de permis."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from compass_core.analysis.mineral_layers import load_cadastre
from compass_core.constants import UNAVAILABLE


def load_cadastral_layer(atlas_dir: Path | None = None) -> gpd.GeoDataFrame | None:
    """Charge la couche cadastrale locale si le fichier existe."""
    if atlas_dir is None:
        return load_cadastre()
    return load_cadastre(atlas_dir)


def lookup_permit(latitude: float, longitude: float) -> dict[str, str]:
    """
    Interroge le cadastre local au point.

    Ne fabrique jamais un statut. Si aucun polygone ne contient le point,
    retourne UNAVAILABLE avec official=False.
    """
    from shapely.geometry import Point

    cadastre = load_cadastral_layer()
    empty = {
        "status_label": UNAVAILABLE,
        "numero": "",
        "type": "",
        "titulaire": "",
        "source": "",
        "official": "Non",
        "data_class": "unavailable",
        "verifiable": "Non",
    }
    if cadastre is None or cadastre.empty:
        return empty

    point = Point(longitude, latitude)
    wgs = cadastre.to_crs(epsg=4326)
    hits = wgs[wgs.contains(point)]
    if hits.empty:
        return empty

    row = hits.iloc[0]
    source = str(row.get("source", ""))
    official = source.lower() in {"cami", "cami_officiel", "rdc.mines-rdc.cd"}
    numero = str(row.get("numero_permis", "") or "")
    statut = str(row.get("statut", "") or "")
    if not numero and not statut:
        return empty

    data_class = "official" if official else "demo" if "demo" in source.lower() else "open"
    return {
        "status_label": statut or UNAVAILABLE,
        "numero": numero,
        "type": statut,
        "titulaire": str(row.get("titulaire", "") or UNAVAILABLE),
        "source": source or UNAVAILABLE,
        "official": "Oui" if official else "Non",
        "data_class": data_class,
        "verifiable": "Oui" if official else "Non",
        "province": str(row.get("province", "") or UNAVAILABLE),
        "commodity": str(row.get("commodity", "") or UNAVAILABLE),
    }
