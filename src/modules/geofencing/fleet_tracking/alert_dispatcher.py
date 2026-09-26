"""Gestionnaire d'alertes de sécurité et conformité pour flotte minière."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from .geofence_engine import GeofenceEngine, ZoneCategory
from .telemetry_parser import EquipmentTelemetry

logger = logging.getLogger(__name__)


@dataclass
class SecurityAlert:
    alert_id: str
    severity: str  # "CRITICAL", "HIGH", "WARNING", "INFO"
    rule: str
    device_id: str
    timestamp: str
    description: str
    location: tuple[float, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class FleetAlertDispatcher:
    """
    Règles métier de sécurité minière :
    - Incursion dans un parc national ICCN (CRITICAL)
    - Déchargement suspect de minerai hors station de pesée autorisée (HIGH)
    - Excès de vitesse sur piste de roulage (WARNING)
    - Présence dans une zone de tir de mine actif (CRITICAL)
    """

    def __init__(self, engine: GeofenceEngine):
        self.engine = engine
        self.alerts_history: List[SecurityAlert] = []
        self._alert_counter = 0

    def process_telemetry(self, telemetry: EquipmentTelemetry) -> List[SecurityAlert]:
        events = self.engine.check_position(
            device_id=telemetry.device_id,
            lat=telemetry.latitude,
            lon=telemetry.longitude,
            speed_kmh=telemetry.speed_kmh,
        )

        new_alerts = []
        for ev in events:
            ev_type = ev["event"]
            category = ev.get("category")

            # Règle 1 : Incursion dans un parc protégé
            if ev_type == "GEOFENCE_ENTER" and category == ZoneCategory.PROTECTED_AREA.value:
                alert = self._create_alert(
                    severity="CRITICAL",
                    rule="RULE_PROTECTED_AREA_INCURSION",
                    device_id=telemetry.device_id,
                    description=f"Incursion illégale détectée dans l'aire protégée {ev['zone_name']}.",
                    location=(telemetry.latitude, telemetry.longitude),
                    metadata=ev,
                )
                new_alerts.append(alert)

            # Règle 2 : Incursion dans une zone de tir
            elif ev_type == "GEOFENCE_ENTER" and category == ZoneCategory.BLAST_ZONE.value:
                alert = self._create_alert(
                    severity="CRITICAL",
                    rule="RULE_ACTIVE_BLAST_INCURSION",
                    device_id=telemetry.device_id,
                    description=f"DANGER DE MORT : Véhicule entré dans la zone de tir de mine {ev['zone_name']}.",
                    location=(telemetry.latitude, telemetry.longitude),
                    metadata=ev,
                )
                new_alerts.append(alert)

            # Règle 3 : Excès de vitesse
            elif ev_type == "SPEED_VIOLATION":
                alert = self._create_alert(
                    severity="WARNING",
                    rule="RULE_HAUL_ROAD_SPEEDING",
                    device_id=telemetry.device_id,
                    description=f"Vitesse excessive ({ev['speed_kmh']} km/h > {ev['limit_kmh']} km/h) dans {ev['zone_name']}.",
                    location=(telemetry.latitude, telemetry.longitude),
                    metadata=ev,
                )
                new_alerts.append(alert)

        # Règle 4 : Déchargement de benne suspect hors station autorisée
        if telemetry.bed_raised and telemetry.payload_kg > 500.0:
            # Vérifier si l'engin est dans une station de pesée / déchargement agréée
            in_weigh_station = False
            for zid, z in self.engine.zones.items():
                if z.category == ZoneCategory.WEIGHING_STATION:
                    if self.engine.is_point_in_zone(telemetry.latitude, telemetry.longitude, zid):
                        in_weigh_station = True
                        break

            if not in_weigh_station:
                alert = self._create_alert(
                    severity="HIGH",
                    rule="RULE_ILLEGAL_ORE_DUMPING",
                    device_id=telemetry.device_id,
                    description=f"Benne levée ({telemetry.payload_kg} kg) hors de toute station de déchargement officielle.",
                    location=(telemetry.latitude, telemetry.longitude),
                    metadata={"payload_kg": telemetry.payload_kg},
                )
                new_alerts.append(alert)

        return new_alerts

    def _create_alert(
        self,
        severity: str,
        rule: str,
        device_id: str,
        description: str,
        location: tuple[float, float],
        metadata: Dict[str, Any],
    ) -> SecurityAlert:
        self._alert_counter += 1
        alert = SecurityAlert(
            alert_id=f"ALT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._alert_counter:04d}",
            severity=severity,
            rule=rule,
            device_id=device_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            description=description,
            location=location,
            metadata=metadata,
        )
        self.alerts_history.append(alert)
        logger.warning(f"[{severity}] {alert.alert_id} ({rule}) pour {device_id}: {description}")
        return alert
