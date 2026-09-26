# Mapp_app : Plateforme Intégrée de Prospectivité Minérale, Traçabilité & Geofencing

Plateforme complète de gestion, cartographie prédictive et sécurisation des ressources minérales stratégiques en RDC (République Démocratique du Congo). 

Le projet combine intelligence artificielle appliquée aux géosciences, modélisation géologique 3D, traçabilité par registres distribués / smart contracts et surveillance géospatiale temps réel par géofencing.

---

## 🏛️ Architecture & Piliers du Projet

```
Mapping/
├── src/modules/
│   ├── exploration/        # Pilier 2 : Exploration & IA Géoscientifique
│   ├── geofencing/         # Pilier 3 : Geofencing & Localisation d'engins
│   └── traceability/       # Pilier 1 : Traçabilité Blockchain & IoT
├── Mineral-Prospectivity-Mapping-ML-main/
│   ├── compass_core/       # Moteur métier ML & SIG (WoE, RF, SVM, ANN, CNN)
│   ├── cli/                # Interface en ligne de commande (critical-compass)
│   ├── api/                # API REST FastAPI
│   ├── app/                # Application interactive Streamlit
│   ├── config/             # Profils miniers & configurations régionales (Kolwezi, etc.)
│   └── tests/              # Suite de tests unitaires et d'intégration
├── .gitignore              # Règles d'exclusion Git
└── README.md               # Documentation générale
```

---

## 🚀 Les 4 Piliers Fondamentaux

### 1. 🔗 Traçabilité (Blockchain & Smart Contracts)
*Dossier : `src/modules/traceability/`*
- **Hyperledger Fabric (Chaincode Go & SDK Python)** : Enregistrement immuable des lots de minerais, historique de pesée sur site, audits QA/QC et transferts de garde.
- **Smart Contracts (Solidity ^0.8.20)** :
  - `MineralBatchERC1155.sol` : Tokenisation semi-fongible de lots par qualité/teneur.
  - `MineralLotNFT.sol` : Passeport numérique unitaire (Battery Passport / traçabilité ESG).
  - Contrôle d'accès RBAC et interfaces standardisées.

### 2. 🛰️ Exploration & IA Géoscientifique
*Dossier : `src/modules/exploration/`*
- **Géophysique & Géochimie (`geoscience-utils`)** : Prétraitement géophysique (1VD, Réduction au Pôle, Signal Analytique), transformation CLR (Centered Log-Ratio) et analyse de densité de linéaments.
- **Détection Multispectrale (`site-detection`)** : Détection automatisée de chantiers artisanaux et puits clandestins par imagerie satellitaire.
- **Modélisation Géologique 3D (`geological-modeling`)** : Wrappers d'interpolation implicite 3D (champs de potentiel RBF, modèles de blocs).

### 3. 📍 Geofencing & Localisation Flotte
*Dossier : `src/modules/geofencing/`*
- **Fleet Tracking (`fleet-tracking`)** : Moteur de barrières virtuelles (concessions CAMI, zones ZEA, réserves ICCN), ingestion de télémétrie NMEA/Traccar et alertes de franchissement illicite.
- **Indexation Spatiale Hexagonale (`spatial-indexing`)** : Grille discrète Uber H3 ($O(1)$ spatial lookup), zones tampons de tir de mine et prévention des collisions d'engins lourds.

### 4. 🧭 Modélisation de Prospectivité Minérale (CriticalMineralsCompass)
*Dossier : `Mineral-Prospectivity-Mapping-ML-main/`*
- **Algorithmes ML prédictifs** :
  - **WoE (Weights of Evidence)** : Poids de preuve bayésiens pour ciblage minéral.
  - **Random Forest (RF)**, **SVM**, **ANN**, **CNN (Conv1D)**.
- **Profils Minéraux RDC** : Cuivre, Cobalt, Lithium, Coltan (Tantale), Or, Manganèse, Terres Rares, etc.
- **Interfaces Utilisateur** :
  - CLI : `critical-compass`
  - Dashboard interactif Streamlit (`app/`)
  - API cloud FastAPI (`api/`)

---

## 🛠️ Installation & Démarrage

### Prérequis
- Python 3.11+
- Git
- (Optionnel) GDAL pour le traitement SIG avancé

### Installation rapide

```bash
# Cloner le dépôt
git clone https://github.com/Nathankabongo/Mapp_app.git
cd Mapp_app

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Sous Linux/macOS
# ou sous Windows :
# .venv\Scripts\activate

# Installer les dépendances du moteur de prospectivité
cd Mineral-Prospectivity-Mapping-ML-main
pip install -e .
```

### Lancer la démonstration rapide
```bash
# Démo en mémoire (modèle WoE)
critical-compass demo

# Lancer le dashboard Streamlit
streamlit run app/Home.py
```

---

## 🧪 Exécution des Tests

Les tests unitaires couvrent l'ensemble des modules :

```bash
# Tests des piliers Exploration, Geofencing et Traçabilité
python -m unittest discover -s Mineral-Prospectivity-Mapping-ML-main/tests -p "test_*.py"

# Tests spécifiques
python -m unittest Mineral-Prospectivity-Mapping-ML-main/tests/test_traceability_pillar.py
python -m unittest Mineral-Prospectivity-Mapping-ML-main/tests/test_geofencing_pillar.py
python -m unittest Mineral-Prospectivity-Mapping-ML-main/tests/test_exploration_pillar.py
```

---

## 📜 Licence & Contribution
Projet développé pour la gestion et la valorisation du secteur minier.
Consultez la documentation spécifique dans chaque sous-répertoire pour plus de détails techniques.