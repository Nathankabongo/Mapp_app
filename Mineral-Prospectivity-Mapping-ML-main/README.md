# CriticalMineralsCompass

**Plateforme de cartographie de prospectivité minérale pour la RDC.**

Adaptation du dépôt [Mineral-Prospectivity-Mapping-ML](https://github.com/) (Hamassana, Soudan) en moteur modulaire **compass_core**, déployable offline ou via API cloud.

---

## Démarrage rapide (sans dataset)

Aucune donnée SIG n'est nécessaire pour valider l'installation :

```bash
# Installation minimale
pip install -e .

# Lister les modèles
critical-compass list-models

# Démo complète en mémoire (WoE, ~2 s)
critical-compass demo

# Démo avec Random Forest
critical-compass demo --model rf --output-dir outputs/demo_rf

# Valider une configuration JSON
critical-compass validate-config --config config/config_demo.json
critical-compass validate-config --config config/config_rdc_kolwezi.json --check-files
```

**Sorties de la démo** : `outputs/demo/kolwezi_woe_cu_co_favorability.npy` + `provenance.json`

---

## Installation complète (avec SIG)

```bash
sudo apt install gdal-bin libgdal-dev   # Linux
pip install -e ".[all]"
```

---

## Architecture

```
compass_core/     # Moteur métier (data, models, pipeline, export, provenance)
cli/              # critical-compass (CLI offline)
api/              # FastAPI (mode cloud)
app/              # Streamlit (visualisation)
config/           # JSON par région / mode démo
legacy/           # Scripts originaux Soudan
```

### Modèles

| Code | Algorithme | Dépendances |
|------|------------|-------------|
| `woe` | Weights of Evidence | numpy, sklearn |
| `rf` | Random Forest | sklearn |
| `svm` | SVM (RBF) | sklearn |
| `ann` | Réseau dense Keras | TensorFlow |
| `cnn` | Conv1D Keras | TensorFlow |

---

## Jeu de données Kolwezi (exemple)

Générez un dataset SIG géoréférencé sans données externes :

```bash
critical-compass generate-sample-data
critical-compass run --config config/config_rdc_kolwezi_sample.json
```

Fichiers créés dans `data/rdc/kolwezi/` : raster 64×64 (8 bandes), gisements Cu-Co, train/test.
Voir `data/rdc/kolwezi/README.md` pour le détail des bandes et formats.

---

## Quand vous aurez des données réelles (Kolwezi)

```bash
critical-compass split-samples \
  --samples data/rdc/kolwezi/deposits_cu_co.gpkg \
  --train-out data/rdc/kolwezi/training.gpkg \
  --test-out data/rdc/kolwezi/testing.gpkg

critical-compass run --config config/config_rdc_kolwezi.json
```

---

## Tests

```bash
pytest
ruff check compass_core cli api tests
```

---

## Lancer l'application (local)

```bash
bash scripts/start.sh
# ou manuellement :
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
streamlit run app/streamlit_app.py
```

| Service | URL |
|---------|-----|
| **API** (Swagger) | http://127.0.0.1:8000/docs |
| **Streamlit** | http://127.0.0.1:8501 |
| **Doc PDF** | `outputs/docs/api_reference.pdf` |

---

## Docker Compose

```bash
cp .env.example .env   # ajuster COMPASS_JWT_SECRET
docker compose up --build

# Générer la doc PDF :
docker compose --profile docs run docs
```

Services : `api` (8000), `streamlit` (8501). JWT activé par défaut en Docker.

Identifiants par défaut : `admin` / `compass-rdc`

---

## Authentification JWT

```bash
# Activer (production / Docker)
export COMPASS_JWT_ENABLED=true
export COMPASS_JWT_SECRET="votre-secret-long"

# Obtenir un token
curl -X POST http://127.0.0.1:8000/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"compass-rdc"}'

# Appel protégé
curl -X POST http://127.0.0.1:8000/v1/demo \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"woe"}'
```

En local, JWT est **désactivé** par défaut (`COMPASS_JWT_ENABLED=false`).

---

## Documentation OpenAPI PDF

```bash
python scripts/export_openapi_pdf.py --output outputs/docs/api_reference.pdf
```

Produit aussi `outputs/docs/api_reference.json`.

---

```bash
pip install -e ".[api]"
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/health` | GET | Santé du service |
| `/v1/models` | GET | Liste des modèles |
| `/v1/demo` | POST | Démo synthétique sans dataset |
| `/v1/validate` | POST | Valider config JSON inline |
| `/v1/validate-config` | GET | Valider un fichier config |
| `/v1/run/inline` | POST | Pipeline (synthétique ou SIG) |

```bash
curl -X POST http://127.0.0.1:8000/v1/demo \
  -H "Content-Type: application/json" \
  -d '{"model":"woe","seed":42}'
```

---

## Streamlit

```bash
pip install -e ".[ui]"
streamlit run app/streamlit_app.py
```

Application nationale **14 pages** (tableau de bord, carte, exploration, sites, cadastre, SIG, IA, risques, démographie, comparateur, projets, rapports, sources, administration). Voir `docs/INSTALL.md` et `docs/ARCHITECTURE.md`.


---

## CI (GitHub Actions)

Workflow `.github/workflows/ci.yml` :
- Ruff (lint) sur Python 3.11 & 3.12
- Pytest + couverture `compass_core`
- Smoke test Docker

---

## Provenance

Chaque exécution produit `provenance.json` : `run_id`, horodatage UTC, graine, hyperparamètres, métriques (AUC, kappa).
