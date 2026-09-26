# Fleet Tracking & Geofencing (`traccar/traccar`)

Ce module extrait et adapte les capacités de géo-clôtures et d'ingestion télémétrique du système open-source **Traccar** pour le suivi de flotte minière lourde (dumpers, excavatrices, camions de transport) et la sécurisation des concessions en RDC.

---

## 🚜 Capacités Implémentées

1. **Moteur de Géo-clôtures Virtuelles (`geofence_engine.py`) :**
   - Support des polygones complexes (test d'inclusion *Ray-Casting*), cercles géodésiques (*Haversine*) et corridors de transport.
   - Catégorisation minière : `ZEA`, `CAMI_PERMIT`, `PROTECTED_AREA` (ICCN), `BLAST_ZONE` (Tir de mine), `HAUL_ROAD` (Pistes), `WEIGH_STATION`.
   - Suivi d'état par engin : détection instantanée des franchissements (`GEOFENCE_ENTER`, `GEOFENCE_EXIT`) et des infractions de vitesse.

2. **Parseur Télémétrique (`telemetry_parser.py`) :**
   - Normalisation des paquets JSON (webhooks Traccar) et des trames GPS standard NMEA `$GPRMC`.
   - Suivi d'état d'engins : contact allumé/éteint, capteurs de benne levée (`bed_raised`), charge utile pesée (`payload_kg`).

3. **Moteur d'Alertes de Sécurité & Fraude (`alert_dispatcher.py`) :**
   - Alerte critique en cas d'intrusion d'engins dans des réserves naturelles protégées (ICCN).
   - Alerte critique lors de pénétration dans un périmètre de tir d'explosifs actif.
   - Alerte haute en cas de déversement suspect de minerai hors station de pesée officielle.

---

## 🚀 Exemple d'Utilisation

```python
from src.modules.geofencing.fleet_tracking import (
    GeofenceEngine,
    GeofenceZone,
    GeofenceType,
    ZoneCategory,
    TelemetryParser,
    FleetAlertDispatcher
)

# 1. Initialiser le moteur et enregistrer une aire protégée
engine = GeofenceEngine()
engine.register_zone(GeofenceZone(
    id="PARC-UPEMBA-01",
    name="Parc National de l'Upemba",
    category=ZoneCategory.PROTECTED_AREA,
    zone_type=GeofenceType.CIRCLE,
    center=(-9.50, 26.00),
    radius_m=5000.0
))

# 2. Configurer le répartiteur d'alertes
dispatcher = FleetAlertDispatcher(engine)

# 3. Traiter un paquet télémétrique d'un camion benne
telemetry = TelemetryParser.parse_json_packet({
    "deviceId": "DUMPER-CAT-777-04",
    "lat": -9.501,
    "lon": 26.002,
    "speed": 35.0,
    "payload_kg": 45000.0,
    "attributes": {"bed_raised": False}
})

alerts = dispatcher.process_telemetry(telemetry)
for alert in alerts:
    print(f"[{alert.severity}] {alert.rule}: {alert.description}")
```
