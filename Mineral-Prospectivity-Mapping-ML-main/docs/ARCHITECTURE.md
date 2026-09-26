# Architecture CriticalMineralsCompass RDC

## Décisions (phases 1–5)

1. **Produit** : système national d’aide à la décision, pas une carte à marqueurs.
2. **Couverture** : vue initiale = RDC entière. Kolwezi = zone pilote IA / MNT, pas le centre unique.
3. **Vérité** : six classes de données (officielle, open data, historique, estimée, modélisée, calculée) + démonstration. Jamais d’invention de permis, réserves, teneurs, opérateurs.
4. **IA** : indice 0–100, disclaimer obligatoire, hors raster = non évalué.
5. **Stack** : Streamlit multipage, Folium, GeoPandas, `compass_core`, FastAPI existante, JWT optionnel.
6. **Offline-first** : crash interdit si CAMI / WorldPop / USGS injoignables ; message de fallback local.

Hypothèses à vérifier : accès et licence CAMI, millésime WorldPop, emprise SRTM nationale, CRS des exports officiels.

Voir le canvas d’architecture dans Cursor (companion) et `docs/DATA.md`.

## Évolution intelligence (v2)

Architecture API-first détaillée dans [`docs/INTELLIGENCE.md`](INTELLIGENCE.md).

## Exploration & Geo Model 3D (v3)

Voir [`docs/EXPLORATION.md`](EXPLORATION.md) — pipeline cibles, forages, Next Best Drillhole, roadmap V1–V5.
