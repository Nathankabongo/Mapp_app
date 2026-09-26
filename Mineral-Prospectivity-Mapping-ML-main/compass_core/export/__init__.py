"""Export SIG (GeoTIFF, GeoPackage) et rapports PDF."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import box

from compass_core.data.raster import write_raster


def export_geotiff(
    reference_raster: str | Path,
    prediction_map: np.ndarray,
    output_path: str | Path,
) -> Path:
    return write_raster(reference_raster, prediction_map, output_path)


def export_geopackage_contours(
    reference_raster: str | Path,
    prediction_map: np.ndarray,
    output_path: str | Path,
    *,
    threshold: float = 0.7,
) -> Path:
    """
    Exporte les zones à haute favorabilité en polygones GeoPackage (compatible QGIS).
    """
    from compass_core.data.gdal_compat import import_gdal

    gdal = import_gdal()
    reference = gdal.Open(str(reference_raster))
    if reference is None:
        raise FileNotFoundError(f"Raster introuvable : {reference_raster}")

    transform = reference.GetGeoTransform()
    rows, cols = prediction_map.shape
    high_mask = prediction_map >= threshold

    if not high_mask.any():
        gdf = gpd.GeoDataFrame(
            {"favorability": [], "geometry": []},
            crs="EPSG:4326",
        )
    else:
        min_row, max_row = np.where(high_mask.any(axis=1))[0][[0, -1]]
        min_col, max_col = np.where(high_mask.any(axis=0))[0][[0, -1]]
        x_min = transform[0] + min_col * transform[1]
        x_max = transform[0] + (max_col + 1) * transform[1]
        y_max = transform[3] + min_row * transform[5]
        y_min = transform[3] + (max_row + 1) * transform[5]
        mean_score = float(prediction_map[high_mask].mean())
        gdf = gpd.GeoDataFrame(
            {
                "favorability": [mean_score],
                "threshold": [threshold],
                "geometry": [box(x_min, y_min, x_max, y_max)],
            }
        )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out, driver="GPKG")
    return out


def export_pdf_report(
    output_path: str | Path,
    *,
    project_name: str,
    metrics: dict[str, float],
    region: dict[str, str],
) -> Path | None:
    """Génère un rapport PDF minimal (optionnel, nécessite reportlab)."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        return None

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(out), pagesize=A4)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, 800, f"CriticalMineralsCompass — {project_name}")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 780, f"Région : {region.get('name', 'N/A')} ({region.get('province', '')})")
    pdf.drawString(50, 765, f"Commodité : {region.get('commodity', 'N/A')}")
    y = 740
    pdf.drawString(50, y, "Métriques de validation :")
    y -= 20
    for key, value in metrics.items():
        pdf.drawString(70, y, f"{key}: {value:.4f}")
        y -= 16
    pdf.save()
    return out
