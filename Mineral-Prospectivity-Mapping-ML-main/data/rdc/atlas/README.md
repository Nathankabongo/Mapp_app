# Atlas minier RDC

Référentiel cartographique multi-minéraux pour CriticalMineralsCompass.

## Génération

```bash
critical-compass generate-atlas
```

Produit :
- `deposits_*.gpkg` — gisements par commodité (Cu-Co, Li, Au, Coltan, Diamant)
- `cadastre_permis.gpkg` — permis miniers CAMI (démo)
- `catalog.json` — métadonnées des couches

## Import CAMI / QGIS

```bash
critical-compass import-atlas \
  --source /chemin/vers/couche_cami.gpkg \
  --commodity cu_co
```

Champs reconnus automatiquement : `nom`, `province`, `statut`, `type_gisement`, `numero_permis`, etc.

## Commodités

| Code | Zone | Gisements de référence |
|------|------|------------------------|
| `cu_co` | Lualaba, Haut-Katanga | Tenke-Fungurume, Mutanda, Kamoto |
| `li` | Tanganyika | Manono-Kitotolo |
| `au` | Est RDC | Kibali, Mongbwalu, Kamituga |
| `coltan` | Kivu | Rubaya, Numbi |
| `diamond` | Kasaï | Mbuji-Mayi, Bakwanga |

## Interface

Onglet **Atlas minier** dans Streamlit : carte nationale, filtres provinciaux, cadastre, tableau des gisements.
