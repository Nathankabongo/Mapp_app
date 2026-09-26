"""Conversions de coordonnées WGS84 ↔ UTM (RDC)."""

from __future__ import annotations

from dataclasses import dataclass

from pyproj import Transformer

DEFAULT_UTM_EPSG = 32733  # UTM zone 33S — Katanga / Lualaba


@dataclass(frozen=True)
class GeoPoint:
    """Point géographique avec coordonnées WGS84 et UTM."""

    latitude: float
    longitude: float
    utm_x: float
    utm_y: float
    epsg: int = DEFAULT_UTM_EPSG

    @property
    def wgs84(self) -> tuple[float, float]:
        return self.latitude, self.longitude

    @property
    def utm(self) -> tuple[float, float]:
        return self.utm_x, self.utm_y


def wgs84_to_utm(
    latitude: float,
    longitude: float,
    *,
    epsg: int = DEFAULT_UTM_EPSG,
) -> tuple[float, float]:
    """Convertit lat/lon WGS84 en coordonnées UTM."""
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    x, y = transformer.transform(longitude, latitude)
    return float(x), float(y)


def utm_to_wgs84(
    utm_x: float,
    utm_y: float,
    *,
    epsg: int = DEFAULT_UTM_EPSG,
) -> tuple[float, float]:
    """Convertit UTM en lat/lon WGS84."""
    transformer = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(utm_x, utm_y)
    return float(lat), float(lon)


def make_geo_point(
    latitude: float,
    longitude: float,
    *,
    epsg: int = DEFAULT_UTM_EPSG,
) -> GeoPoint:
    """Crée un GeoPoint à partir de coordonnées WGS84."""
    utm_x, utm_y = wgs84_to_utm(latitude, longitude, epsg=epsg)
    return GeoPoint(
        latitude=latitude,
        longitude=longitude,
        utm_x=utm_x,
        utm_y=utm_y,
        epsg=epsg,
    )
