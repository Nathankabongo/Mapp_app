# Exploration minière & Geo Model 3D

CriticalMineralsCompass est une **plateforme intelligente d'exploration minière** pour la RDC.

## Différenciation

```text
Logiciels traditionnels : FORAGES → MODÈLE 3D → ESTIMATION
Compass : SATELLITE+GÉOLOGIE+IA → PROSPECTIVITÉ → CIBLES → FORAGES → MODÈLE 3D → NOUVELLES CIBLES
```

## Pipeline MVP (vertical slice)

Zone → inventaire données → prospectivité IA → cibles → classement → carte → Next Best Drillhole → rapport JSON

## Pages

| Page | Rôle |
|------|------|
| Campagne exploration (`17_Campagne_exploration`) | Campagne centrale |
| Prospectivité / IA | Scores + confiance |
| Cibles | Hotspots classés |
| Décision exploration | TOP 5 + NBD |
| Forages | Collar / logs |
| Geo Model 3D | V1 trajectoires Plotly |

## Modules

`compass_core/exploration|drillholes|modelling|drilling|geophysics|geochemistry`

## Roadmap Geo 3D

V1 forages → V2 lithologie/surfaces → V3 + prospectivité → V4 géophysique/géochimie → V5 NBD & boucle

## Règles

- Jamais de teneur inventée
- DEMO-* pour forages pédagogiques
- Mesure ≠ interpolation ≠ prédiction IA
- Proposition de forage = à valider par un géologue
