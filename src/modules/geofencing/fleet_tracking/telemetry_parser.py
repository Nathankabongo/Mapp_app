"""Parseur et normalisateur de télémétrie pour engins miniers lourds."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class EquipmentTelemetry:
    device_id: str
    timestamp: str
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    speed_kmh: float = 0.0
    course_deg: float = 0.0
    ignition: bool = True
    payload_kg: float = 0.0        # Charge utile dans la benne
    bed_raised: bool = False       # Benne levée (déchargement de minerai)
    fuel_level_pct: float = 100.0
    raw_protocol: str = "traccar_osm"
    attributes: Dict[str, Any] = field(default_factory=dict)


class TelemetryParser:
    """
    Normalise les flux télémétriques provenant des boîtiers GPS industriels
    (Traccar Client, Teltonika FMB, CalAmp, ou messages MQTT/HTTP).
    """

    @staticmethod
    def parse_json_packet(data: Dict[str, Any]) -> EquipmentTelemetry:
        """Parse un paquet JSON normalisé (ex: Traccar HTTP Webhook)."""
        device_id = str(data.get("deviceId") or data.get("device_id") or "UNKNOWN")
        lat = float(data.get("lat") or data.get("latitude", 0.0))
        lon = float(data.get("lon") or data.get("longitude", 0.0))

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            raise ValueError(f"Coordonnées GPS hors limites: lat={lat}, lon={lon}")

        speed = float(data.get("speed", data.get("speed_kmh", 0.0)))
        course = float(data.get("course", data.get("course_deg", 0.0)))
        alt = float(data.get("altitude", data.get("altitude_m", 0.0)))

        ts = data.get("timestamp") or data.get("fixTime")
        if not ts:
            ts = datetime.now(timezone.utc).isoformat()

        attrs = data.get("attributes", {})
        payload = float(attrs.get("payload_kg", data.get("payload_kg", 0.0)))
        bed = bool(attrs.get("bed_raised", data.get("bed_raised", False)))
        ignition = bool(attrs.get("ignition", True))

        return EquipmentTelemetry(
            device_id=device_id,
            timestamp=str(ts),
            latitude=lat,
            longitude=lon,
            altitude_m=alt,
            speed_kmh=speed,
            course_deg=course,
            ignition=ignition,
            payload_kg=payload,
            bed_raised=bed,
            attributes=attrs,
        )

    @staticmethod
    def parse_raw_nmea_sentence(sentence: str, device_id: str) -> Optional[EquipmentTelemetry]:
        """Parse une trame brute NMEA $GPRMC basique."""
        parts = sentence.strip().split(",")
        if len(parts) < 10 or not parts[0].endswith("RMC"):
            return None

        # Format: $GPRMC,hhmmss.ss,A,llll.ll,a,yyyyy.yy,a,x.x,x.x,ddmmyy,,,A*hh
        status = parts[2]
        if status != "A":  # 'A' = Valid fix, 'V' = Warning
            return None

        raw_lat = parts[3]
        lat_dir = parts[4]
        raw_lon = parts[5]
        lon_dir = parts[6]

        # Convertir ddmm.mmmm en degrés décimaux
        lat_deg = float(raw_lat[:2]) + float(raw_lat[2:]) / 60.0
        if lat_dir == "S":
            lat_deg = -lat_deg

        lon_deg = float(raw_lon[:3]) + float(raw_lon[3:]) / 60.0
        if lon_dir == "W":
            lon_deg = -lon_deg

        speed_knots = float(parts[7]) if parts[7] else 0.0
        speed_kmh = speed_knots * 1.852

        course = float(parts[8]) if parts[8] else 0.0

        return EquipmentTelemetry(
            device_id=device_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=round(lat_deg, 6),
            longitude=round(lon_deg, 6),
            speed_kmh=round(speed_kmh, 2),
            course_deg=course,
            raw_protocol="nmea_gprmc",
        )
