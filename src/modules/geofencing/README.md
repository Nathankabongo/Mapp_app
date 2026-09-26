# Pilier 3 : Geofencing & Localisation

Le pilier **Geofencing & Localisation** assure le suivi temps-réel des flottes d'engins miniers lourds, la surveillance des franchissements de limites de titres CAMI / aires protégées ICCN, et la prévention des collisions par maillage hexagonal discret.

---

## 🏛️ Sous-modules

| Sous-module | Dépôt Source | Rôle Opérationnel | Technologie |
| :--- | :--- | :--- | :--- |
| [`fleet-tracking/`](fleet-tracking/) | `traccar/traccar` | Moteur de clôtures virtuelles (polygones CAMI, ZEA, parcs ICCN), parsing télémétrique et alertes de sécurité/fraude. | Python, Traccar Webhook / NMEA |
| [`spatial-indexing/`](spatial-indexing/) | `uber/h3` | Indexation spatiale hexagonale haute performance, buffer de tirs de mine et système anti-collision d'engins miniers. | Python, Uber H3 (v4), O(1) Lookup |

---

## 🧪 Tests Rapides

```bash
python -m unittest tests/test_geofencing_pillar.py
```
