"""Stratégie CRS nationale — jamais UTM 33S seul pour toute la RDC."""

from __future__ import annotations

from dataclasses import dataclass

from pyproj import Transformer

DISPLAY_CRS = "EPSG:4326"


@dataclass(frozen=True)
class MetricCRS:
    epsg: int
    label: str


def utm_epsg_for_longitude(longitude: float, *, southern: bool = True) -> MetricCRS:
    """Choisit la zone UTM adaptée à la longitude (RDC ~12°E–31°E)."""
    zone = int((longitude + 180) // 6) + 1
    zone = max(32, min(36, zone))  # bornes utiles RDC
    epsg = (32700 if southern else 32600) + zone
    return MetricCRS(epsg=epsg, label=f"UTM {zone}{'S' if southern else 'N'} (EPSG:{epsg})")


def resolve_metric_crs(latitude: float, longitude: float) -> MetricCRS:
    southern = latitude < 0
    return utm_epsg_for_longitude(longitude, southern=southern)


def to_metric(longitude: float, latitude: float, epsg: int) -> tuple[float, float]:
    t = Transformer.from_crs(DISPLAY_CRS, f"EPSG:{epsg}", always_xy=True)
    x, y = t.transform(longitude, latitude)
    return float(x), float(y)


def from_metric(x: float, y: float, epsg: int) -> tuple[float, float]:
    t = Transformer.from_crs(f"EPSG:{epsg}", DISPLAY_CRS, always_xy=True)
    lon, lat = t.transform(x, y)
    return float(lat), float(lon)


def crs_strategy_doc() -> str:
    return (
        "Affichage/stockage : EPSG:4326. "
        "Distances générales : géodésique (haversine). "
        "Analyses métriques : UTM auto selon longitude (32S–36S). "
        "EPSG:32733 réservé à la zone pilote Kolwezi / Lualaba lorsque le raster l'impose."
    )
