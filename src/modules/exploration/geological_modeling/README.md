# Geological Modeling (`cgre-aachen/gempy`)

Ce module fournit un wrapper et un moteur d'interpolation implicite 3D pour la modélisation géologique structurale et l'estimation de volumes de corps minéralisés (*Block Models*), inspiré de la méthodologie **GemPy** (méthode du champ de potentiel).

---

## 🏔️ Capacités Implémentées

1. **Interpolation Implicite par Champ de Potentiel (`implicit_interpolator.py`) :**
   - Utilisation de splines RBF minces (*Thin Plate Splines*) pour reconstruire des surfaces géologiques continues et non planes (plis, synclinaux, failles).
   - Génération d'une grille 3D régulière discrétisée en unités lithologiques.

2. **Wrapper Modulaire (`gempy_wrapper.py`) :**
   - API fluide pour injecter les contacts de forages (`add_surface_point`) et les mesures d'orientation au compas géologique (`add_orientation`).
   - Calcul résilient avec gestion des stratigraphies par défaut.
   - Calcul du ratio volumique minéralisé (*Ore Volume Ratio*) pour l'estimation rapide des ressources.

---

## 🚀 Exemple d'Utilisation

```python
from src.modules.exploration.geological_modeling import GemPyGeologicalModel

# 1. Initialiser le projet de modélisation (emprise en mètres: X, Y, Z)
model = GemPyGeologicalModel(
    project_name="Gisement_Kolwezi_Nord",
    extent=(0, 2000, 0, 2000, -600, 200)
)

# 2. Injecter les données de forages (ex: toit de la minéralisation Cu-Co)
model.add_surface_point(x=500, y=500, z=-150, surface="OreBody")
model.add_surface_point(x=1000, y=800, z=-180, surface="OreBody")
model.add_surface_point(x=1500, y=1200, z=-210, surface="OreBody")

# 3. Injecter des mesures de pendage
model.add_orientation(x=1000, y=800, z=-180, azimuth=45.0, dip=25.0)

# 4. Calculer le modèle de blocs 3D
block_model = model.compute_model(resolution=(30, 30, 20))
summary = model.export_summary()

print(f"Total Blocs : {summary['total_blocks']}")
print(f"Blocs Minéralisés : {summary['ore_blocks']} ({summary['ore_volume_pct']} % du volume)")
```
