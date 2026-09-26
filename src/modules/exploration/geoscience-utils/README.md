# Geoscience Utils (`softwareunderground/awesome-open-geoscience`)

Ce module regroupe les fonctions algorithmiques essentielles issues des standards de la communauté open-source géoscientifique (*Software Underground*), adaptées pour le prétraitement des levés géophysiques, géochimiques et structuraux en RDC.

---

## 🔬 Capacités Implémentées

### 1. Filtrage Géophysique Magnétique (`magnetics.py`)
- **Première Dérivée Verticale (1VD) :** Améliore la détection des contacts lithologiques superficiels et failles minéralisées.
- **Signal Analytique (Total Gradient) :** Indépendant de la rémanence magnétique et de l'inclinaison.
- **Réduction au Pôle (RTP) :** Recentre les dipôles magnétiques à la verticale des gisements.

### 2. Géochimie Compositionnelle (`geochem.py`)
- **Transformation Centered Log-Ratio (CLR) :** Élimine le biais de somme constante (*closure effect*) des dosages en ppm/%.
- **Score d'Anomalie Multivariée Robuste :** Normalisation par médiane et écart interquartile (MAD) pour cibler les anomalies multi-éléments (ex: Cu-Co, Li-Ta).

### 3. Analyse Structurale & Failles (`lineaments.py`)
- **Densité des Failles :** Convolution gaussienne des linéaments structuraux.
- **Proximité Décroissante :** Modélisation de la favorabilité métallogénique en fonction de la distance euclidienne aux accidents majeurs.

---

## 🚀 Exemple d'Utilisation

```python
import numpy as np
import pandas as pd
from src.modules.exploration.geoscience_utils import (
    first_vertical_derivative,
    centered_log_ratio,
    compute_fault_proximity
)

# 1. Traitement géophysique
tmi_grid = np.random.uniform(33000, 34000, size=(100, 100))
vd1 = first_vertical_derivative(tmi_grid, cell_size_m=50.0)

# 2. Traitement géochimique
assays = pd.DataFrame({"Cu": [150.0, 4500.0, 12.0], "Co": [20.0, 320.0, 5.0], "Fe": [25000.0, 42000.0, 18000.0]})
clr_assays = centered_log_ratio(assays, elements=["Cu", "Co", "Fe"])

# 3. Proximité structurale
fault_mask = np.zeros((100, 100), dtype=bool)
fault_mask[50, :] = True # Faille est-ouest
proximity = compute_fault_proximity(fault_mask, pixel_size_m=50.0)
```
