"""Pilier 3 : Geofencing & Localisation."""

from .fleet_tracking import (
    EquipmentTelemetry,
    FleetAlertDispatcher,
    GeofenceEngine,
    GeofenceType,
    GeofenceZone,
    SecurityAlert,
    TelemetryParser,
    ZoneCategory,
    haversine_distance_m,
    point_in_polygon,
)
from .spatial_indexing import (
    CollisionRisk,
    HexagonalSpatialIndexer,
    MiningCollisionPreventionSystem,
    VehiclePosition,
)

__all__ = [
    "GeofenceEngine",
    "GeofenceZone",
    "GeofenceType",
    "ZoneCategory",
    "TelemetryParser",
    "EquipmentTelemetry",
    "FleetAlertDispatcher",
    "SecurityAlert",
    "haversine_distance_m",
    "point_in_polygon",
    "HexagonalSpatialIndexer",
    "MiningCollisionPreventionSystem",
    "VehiclePosition",
    "CollisionRisk",
]
