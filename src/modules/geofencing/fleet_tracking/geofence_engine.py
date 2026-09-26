"""Moteur de géo-clôtures (Geofencing) inspiré de l'architecture Traccar."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class GeofenceType(str, Enum):
    POLYGON = "POLYGON"
    CIRCLE = "CIRCLE"
    CORRIDOR = "CORRIDOR"


class ZoneCategory(str, Enum):
    ZEA = "ZEA"                       # Zone d'Exploitation Artisanale
    CAMI_PERMIT = "CAMI_PERMIT"       # Permis d'Exploitation ou de Recherches
    PROTECTED_AREA = "PROTECTED_AREA" # Aire protégée ICCN (interdiction absolue)
    BLAST_ZONE = "BLAST_ZONE"         # Périmètre de tir d'explosifs
    HAUL_ROAD = "HAUL_ROAD"           # Piste de roulage des camions bennes
    WEIGHING_STATION = "WEIGH_STATION"# Carreau de mine / Station de pesée


@dataclass
class GeofenceZone:
    id: str
    name: str
    category: ZoneCategory
    zone_type: GeofenceType
    # Pour POLYGON : liste de (lat, lon)
    coordinates: List[Tuple[float, float]] = field(default_factory=list)
    # Pour CIRCLE : (lat, lon) du centre et rayon en mètres
    center: Optional[Tuple[float, float]] = None
    radius_m: float = 0.0
    speed_limit_kmh: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcule la distance géodésique entre deux points en mètres (WGS 84)."""
    R = 6371000.0  # Rayon terrestre moyen
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def point_in_polygon(lat: float, lon: float, polygon: List[Tuple[float, float]]) -> bool:
    """Algorithme Ray-Casting standard pour tester l'inclusion d'un point dans un polygone."""
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    p1_lat, p1_lon = polygon[0]
    for i in range(1, n + 1):
        p2_lat, p2_lon = polygon[i % n]
        if min(p1_lon, p2_lon) < lon <= max(p1_lon, p2_lon):
            if lat <= max(p1_lat, p2_lat):
                if p1_lon != p2_lon:
                    xinters = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                if p1_lat == p2_lat or lat <= xinters:
                    inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon

    return inside


class GeofenceEngine:
    """
    Moteur de gestion des clôtures virtuelles minières.
    Évalue instantanément la conformité spatiale de tout équipement lourd ou transporteur.
    """

    def __init__(self):
        self.zones: Dict[str, GeofenceZone] = {}
        self._device_states: Dict[str, Dict[str, bool]] = {}  # device_id -> {zone_id: inside}

    def register_zone(self, zone: GeofenceZone):
        """Enregistre un nouveau périmètre de géo-clôture."""
        self.zones[zone.id] = zone

    def is_point_in_zone(self, lat: float, lon: float, zone_id: str) -> bool:
        """Vérifie si une coordonnée GPS est située dans une zone donnée."""
        zone = self.zones.get(zone_id)
        if not zone:
            return False

        if zone.zone_type == GeofenceType.CIRCLE:
            if not zone.center:
                return False
            dist = haversine_distance_m(lat, lon, zone.center[0], zone.center[1])
            return dist <= zone.radius_m

        if zone.zone_type == GeofenceType.POLYGON:
            return point_in_polygon(lat, lon, zone.coordinates)

        return False

    def check_position(
        self,
        device_id: str,
        lat: float,
        lon: float,
        speed_kmh: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Analyse une position télémétrique et génère les transitions d'événements.
        Retourne la liste des alertes et franchissements constatés.
        """
        events = []
        if device_id not in self._device_states:
            self._device_states[device_id] = {}

        for zone_id, zone in self.zones.items():
            is_inside = self.is_point_in_zone(lat, lon, zone_id)
            was_inside = self._device_states[device_id].get(zone_id, False)

            if is_inside and not was_inside:
                events.append({
                    "event": "GEOFENCE_ENTER",
                    "device_id": device_id,
                    "zone_id": zone_id,
                    "zone_name": zone.name,
                    "category": zone.category.value,
                    "lat": lat,
                    "lon": lon,
                })
            elif not is_inside and was_inside:
                events.append({
                    "event": "GEOFENCE_EXIT",
                    "device_id": device_id,
                    "zone_id": zone_id,
                    "zone_name": zone.name,
                    "category": zone.category.value,
                    "lat": lat,
                    "lon": lon,
                })

            if is_inside and zone.speed_limit_kmh and speed_kmh > zone.speed_limit_kmh:
                events.append({
                    "event": "SPEED_VIOLATION",
                    "device_id": device_id,
                    "zone_id": zone_id,
                    "zone_name": zone.name,
                    "speed_kmh": speed_kmh,
                    "limit_kmh": zone.speed_limit_kmh,
                })

            self._device_states[device_id][zone_id] = is_inside

        return events
