"""Traitement des échantillons vectoriels (GeoPackage / Shapefile)."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np


def split_samples(
    samples_path: str | Path,
    train_path: str | Path,
    test_path: str | Path,
    *,
    train_fraction: float = 0.8,
    label_field: str = "Value",
    seed: int = 42,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Divise les points d'échantillonnage en jeux train/test.

    Attend un champ binaire (0 = absence, 1 = présence du minéral cible).
    Migré depuis ``Data_preprocessing.target_variable``.
    """
    gdf = gpd.read_file(samples_path)
    if label_field not in gdf.columns:
        raise KeyError(
            f"Champ '{label_field}' absent du fichier échantillons. "
            f"Colonnes disponibles : {list(gdf.columns)}"
        )

    gdf = gdf.copy()
    gdf["raster"] = np.where(gdf[label_field] == 0, 1, 2)

    train_gdf = gdf.sample(frac=train_fraction, random_state=seed)
    test_gdf = gdf.drop(train_gdf.index)

    train_out = Path(train_path)
    test_out = Path(test_path)
    train_out.parent.mkdir(parents=True, exist_ok=True)
    test_out.parent.mkdir(parents=True, exist_ok=True)

    train_gdf.to_file(train_out)
    test_gdf.to_file(test_out)
    return train_gdf, test_gdf


def rasterize_samples(
    reference_raster: str | Path,
    samples_path: str | Path,
    *,
    attribute: str = "raster",
) -> np.ndarray:
    """Rasterise une couche vectorielle d'échantillons sur la grille du raster."""
    from compass_core.data.gdal_compat import import_gdal, import_ogr

    gdal = import_gdal()
    ogr = import_ogr()
    reference = gdal.Open(str(reference_raster))
    if reference is None:
        raise FileNotFoundError(f"Raster introuvable : {reference_raster}")

    vector = ogr.Open(str(samples_path))
    if vector is None:
        raise FileNotFoundError(f"Couche vectorielle introuvable : {samples_path}")

    layer = vector.GetLayer()
    mem_driver = gdal.GetDriverByName("MEM")
    target = mem_driver.Create(
        "",
        reference.RasterXSize,
        reference.RasterYSize,
        1,
        gdal.GDT_UInt16,
    )
    target.SetGeoTransform(reference.GetGeoTransform())
    target.SetProjection(reference.GetProjectionRef())
    gdal.RasterizeLayer(target, [1], layer, options=[f"ATTRIBUTE={attribute}"])
    return target.GetRasterBand(1).ReadAsArray()
