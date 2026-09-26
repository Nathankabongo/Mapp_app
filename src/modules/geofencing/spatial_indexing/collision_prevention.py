"""Système de prévention des collisions d'engins miniers lourds basé sur H3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .h3_indexer import HexagonalSpatialIndexer


@dataclass
class VehiclePosition:
    vehicle_id: str
    vehicle_type: str  # DUMPER, EXCAVATOR, LIGHT_VEHICLE, DRILL_RIG
    lat: float
    lon: float
    speed_kmh: float
    h3_cell: str


@dataclass
class CollisionRisk:
    vehicle_a: str
    vehicle_b: str
    risk_level: str  # CRITICAL (même cellule), WARNING (cellules adjacentes à vitesse élevée)
    h3_distance: int
    cell_a: str
    cell_b: str
    message: str


class MiningCollisionPreventionSystem:
    """
    Système d'alerte anti-collision haute performance basé sur le carroyage H3.
    Évite les calculs trigonométriques coûteux en exploitant les voisinages d'hexagones en mémoire.
    """

    def __init__(self, indexer: Optional[HexagonalSpatialIndexer] = None, resolution: int = 10):
        # Résolution 10 = cellule d'environ 65 mètres
        self.indexer = indexer or HexagonalSpatialIndexer(default_resolution=resolution)
        self.active_vehicles: Dict[str, VehiclePosition] = {}

    def update_vehicle_position(
        self,
        vehicle_id: str,
        vehicle_type: str,
        lat: float,
        lon: float,
        speed_kmh: float,
    ) -> VehiclePosition:
        cell = self.indexer.lat_lon_to_h3(lat, lon)
        pos = VehiclePosition(
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            lat=lat,
            lon=lon,
            speed_kmh=speed_kmh,
            h3_cell=cell,
        )
        self.active_vehicles[vehicle_id] = pos
        return pos

    def detect_proximity_conflicts(self, target_vehicle_id: str) -> List[CollisionRisk]:
        """
        Détecte les conflits de proximité immédiats pour un engin donné.
        """
        target = self.active_vehicles.get(target_vehicle_id)
        if not target:
            return []

        conflicts = []
        # Hexagones de danger immédiat (k=1 : même cellule ou 6 voisines directes)
        danger_zone = self.indexer.get_k_ring(target.h3_cell, k=1)

        for other_id, other in self.active_vehicles.items():
            if other_id == target_vehicle_id:
                continue

            # 1. Même cellule H3 : Risque critique
            if other.h3_cell == target.h3_cell:
                conflicts.append(CollisionRisk(
                    vehicle_a=target.vehicle_id,
                    vehicle_b=other.vehicle_id,
                    risk_level="CRITICAL",
                    h3_distance=0,
                    cell_a=target.h3_cell,
                    cell_b=other.h3_cell,
                    message=f"ALERTE COLLISION : {target.vehicle_id} et {other.vehicle_id} occupent la même cellule minière ({target.h3_cell}).",
                ))
            # 2. Cellule adjacente : Risque élevé si l'un d'eux est en mouvement
            elif other.h3_cell in danger_zone:
                if target.speed_kmh > 15.0 or other.speed_kmh > 15.0:
                    conflicts.append(CollisionRisk(
                        vehicle_a=target.vehicle_id,
                        vehicle_b=other.vehicle_id,
                        risk_level="WARNING",
                        h3_distance=1,
                        cell_a=target.h3_cell,
                        cell_b=other.h3_cell,
                        message=f"ATTENTION PROXIMITÉ : {other.vehicle_id} ({other.speed_kmh} km/h) est dans l'hexagone adjacent de {target.vehicle_id}.",
                    ))

        return conflicts
