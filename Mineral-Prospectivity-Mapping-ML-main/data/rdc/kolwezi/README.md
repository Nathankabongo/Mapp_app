# Données RDC — CriticalMineralsCompass

Placez ici vos jeux de données géospatiaux pour la zone pilote **Kolwezi**.

## Générer le jeu d'exemple (recommandé)

Aucune donnée externe requise — un raster multiphysique géoréférencé et des gisements Cu-Co synthétiques sont créés automatiquement :

```bash
critical-compass generate-sample-data
# ou
python scripts/generate_sample_data.py
```

Puis lancez le pipeline SIG :

```bash
critical-compass run --config config/config_rdc_kolwezi_sample.json
```

## Structure du jeu Kolwezi

```
data/rdc/kolwezi/
├── stack_multiphysics.tif         # Raster 64×64, 8 bandes (EPSG:32733)
├── stack_multiphysics.bands.json  # Descripteur des bandes
├── deposits_cu_co.gpkg            # ~60 points Cu-Co (champ Value: 0|1)
├── training.gpkg                  # Échantillons entraînement (80 %)
├── testing.gpkg                   # Échantillons test (20 %)
└── metadata.json                  # Métadonnées du jeu
```

### Bandes du raster multiphysique

| Bande | Nom | Description |
|-------|-----|-------------|
| B1 | `mag_total` | Anomalie magnétique totale |
| B2 | `mag_derivative` | Dérivée verticale magnétique |
| B3 | `radiometry_k` | Potassium radiométrique |
| B4 | `radiometry_th` | Thorium radiométrique |
| B5 | `radiometry_u` | Uranium radiométrique |
| B6 | `spectro_clay` | Indice argiles / altération |
| B7 | `geology_code` | Code lithologique |
| B8 | `elevation` | MNT |

**Emprise** : ~16 km × 16 km autour de Kolwezi (UTM 33S, origine 547 000 E / 8 825 000 N).

## Données réelles (production)

Pour vos propres données CAMI / Xcalibur / QGIS :

| Fichier | Format | Notes |
|---------|--------|-------|
| `stack_multiphysics.tif` | GeoTIFF multi-bandes | Empiler mag/rad/spectro/géologie |
| `deposits_cu_co.gpkg` | GeoPackage (points) | Champ `Value` binaire obligatoire (0\|1) |
| `training.gpkg` / `testing.gpkg` | GeoPackage | Générés par `split-samples` |

**CRS recommandé** : EPSG:32733 (UTM 33S)

```bash
critical-compass split-samples \
  --samples data/rdc/kolwezi/deposits_cu_co.gpkg \
  --train-out data/rdc/kolwezi/training.gpkg \
  --test-out data/rdc/kolwezi/testing.gpkg

critical-compass run --config config/config_rdc_kolwezi.json
```

## Commodités cibles

| Code | Commodité | Zone type |
|------|-----------|-----------|
| `cu_co` | Cuivre-Cobalt | Kolwezi, Fungurume |
| `li` | Lithium | Pegmatites Manono |
| `au` | Or | Formations orientales |
| `diamond` | Diamant | Kimberlites |
| `coltan` | Coltan | Pegmatites, placers |

## Formats compatibles

| Source | Format | Notes |
|--------|--------|-------|
| CAMI / SIG gouvernemental | GeoPackage, Shapefile | CRS : EPSG:32733 |
| Xcalibur Multiphysics | GeoTIFF | Empiler les bandes |
| Forages / affleurements | GeoPackage (points) | Attribut `Value` binaire |
| QGIS | Export `.gpkg` / `.tif` | Import direct des résultats |
