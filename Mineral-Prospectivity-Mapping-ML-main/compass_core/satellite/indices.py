"""Indices spectraux — calcul uniquement si raster fourni."""

from __future__ import annotations

from pathlib import Path

from compass_core.constants import UNAVAILABLE


def ndvi_status(raster_path: str | Path | None = None) -> dict:
    """NDVI réel nécessite bandes NIR/Red — sinon non disponible."""
    if raster_path and Path(raster_path).exists():
        # Le stack Kolwezi n'est pas un Sentinel-2 → on ne calcule pas un faux NDVI
        return {
            "status": "NON DISPONIBLE",
            "value": None,
            "message": (
                "Raster présent mais ce n'est pas une scène Sentinel-2/Landsat calibrée. "
                "NDVI non calculé pour éviter une fausse observation."
            ),
            "data_class": "unavailable",
        }
    return {
        "status": "NON DISPONIBLE",
        "value": None,
        "message": UNAVAILABLE + " — fournir une scène optique avec bandes NIR/Red.",
        "data_class": "unavailable",
    }
