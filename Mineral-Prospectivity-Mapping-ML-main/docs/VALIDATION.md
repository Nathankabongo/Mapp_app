# Validation

## Procédure

1. `pytest` — y compris `tests/test_platform_national.py` (pas d’invention cadastrale).
2. Générer l’atlas, ouvrir le tableau de bord : vue centrée RDC, pas uniquement Kolwezi.
3. Page Cadastre : bandeau d’avertissement visible ; aucun titulaire fictif « SARL ».
4. Page Exploration hors emprise IA : favorabilité = information non disponible, pas un 0 % déguisé en certitude.
5. Page Sources : chaque couche a source, classe, officiel oui/non, confiance.
6. Export PDF/CSV depuis Rapports.
7. Couper le réseau : l’UI ne doit pas crasher (tuiles éventuellement vides).

## Critères d’acceptation

- Navigation 14 pages via la barre Streamlit.
- Filtres globaux persistants + réinitialisation.
- Disclaimer IA sur le potentiel minéral.
- Rôles documentés ; JWT API existant, login UI encore hors scope.
