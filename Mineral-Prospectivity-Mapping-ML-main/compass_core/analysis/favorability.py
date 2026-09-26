"""Interrogation des cartes de favorabilité et extraction de hotspots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box

from compass_core.analysis.coordinates import utm_to_wgs84
from compass_core.data.gdal_compat import import_gdal


@dataclass
class GeoGrid:
    """Grille géoréférencée (favorabilité ou autre raster)."""

    values: np.ndarray
    geo_transform: tuple[float, float, float, float, float, float]
    crs_epsg: int = 32733

    @property
    def rows(self) -> int:
        return self.values.shape[0]

    @property
    def cols(self) -> int:
        return self.values.shape[1]

    @property
    def pixel_size_x(self) -> float:
        return abs(self.geo_transform[1])

    @property
    def pixel_size_y(self) -> float:
        return abs(self.geo_transform[5])

    def extent_utm(self) -> tuple[float, float, float, float]:
        """(xmin, ymin, xmax, ymax) en CRS métrique de la grille."""
        t = self.geo_transform
        xmin = t[0]
        ymax = t[3]
        xmax = t[0] + self.cols * t[1]
        ymin = t[3] + self.rows * t[5]
        return (min(xmin, xmax), min(ymin, ymax), max(xmin, xmax), max(ymin, ymax))

    def extent_wgs84(self) -> tuple[float, float, float, float]:
        """(south, west, north, east) pour Folium ImageOverlay / rectangle."""
        xmin, ymin, xmax, ymax = self.extent_utm()
        corners = [
            utm_to_wgs84(xmin, ymin, epsg=self.crs_epsg),
            utm_to_wgs84(xmax, ymin, epsg=self.crs_epsg),
            utm_to_wgs84(xmax, ymax, epsg=self.crs_epsg),
            utm_to_wgs84(xmin, ymax, epsg=self.crs_epsg),
        ]
        lats = [c[0] for c in corners]
        lons = [c[1] for c in corners]
        return (min(lats), min(lons), max(lats), max(lons))

    def extent_polygon_wgs84(self) -> Polygon:
        """Polygone d'emprise WGS84 (lon, lat)."""
        south, west, north, east = self.extent_wgs84()
        return box(west, south, east, north)


@dataclass
class FavorabilityHit:
    """Résultat d'interrogation à un point GPS."""

    score: float
    row: int
    col: int
    utm_x: float
    utm_y: float
    latitude: float
    longitude: float
    in_bounds: bool
    predicted_commodity: str = "cu_co"


@dataclass
class HotspotZone:
    """Polygone de zone à forte favorabilité."""

    score_mean: float
    score_max: float
    area_km2: float
    polygon_wgs84: Polygon
    distance_m: float


def load_geogrid(path: str | Path) -> GeoGrid:
    """Charge une carte depuis GeoTIFF ou fichier .npy + métadonnées."""
    source = Path(path)
    if source.suffix == ".npy":
        return _load_npy_with_metadata(source)
    return _load_geotiff(source)


def _load_geotiff(path: Path) -> GeoGrid:
    gdal = import_gdal()
    dataset = gdal.Open(str(path))
    if dataset is None:
        raise FileNotFoundError(f"Raster introuvable : {path}")

    band = dataset.GetRasterBand(1)
    values = band.ReadAsArray().astype(np.float32)
    transform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()
    epsg = 32733
    if "32733" in projection:
        epsg = 32733
    return GeoGrid(values=values, geo_transform=transform, crs_epsg=epsg)


def _load_npy_with_metadata(npy_path: Path) -> GeoGrid:
    """Charge un .npy en utilisant metadata.json du jeu Kolwezi."""
    import json

    values = np.load(npy_path)
    meta_path = Path("data/rdc/kolwezi/metadata.json")
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Métadonnées géospatiales introuvables pour {npy_path}. "
            "Utilisez un GeoTIFF ou générez le dataset Kolwezi."
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    origin = meta["origin_utm"]
    extent = meta["extent_m"]
    rows, cols = values.shape
    pixel_x = extent["width"] / cols
    pixel_y = extent["height"] / rows
    transform = (origin["x"], pixel_x, 0.0, origin["y"], 0.0, -pixel_y)
    return GeoGrid(values=values.astype(np.float32), geo_transform=transform)


def utm_to_pixel(
    utm_x: float,
    utm_y: float,
    grid: GeoGrid,
) -> tuple[int, int, bool]:
    """Convertit UTM en indices pixel (row, col)."""
    transform = grid.geo_transform
    col = int((utm_x - transform[0]) / transform[1])
    row = int((utm_y - transform[3]) / transform[5])
    in_bounds = 0 <= row < grid.rows and 0 <= col < grid.cols
    return row, col, in_bounds


