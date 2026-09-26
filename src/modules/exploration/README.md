# Pilier 2 : Exploration & Intelligence Artificielle

Le pilier **Exploration & IA** regroupe les algorithmes géoscientifiques, les modèles de vision par ordinateur pour la télédétection et les wrappers de modélisation géologique 3D nécessaires pour réduire l'incertitude sur les cibles minières en RDC.

---

## 🏛️ Sous-modules

| Sous-module | Dépôt Source | Rôle Opérationnel | Technologie |
| :--- | :--- | :--- | :--- |
| [`geoscience-utils/`](geoscience-utils/) | `softwareunderground/awesome-open-geoscience` | Prétraitement géophysique (1VD, RTP, Signal Analytique), géochimie compositionnelle (CLR) et densité de failles. | Python, NumPy, SciPy, Pandas |
| [`site-detection/`](site-detection/) | `datakind/public-DKHQ_GlobalWitness` | Détection automatisée des chantiers miniers artisanaux et puits clandestins par télédétection multispectrale. | Python, SciPy (Morphologie), GeoJSON |
| [`geological-modeling/`](geological-modeling/) | `cgre-aachen/gempy` | Modélisation géologique implicite 3D (champ de potentiel RBF) et génération de modèles de blocs minéraliers. | Python, SciPy RBF, NumPy 3D |

---

## 🧪 Tests Rapides

```bash
python -m unittest tests/test_exploration_pillar.py
```
