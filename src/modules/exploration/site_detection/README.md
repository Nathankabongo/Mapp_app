# Site Detection (`datakind/public-DKHQ_GlobalWitness`)

Ce module adapte les modèles et approches de vision par ordinateur développés par **DataKind** et **Global Witness** pour la détection automatisée des chantiers miniers artisanaux et de l'orpaillage/creusement clandestin à partir d'imagerie satellitaire (Sentinel-2, Landsat).

---

## 🛰️ Pipeline Algorithmique

1. **Extraction d'Indices Multispectraux Spécifiques :**
   - $BSI$ (*Bare Soil Index*) : Détection des sols décapés et affleurements rocheux fraîchement excavés.
   - $NDVI$ (*Vegetation Index*) : Détection de la clairière / déforestation brutale causée par l'ouverture d'un puits.
   - $NDWI$ (*Water Index*) : Détection des excavations inondées, bassins de lavage et décantation de rejets.
   - $Score_{\text{excavation}} = 0.7 \times (BSI - NDVI) + 0.3 \times \max(0, NDWI)$

2. **Segmentation & Filtrage Morphologique :**
   - Élimination des pixels bruités par ouverture/fermeture binaire (`binary_opening`, `binary_closing`).
   - Regroupement des composantes connexes en clusters d'activité.

3. **Vectorisation GeoJSON :**
   - Calcul de la superficie en hectares, score de confiance, bounding box et coordonnées centroïdes pour croisement immédiat avec la géo-clôture CAMI.

---

## 🚀 Exemple d'Utilisation

```python
import numpy as np
from src.modules.exploration.site_detection import MiningSiteDetector, filter_and_polygonize_sites

# 1. Simuler ou charger des bandes Sentinel-2 (taille 256x256)
blue, green, red, nir, swir1 = [np.random.rand(256, 256) for _ in range(5)]

# 2. Détecter les anomalies d'excavation
detector = MiningSiteDetector(bsi_threshold=0.15, ndvi_max_threshold=0.25)
mask = detector.detect_sites(blue, green, red, nir, swir1)

# 3. Extraire les polygones GeoJSON des sites détectés
sites = filter_and_polygonize_sites(
    mask,
    min_pixels=5,
    pixel_size_m=10.0,
    origin_lon=25.45,
    origin_lat=-10.65
)

print(f"Sites miniers détectés : {len(sites)}")
for site in sites[:3]:
    print(site["properties"])
```
