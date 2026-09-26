# Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[ui,api,report,dev]"
```

GDAL optionnel pour rasters : `pip install -e ".[gis]"` (nécessite `libgdal-dev`).

```bash
# Atlas de démonstration (occurrences de référence + couche cadastrale DÉMO)
python -c "from compass_core.analysis.mineral_layers import generate_atlas_layers; generate_atlas_layers()"

# Dataset SIG Kolwezi d'exemple (MNT / favorabilité pilote)
critical-compass generate-sample-data

streamlit run app/streamlit_app.py
# ou
streamlit run app/main.py
```

Interface : http://127.0.0.1:8501  
API : `uvicorn api.main:app --port 8000`

Docker : `docker compose up --build`

Identifiants API Docker : `admin` / `compass-rdc` (JWT).
