"""Génération d'un jeu de données SIG d'exemple pour la zone pilote Kolwezi."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import Point

from compass_core.data.gdal_compat import import_gdal, import_osr
from compass_core.data.vector import split_samples
from compass_core.pipeline.synthetic import generate_synthetic_dataset

KOLWEZI_LAT = -10.716
KOLWEZI_LON = 25.465
KOLWEZI_CRS = "EPSG:32733"
DEFAULT_PIXEL_SIZE = 250.0


def _kolwezi_origin(rows: int, cols: int, pixel_size: float = DEFAULT_PIXEL_SIZE) -> tuple[float, float]:
    """Calcule l'origine UTM (coin supérieur gauche) centrée sur Kolwezi."""
    from compass_core.analysis.coordinates import wgs84_to_utm

    center_x, center_y = wgs84_to_utm(KOLWEZI_LAT, KOLWEZI_LON)
    origin_x = center_x - (cols * pixel_size) / 2
    origin_y = center_y + (rows * pixel_size) / 2
    return origin_x, origin_y


KOLWEZI_ORIGIN_X, KOLWEZI_ORIGIN_Y = _kolwezi_origin(64, 64)

BAND_NAMES = (
    "mag_total",
    "mag_derivative",
    "radiometry_k",
    "radiometry_th",
    "radiometry_u",
    "spectro_clay",
    "geology_code",
    "elevation",
)

KOLWEZI_DATASET_FILES: dict[str, str] = {
    "raster": "stack_multiphysics.tif",
    "samples": "deposits_cu_co.gpkg",
    "training": "training.gpkg",
    "testing": "testing.gpkg",
    "metadata": "metadata.json",
    "bands": "stack_multiphysics.bands.json",
}


@dataclass
class SampleDatasetReport:
    """Rapport de génération du jeu de données d'exemple."""

    output_dir: Path
    raster_path: Path
    deposits_path: Path
    training_path: Path
    testing_path: Path
    metadata_path: Path
    rows: int
    cols: int
    nbands: int
    n_deposits: int
    n_positive: int
    n_negative: int
    crs: str = KOLWEZI_CRS


def build_geo_transform(
    origin_x: float,
    origin_y: float,
    pixel_size: float,
) -> tuple[float, float, float, float, float, float]:
    """Construit la géotransformation GDAL (coin supérieur gauche)."""
    return (origin_x, pixel_size, 0.0, origin_y, 0.0, -pixel_size)


def pixel_center_to_utm(
    row: int,
    col: int,
    origin_x: float,
    origin_y: float,
    pixel_size: float,
) -> tuple[float, float]:
    """Convertit un indice pixel en coordonnées UTM (centre du pixel)."""
    x = origin_x + (col + 0.5) * pixel_size
    y = origin_y - (row + 0.5) * pixel_size
    return x, y


def utm_to_pixel(
    x: float,
    y: float,
    origin_x: float,
    origin_y: float,
    pixel_size: float,
) -> tuple[int, int]:
    """Convertit des coordonnées UTM en indices pixel."""
    col = int((x - origin_x) / pixel_size)
    row = int((origin_y - y) / pixel_size)
    return row, col


def write_geotiff(
    path: str | Path,
    cube: np.ndarray,
    geo_transform: tuple[float, float, float, float, float, float],
    *,
    crs_epsg: int = 32733,
) -> Path:
    """Écrit un raster multi-bandes géoréférencé."""
    gdal = import_gdal()
    osr = import_osr()
    rows, cols, nbands = cube.shape
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(str(destination), cols, rows, nbands, gdal.GDT_Float32)
    dataset.SetGeoTransform(geo_transform)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(crs_epsg)
    dataset.SetProjection(srs.ExportToWkt())

    for index in range(nbands):
        dataset.GetRasterBand(index + 1).WriteArray(cube[:, :, index].astype(np.float32))

    dataset.FlushCache()
    dataset = None
    return destination


def _build_deposits_gdf(
    cube: np.ndarray,
    *,
    n_deposits: int,
    origin_x: float,
    origin_y: float,
    pixel_size: float,
    seed: int,
) -> gpd.GeoDataFrame:
    """Crée des points d'affleurement Cu-Co étiquetés à partir du raster synthétique."""
    rows, cols, _ = cube.shape
    rng = np.random.default_rng(seed)
    flat = cube.reshape(rows * cols, cube.shape[2])

    indices = rng.choice(rows * cols, size=n_deposits, replace=False)
    records: list[dict] = []

    for idx in indices:
        row, col = divmod(int(idx), cols)
        features = flat[idx]
        signal = features[0] + 0.5 * features[1]
        value = int(signal + rng.normal(scale=0.3) > signal.mean())
        x, y = pixel_center_to_utm(row, col, origin_x, origin_y, pixel_size)
        records.append(
            {
                "geometry": Point(x, y),
                "Value": value,
                "commodity": "cu_co",
                "source": "synthetic_demo",
                "pixel_row": row,
                "pixel_col": col,
            }
        )

    gdf = gpd.GeoDataFrame(records, crs=KOLWEZI_CRS)
    return gdf


