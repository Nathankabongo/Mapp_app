"""Couches carte liées au moteur de prospectivité (emprise + raster)."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import numpy as np

from compass_core.analysis.favorability import GeoGrid, extract_hotspots, load_geogrid
from compass_core.analysis.site_evaluation import resolve_favorability_path
from compass_core.minerals.profiles import mineral_supports_raster
from compass_core.minerals.zone_knowledge import ATLAS_MINERAL_MAP

# Libellés filtre sidebar ↔ minerai libre
_MINERAL_TO_COMMODITY_LABEL: dict[str, list[str]] = {
    "cuivre": ["Cu-Co"],
    "cobalt": ["Cu-Co"],
    "germanium": ["Cu-Co"],
    "lithium": ["Lithium"],
    "or": ["Or (Au)"],
    "coltan": ["3T (Coltan)"],
    "tantale": ["3T (Coltan)"],
    "étain": ["3T (Coltan)"],
    "tungstène": ["3T (Coltan)"],
    "niobium": ["3T (Coltan)"],
    "diamant": ["Diamant"],
}


def commodity_labels_for_mineral(mineral: str) -> list[str]:
    return list(_MINERAL_TO_COMMODITY_LABEL.get((mineral or "").lower(), []))


def atlas_codes_for_mineral(mineral: str) -> list[str]:
    m = (mineral or "").lower()
    return [code for code, minerals in ATLAS_MINERAL_MAP.items() if m in minerals]


def favorability_png_data_uri(grid: GeoGrid, *, cmap: str = "YlOrRd") -> str:
    """PNG base64 (RGBA) pour Folium ImageOverlay."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    arr = np.clip(grid.values.astype(np.float32), 0.0, 1.0)
    # Masquer NoData / zéros hors zone utile (transparence)
    rgba = plt.get_cmap(cmap)(arr)
    rgba[..., 3] = np.where(arr > 0.02, 0.75, 0.0)
    fig = plt.figure(figsize=(arr.shape[1] / 32, arr.shape[0] / 32), dpi=96)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(rgba, origin="upper", interpolation="nearest")
    ax.axis("off")
    buf = BytesIO()
    fig.savefig(buf, format="png", transparent=True, pad_inches=0)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_prospectivity_map_layers(
    *,
    mineral: str,
    latitude: float,
    longitude: float,
    status: str,
    prospectivity_pct: float | None,
    prospectivity_level: str,
    in_bounds: bool,
    model_used: str,
) -> dict:
    """
    Prépare overlays carte pour la page MPM.

    Retourne hotspots, image_overlays, extent_overlays, highlight_popup, show_hotspots.
    """
    out: dict = {
        "hotspots": [],
        "show_hotspots": False,
        "image_overlays": [],
        "extent_overlays": [],
        "highlight_popup": "",
        "has_raster_for_mineral": False,
        "near_extent": False,
    }

    score_txt = (
        f"{prospectivity_pct:.0f} % · {prospectivity_level}"
        if prospectivity_pct is not None
        else "N/E — non évalué"
    )
    out["highlight_popup"] = (
        f"<b>Point MPM</b><br>"
        f"Minerai : {mineral}<br>"
        f"Prospectivité : <b>{score_txt}</b><br>"
        f"Modèle : {model_used}<br>"
        f"<i>PRÉDICTION IA — pas un gisement confirmé</i>"
    )

    if not mineral_supports_raster(mineral):
        return out

    path = resolve_favorability_path()
    if path is None or not Path(path).exists():
        return out

    try:
        grid = load_geogrid(path)
    except Exception:
        return out

    out["has_raster_for_mineral"] = True
    south, west, north, east = grid.extent_wgs84()
    # N'afficher le raster que si la vue est près de l'emprise (évite Kolwezi sur Kibali)
    pad = 0.35  # ~40 km
    near_extent = (south - pad) <= latitude <= (north + pad) and (west - pad) <= longitude <= (
        east + pad
    )
    out["near_extent"] = near_extent or in_bounds

    if out["near_extent"]:
        poly = grid.extent_polygon_wgs84()
        out["extent_overlays"].append(
            {
                "polygon": poly,
                "label": f"Emprise raster pilote ({Path(path).name})",
                "fill": "#38BDF8" if in_bounds else "#94A3B8",
                "color": "#0284C7" if in_bounds else "#64748B",
                "fill_opacity": 0.06,
                "dash": "4 4" if not in_bounds else None,
            }
        )
        try:
            uri = favorability_png_data_uri(grid)
            out["image_overlays"].append(
                {
                    "image": uri,
                    "bounds": [[south, west], [north, east]],
                    "opacity": 0.55 if status == "evaluated" else 0.35,
                    "name": "Carte de prospectivité (pilote)",
                }
            )
        except Exception:
            pass

    if status == "evaluated" and in_bounds:
        from compass_core.analysis.coordinates import wgs84_to_utm

        ux, uy = wgs84_to_utm(latitude, longitude, epsg=grid.crs_epsg)
        hotspots = extract_hotspots(
            grid,
            center_utm_x=ux,
            center_utm_y=uy,
            threshold=0.7,
            max_distance_m=12_000.0,
            max_zones=8,
        )
        out["hotspots"] = hotspots
        out["show_hotspots"] = bool(hotspots)

    return out
