import sys
import unittest
from pathlib import Path

# Ajouter d:\Mapping au sys.path
workspace_root = Path("d:/Mapping")
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from src.modules.geofencing.fleet_tracking import (
    FleetAlertDispatcher,
    GeofenceEngine,
    GeofenceType,
    GeofenceZone,
    TelemetryParser,
    ZoneCategory,
    haversine_distance_m,
    point_in_polygon,
)
from src.modules.geofencing.spatial_indexing import (
    HexagonalSpatialIndexer,
    MiningCollisionPreventionSystem,
)


class TestGeofencingPillar(unittest.TestCase):
    def test_haversine_and_polygon_inclusion(self):
        # Distance entre Kolwezi (-10.71, 25.47) et Likasi (-10.98, 26.73) ~140 km
        dist = haversine_distance_m(-10.71, 25.47, -10.98, 26.73)
        self.assertTrue(130000 < dist < 150000)

        # Polygone carré
        square = [(-10.0, 25.0), (-10.0, 26.0), (-11.0, 26.0), (-11.0, 25.0)]
        self.assertTrue(point_in_polygon(-10.5, 25.5, square))
        self.assertFalse(point_in_polygon(-12.0, 25.5, square))

    def test_geofence_engine_and_alerts(self):
        engine = GeofenceEngine()
        # Enregistrer une zone protégée (Parc)
        engine.register_zone(GeofenceZone(
            id="ZONE-PARC-01",
            name="Reserve Naturelle",
            category=ZoneCategory.PROTECTED_AREA,
            zone_type=GeofenceType.CIRCLE,
            center=(-10.50, 25.50),
            radius_m=2000.0,
            speed_limit_kmh=30.0,
        ))

        dispatcher = FleetAlertDispatcher(engine)

        # Position en dehors du parc
        tel1 = TelemetryParser.parse_json_packet({
            "deviceId": "TRUCK-01",
            "lat": -10.60,
            "lon": 25.50,
            "speed": 40.0,
        })
        alerts1 = dispatcher.process_telemetry(tel1)
        self.assertEqual(len(alerts1), 0)

        # Incursion dans le parc (lat=-10.501, lon=25.501)
        tel2 = TelemetryParser.parse_json_packet({
            "deviceId": "TRUCK-01",
            "lat": -10.501,
            "lon": 25.501,
            "speed": 45.0,  # Vitesse excessive aussi
        })
        alerts2 = dispatcher.process_telemetry(tel2)
        self.assertGreater(len(alerts2), 0)
        rules = [a.rule for a in alerts2]
        self.assertIn("RULE_PROTECTED_AREA_INCURSION", rules)

    def test_illegal_ore_dumping_alert(self):
        engine = GeofenceEngine()
        engine.register_zone(GeofenceZone(
            id="STATION-PESEE-01",
            name="Station de Pesée Officielle",
            category=ZoneCategory.WEIGHING_STATION,
            zone_type=GeofenceType.CIRCLE,
            center=(-10.70, 25.40),
            radius_m=300.0,
        ))
        dispatcher = FleetAlertDispatcher(engine)

        # Benne levée avec 15 tonnes de minerai en pleine brousse (hors station)
        tel_fraud = TelemetryParser.parse_json_packet({
            "deviceId": "TRUCK-DUMP-09",
            "lat": -10.85,
            "lon": 25.60,
            "speed": 0.0,
            "payload_kg": 15000.0,
            "bed_raised": True,
        })
        alerts = dispatcher.process_telemetry(tel_fraud)
        rules = [a.rule for a in alerts]
        self.assertIn("RULE_ILLEGAL_ORE_DUMPING", rules)

    def test_h3_hexagonal_indexing(self):
        indexer = HexagonalSpatialIndexer(default_resolution=9)
        lat, lon = -10.71234, 25.48567
        h3_cell = indexer.lat_lon_to_h3(lat, lon)
        self.assertTrue(len(h3_cell) > 0)

        c_lat, c_lon = indexer.h3_to_lat_lon(h3_cell)
        self.assertAlmostEqual(lat, c_lat, places=2)
        self.assertAlmostEqual(lon, c_lon, places=2)

        # Test k-ring
        ring = indexer.get_k_ring(h3_cell, k=1)
        # Un anneau k=1 contient 7 cellules (le centre + 6 voisines)
        self.assertEqual(len(ring), 7)
        self.assertIn(h3_cell, ring)

    def test_mining_collision_prevention(self):
        system = MiningCollisionPreventionSystem(resolution=10)
        # Positionner deux engins dans la même cellule H3 exacte
        system.update_vehicle_position("CAT-777-A", "DUMPER", -10.7100, 25.5000, 25.0)
        system.update_vehicle_position("CAT-777-B", "DUMPER", -10.7100, 25.5000, 20.0)

        conflicts = system.detect_proximity_conflicts("CAT-777-A")
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].risk_level, "CRITICAL")

        # Positionner un 3e engin dans la cellule adjacente en mouvement
        system.update_vehicle_position("CAT-777-C", "DUMPER", -10.71001, 25.50001, 22.0)
        conflicts_all = system.detect_proximity_conflicts("CAT-777-A")
        self.assertEqual(len(conflicts_all), 2)
        risk_levels = {c.risk_level for c in conflicts_all}
        self.assertIn("CRITICAL", risk_levels)
        self.assertIn("WARNING", risk_levels)



if __name__ == "__main__":
    unittest.main()