def dataset_paths(output_dir: str | Path) -> dict[str, Path]:
    """Retourne les chemins attendus du jeu Kolwezi."""
    base = Path(output_dir)
    return {key: base / filename for key, filename in KOLWEZI_DATASET_FILES.items()}


def check_dataset_inventory(output_dir: str | Path = "data/rdc/kolwezi") -> list[tuple[str, Path, bool]]:
    """Vérifie la présence de chaque fichier du jeu Kolwezi."""
    paths = dataset_paths(output_dir)
    labels = {
        "raster": "Raster multiphysique",
        "samples": "Gisements Cu-Co",
        "training": "Échantillons entraînement",
        "testing": "Échantillons test",
        "metadata": "Métadonnées",
        "bands": "Descripteur bandes",
    }
    return [(labels[key], path, path.exists()) for key, path in paths.items()]


def generate_kolwezi_sample_dataset(
    output_dir: str | Path = "data/rdc/kolwezi",
    *,
    rows: int = 64,
    cols: int = 64,
    nbands: int = 8,
    n_deposits: int = 60,
    seed: int = 42,
    pixel_size: float = DEFAULT_PIXEL_SIZE,
    split_train: bool = True,
    train_fraction: float = 0.8,
) -> SampleDatasetReport:
    """
    Génère un jeu SIG géoréférencé Kolwezi (GeoTIFF + GeoPackage).

    Simule un empilement multiphysique (magnétisme, radiométrie, spectro, géologie)
    et des points d'affleurement Cu-Co pour tester le pipeline SIG complet.
    """
    origin_x, origin_y = _kolwezi_origin(rows, cols, pixel_size)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = dataset_paths(output)

    dataset = generate_synthetic_dataset(
        rows=rows,
        cols=cols,
        nbands=nbands,
        n_train=80,
        n_test=30,
        seed=seed,
    )
    geo_transform = build_geo_transform(origin_x, origin_y, pixel_size)
    write_geotiff(paths["raster"], dataset.cube, geo_transform)

    deposits = _build_deposits_gdf(
        dataset.cube,
        n_deposits=n_deposits,
        origin_x=origin_x,
        origin_y=origin_y,
        pixel_size=pixel_size,
        seed=seed + 1,
    )
    deposits.to_file(paths["samples"], driver="GPKG")

    training_path = paths["training"]
    testing_path = paths["testing"]
    if split_train:
        split_samples(
            paths["samples"],
            training_path,
            testing_path,
            train_fraction=train_fraction,
            seed=seed,
        )

    n_positive = int((deposits["Value"] == 1).sum())
    n_negative = int((deposits["Value"] == 0).sum())

    bands_meta = {
        "source": "CriticalMineralsCompass sample generator",
        "crs": KOLWEZI_CRS,
        "pixel_size_m": pixel_size,
        "bands": [
            {"index": i + 1, "name": name, "description": _band_description(name)}
            for i, name in enumerate(BAND_NAMES[:nbands])
        ],
    }
    paths["bands"].write_text(json.dumps(bands_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    metadata = {
        "title": "Jeu d'exemple Kolwezi Cu-Co",
        "description": (
            "Données SIG synthétiques géoréférencées simulant la ceinture cuprifère "
            "de Kolwezi (Lualaba, RDC). Permet de tester le pipeline complet sans "
            "données CAMI/Xcalibur réelles."
        ),
        "region": "kolwezi",
        "province": "Lualaba",
        "commodity": "cu_co",
        "crs": KOLWEZI_CRS,
        "origin_utm": {"x": origin_x, "y": origin_y},
        "center_wgs84": {"lat": KOLWEZI_LAT, "lon": KOLWEZI_LON},
        "extent_m": {"width": cols * pixel_size, "height": rows * pixel_size},
        "shape": {"rows": rows, "cols": cols, "bands": nbands},
        "deposits": {
            "total": n_deposits,
            "positive": n_positive,
            "negative": n_negative,
        },
        "files": {key: str(path.name) for key, path in paths.items()},
        "seed": seed,
    }
    paths["metadata"].write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    return SampleDatasetReport(
        output_dir=output,
        raster_path=paths["raster"],
        deposits_path=paths["samples"],
        training_path=training_path,
        testing_path=testing_path,
        metadata_path=paths["metadata"],
        rows=rows,
        cols=cols,
        nbands=nbands,
        n_deposits=n_deposits,
        n_positive=n_positive,
        n_negative=n_negative,
    )


def _band_description(name: str) -> str:
    descriptions = {
        "mag_total": "Anomalie magnétique totale (nT)",
        "mag_derivative": "Dérivée verticale du champ magnétique",
        "radiometry_k": "Potassium radiométrique (%)",
        "radiometry_th": "Thorium radiométrique (ppm)",
        "radiometry_u": "Uranium radiométrique (ppm)",
        "spectro_clay": "Indice argiles/altération (spectroscopie)",
        "geology_code": "Code lithologique (rasterisé)",
        "elevation": "Modèle numérique de terrain (m)",
    }
    return descriptions.get(name, name)
