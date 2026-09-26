"""Chargement et manipulation de rasters GeoTIFF (GDAL)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from compass_core.data.gdal_compat import import_gdal


@dataclass
class RasterStack:
    """Stack multi-bandes avec métadonnées géospatiales."""

    cube: np.ndarray
    flat: np.ndarray
    source_path: str
    nbands: int
    rows: int
    cols: int

    @property
    def shape_2d(self) -> tuple[int, int]:
        return self.rows, self.cols


def load_raster(path: str | Path, *, reshape: bool = True) -> RasterStack:
    """
    Ouvre un GeoTIFF multi-bandes et retourne le cube + tableau aplati.

    Migré depuis ``Data_preprocessing.rs_preprocessing``.
    """
    gdal = import_gdal()
    source = str(path)
    dataset = gdal.Open(source)
    if dataset is None:
        raise FileNotFoundError(f"Impossible d'ouvrir le raster : {source}")

    nbands = dataset.RasterCount
    rows = dataset.RasterYSize
    cols = dataset.RasterXSize
    bands: list[np.ndarray] = []

    for index in range(1, nbands + 1):
        bands.append(dataset.GetRasterBand(index).ReadAsArray())

    cube = np.dstack(bands)
    flat = np.empty((0, nbands), dtype=cube.dtype)

    if reshape:
        flat = cube.reshape(rows * cols, nbands)
        flat = np.nan_to_num(flat)

    return RasterStack(
        cube=cube,
        flat=flat,
        source_path=source,
        nbands=nbands,
        rows=rows,
        cols=cols,
    )


def write_raster(
    reference_raster: str | Path,
    prediction: np.ndarray,
    output_path: str | Path,
    *,
    dtype: int | None = None,
) -> Path:
    """
    Écrit une carte de prédiction GeoTIFF géoréférencée.

    Migré depuis ``Data_preprocessing.write_raster``.
    """
    gdal = import_gdal()
    if dtype is None:
        dtype = gdal.GDT_Float32
    reference = gdal.Open(str(reference_raster))
    if reference is None:
        raise FileNotFoundError(f"Raster de référence introuvable : {reference_raster}")

    rows, cols = prediction.shape
    driver = gdal.GetDriverByName("GTiff")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    out_dataset = driver.Create(str(destination), cols, rows, 1, dtype)
    out_dataset.SetGeoTransform(reference.GetGeoTransform())
    out_dataset.SetProjection(reference.GetProjection())
    out_dataset.GetRasterBand(1).WriteArray(prediction.astype(np.float32))
    out_dataset.FlushCache()
    return destination
