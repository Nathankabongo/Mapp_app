"""Buffers geometriques."""

from __future__ import annotations

from shapely.geometry import Point
from shapely.ops import transform
from pyproj import Transformer


def buffer_wgs84_km(latitude: float, longitude: float, radius_km: float):
    """Polygone tampon approximatif en WGS84 (projection aeqd locale)."""
    aeqd = (
        f"+proj=aeqd +lat_0={latitude} +lon_0={longitude} +x_0=0 +y_0=0 "
        "+datum=WGS84 +units=m +no_defs"
    )
    to_m = Transformer.from_crs("EPSG:4326", aeqd, always_xy=True).transform
    to_wgs = Transformer.from_crs(aeqd, "EPSG:4326", always_xy=True).transform
    point_m = transform(to_m, Point(longitude, latitude))
    return transform(to_wgs, point_m.buffer(radius_km * 1000))
