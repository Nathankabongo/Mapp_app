# Architecture intelligence géospatiale

Le design system UI reste inchangé. La plateforme évolue vers un **moteur de connaissance et de prospectivité**.

## Pipeline

```text
SOURCE → CONNECTOR → NORMALISATION → COMMON DATA MODEL → ANALYSIS → STREAMLIT / API / REPORT
```

## Modules `compass_core/`

| Package | Rôle |
|---------|------|
| `api/` | Registre sources, connecteurs, adapters |
| `gis/` | CRS national, couches, analyse spatiale |
| `satellite/` | Sentinel/Landsat (probe), indices, change detection |
| `geology/` | Géologie, géophysique, géochimie |
| `mining/` | CAMI, occurrences, ASM |
| `prospectivity/` | Features, modèles, prédiction, confiance |
| `environment/` | État environnemental |
| `decision/` | Recommandation explicable |
| `risk/` / `social/` | Réexports |

## Pages nouvelles

- `15_Data_API_Hub.py` — catalogue sources / connecteurs
- `16_Decision.py` — parcours MVP zone → décision

## API REST (JWT optionnel comme le reste)

- `GET /api/areas`
- `GET /api/layers`
- `GET /api/minerals`
- `GET /api/sources`
- `GET /api/prospectivity/{area}?mineral=cuivre`
- `GET /api/environment/{area}`
- `GET /api/mining/{area}`
- `GET /api/risk/{area}`
- `GET /api/decision/{area}`

## MVP vertical

Kolwezi + Cuivre : raster WoE local → score + confiance + couches disponibles/manquantes → décision.

## Règle

Concessions vérifiées = 0 sans fichier sous `data/rdc/official/`.
