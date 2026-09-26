# Spatial Indexing (`uber/h3`)

Ce module intègre le système d'indexation spatiale discrète et hiérarchique **Uber H3** pour accélérer de façon critique les calculs de distance, de couverture géométrique et de sécurité sur les concessions et fosses minières en RDC.

---

## 🛑 Avantages du Maillage Hexagonal en Contexte Minier

Contrairement aux carroyages rectangulaires classiques où les distances entre cellules voisines varient (diagonale vs côtés orthogonaux), les cellules hexagonales H3 garantissent que :
1. **Tous les voisins sont équidistants :** Les 6 voisins d'un hexagone sont à une distance strictement identique du centroïde.
2. **Complexité Algorithmique $O(1)$ :** Les tests de proximité spatiale et de recherche d'engins dans un rayon donné se réduisent à des recherches de clés dans une table de hachage en mémoire vive, sans calcul trigonométrique lourd.

---

## ⚙️ Composants

1. **`h3_indexer.py` :**
   - Conversion `(lat, lon)` vers index H3.
   - Calcul des disques d'adjacence `get_k_ring(cell, k)`.
   - Polyfill de boîtes englobantes et concessions CAMI.
   - Résolutions types :
     - **Résolution 7 :** Concession régionale CAMI (~1.2 km).
     - **Résolution 9 :** Carreau de mine / chantiers artisanaux ZEA (~100 m).
     - **Résolution 10 :** Alerte d'angle mort et collision d'engins lourds (~65 m).

2. **`collision_prevention.py` :**
   - Moteur temps-réel de détection de risques de collision entre dumpers, pelles de chargement et véhicules légers.
   - Alerte `CRITICAL` si deux engins partagent la même cellule H3, et `WARNING` si adjacent avec vitesse $> 15$ km/h.

---

## 🚀 Exemple d'Utilisation

```python
from src.modules.geofencing.spatial_indexing import MiningCollisionPreventionSystem

# 1. Initialiser le système anti-collision (résolution 10 ~65m)
system = MiningCollisionPreventionSystem(resolution=10)

# 2. Positionner un camion benne CAT 777 (dans la fosse)
system.update_vehicle_position(
    vehicle_id="DUMPER-01",
    vehicle_type="DUMPER",
    lat=-10.7100,
    lon=25.5000,
    speed_kmh=25.0
)

# 3. Positionner un véhicule léger à proximité immédiate
system.update_vehicle_position(
    vehicle_id="PICKUP-SEC-02",
    vehicle_type="LIGHT_VEHICLE",
    lat=-10.7101,
    lon=25.5001,
    speed_kmh=30.0
)

# 4. Évaluer les conflits
conflicts = system.detect_proximity_conflicts("DUMPER-01")
for c in conflicts:
    print(f"[{c.risk_level}] {c.message}")
```
