# Données et sources

| Couche | Classe | Officiel | Notes |
|--------|--------|----------|--------|
| CAMI | officielle **si** export chargé | Oui seulement alors | https://rdc.mines-rdc.cd/ — non téléchargé automatiquement |
| Atlas Compass | historique / démo | Non | Points publics approximatifs + `atlas_demo` |
| Cadastre généré | démonstration | Non | Préfixe `DEMO-`, titulaire vide |
| USGS MRDS | open data | Non | Intégrer un extrait ISO=CD avant usage opérationnel |
| OSM / ESRI / OpenTopo | open data | Non | Fonds tuiles, mode online |
| WorldPop | estimée | Non | Proxy `.npy` si pas de GeoTIFF licence |
| SRTM / stack Kolwezi | open / échantillon | Non | Emprise souvent locale |
| Favorabilité ML | modélisée | Non | Indice prédictif, emprise d'entraînement |

CRS d’affichage / stockage géographique : **EPSG:4326**.

Distances générales : **géodésiques** (haversine).

Analyses métriques : **UTM automatique** selon longitude (zones 32S–36S pour la RDC).  
`EPSG:32733` n’est **pas** la projection nationale — il reste pertinent pour la zone pilote Kolwezi lorsque le raster l’impose.

Voir `compass_core.gis.crs.crs_strategy_doc()`.

Si une source distante manque : *Source temporairement indisponible. Utilisation de la dernière donnée locale disponible.*

Ne jamais présenter un score IA comme un gisement confirmé.

Chaîne de crédibilité : Observation satellite → Indice/anomalie → Prédiction modèle → Validation terrain → Donnée géologique confirmée.