def pixel_to_utm(row: int, col: int, grid: GeoGrid) -> tuple[float, float]:
    """Centre pixel en coordonnées UTM."""
    transform = grid.geo_transform
    x = transform[0] + (col + 0.5) * transform[1]
    y = transform[3] + (row + 0.5) * transform[5]
    return x, y


def query_favorability(
    grid: GeoGrid,
    *,
    latitude: float,
    longitude: float,
    commodity: str = "cu_co",
) -> FavorabilityHit:
    """Interroge la carte de favorabilité à un point GPS."""
    from compass_core.analysis.coordinates import wgs84_to_utm

    utm_x, utm_y = wgs84_to_utm(latitude, longitude, epsg=grid.crs_epsg)
    row, col, in_bounds = utm_to_pixel(utm_x, utm_y, grid)

    if in_bounds:
        score = float(grid.values[row, col])
    else:
        score = 0.0

    return FavorabilityHit(
        score=score,
        row=row,
        col=col,
        utm_x=utm_x,
        utm_y=utm_y,
        latitude=latitude,
        longitude=longitude,
        in_bounds=in_bounds,
        predicted_commodity=commodity if score >= 0.5 else "incertain",
    )


def _pixel_polygon(row: int, col: int, grid: GeoGrid) -> Polygon:
    transform = grid.geo_transform
    x_min = transform[0] + col * transform[1]
    x_max = transform[0] + (col + 1) * transform[1]
    y_max = transform[3] + row * transform[5]
    y_min = transform[3] + (row + 1) * transform[5]
    coords = [
        utm_to_wgs84(x_min, y_min, epsg=grid.crs_epsg),
        utm_to_wgs84(x_max, y_min, epsg=grid.crs_epsg),
        utm_to_wgs84(x_max, y_max, epsg=grid.crs_epsg),
        utm_to_wgs84(x_min, y_max, epsg=grid.crs_epsg),
        utm_to_wgs84(x_min, y_min, epsg=grid.crs_epsg),
    ]
    return Polygon([(lon, lat) for lat, lon in coords])


def extract_hotspots(
    grid: GeoGrid,
    *,
    center_utm_x: float,
    center_utm_y: float,
    threshold: float = 0.85,
    max_distance_m: float = 5000.0,
    max_zones: int = 5,
) -> list[HotspotZone]:
    """
    Extrait les zones connectées à forte favorabilité proches du point ciblé.

    Algorithme : composantes connexes sur masque (score >= seuil).
    """
    from scipy import ndimage

    mask = grid.values >= threshold
    if not mask.any():
        return []

    labeled, num_features = ndimage.label(mask)
    hotspots: list[HotspotZone] = []

    for zone_id in range(1, num_features + 1):
        zone_mask = labeled == zone_id
        rows, cols = np.where(zone_mask)
        scores = grid.values[zone_mask]
        center_row = int(rows.mean())
        center_col = int(cols.mean())
        zone_utm_x, zone_utm_y = pixel_to_utm(center_row, center_col, grid)
        distance = float(
            np.hypot(zone_utm_x - center_utm_x, zone_utm_y - center_utm_y)
        )
        if distance > max_distance_m:
            continue

        min_row, max_row = int(rows.min()), int(rows.max())
        min_col, max_col = int(cols.min()), int(cols.max())
        corners = [
            pixel_to_utm(min_row, min_col, grid),
            pixel_to_utm(min_row, max_col, grid),
            pixel_to_utm(max_row, max_col, grid),
            pixel_to_utm(max_row, min_col, grid),
        ]
        lats_lons = [utm_to_wgs84(x, y, epsg=grid.crs_epsg) for x, y in corners]
        polygon = box(
            min(lon for lat, lon in lats_lons),
            min(lat for lat, lon in lats_lons),
            max(lon for lat, lon in lats_lons),
            max(lat for lat, lon in lats_lons),
        )
        pixel_area_m2 = grid.pixel_size_x * grid.pixel_size_y
        area_km2 = zone_mask.sum() * pixel_area_m2 / 1_000_000

        hotspots.append(
            HotspotZone(
                score_mean=float(scores.mean()),
                score_max=float(scores.max()),
                area_km2=float(area_km2),
                polygon_wgs84=polygon,
                distance_m=distance,
            )
        )

    hotspots.sort(key=lambda zone: (-zone.score_max, zone.distance_m))
    return hotspots[:max_zones]


def predict_commodity_label(score: float, primary: str = "cu_co") -> str:
    """Libellé minéral prédit à partir du score de favorabilité."""
    labels = {
        "cu_co": "Cuivre / Cobalt",
        "li": "Lithium",
        "au": "Or",
        "diamond": "Diamant",
        "coltan": "Coltan (3T)",
    }
    if score < 0.35:
        return "Faible potentiel minier"
    if score < 0.65:
        return f"Potentiel modéré ({labels.get(primary, primary)})"
    return labels.get(primary, primary)
