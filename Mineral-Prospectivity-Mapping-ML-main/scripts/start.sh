#!/usr/bin/env bash
# Démarre API FastAPI + Streamlit (local)
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

if [ ! -d .venv ]; then
  echo "Création du venv…"
  python3 -m venv .venv
  .venv/bin/pip install -U pip
  .venv/bin/pip install -e ".[api,ui,report]"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

export COMPASS_JWT_ENABLED="${COMPASS_JWT_ENABLED:-false}"
export COMPASS_API_URL="${COMPASS_API_URL:-http://127.0.0.1:8000}"

mkdir -p outputs/docs logs data/rdc/kolwezi

if [ ! -f data/rdc/kolwezi/stack_multiphysics.tif ]; then
  echo "→ Génération du jeu de données Kolwezi d'exemple…"
  critical-compass generate-sample-data || python scripts/generate_sample_data.py || true
fi

echo "→ Export documentation OpenAPI PDF…"
python scripts/export_openapi_pdf.py --output outputs/docs/api_reference.pdf || true

echo "→ Démarrage API sur http://127.0.0.1:8000"
uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
API_PID=$!

echo "→ Démarrage Streamlit sur http://127.0.0.1:8501"
streamlit run app/streamlit_app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --browser.gatherUsageStats=false > logs/streamlit.log 2>&1 &
UI_PID=$!

sleep 3

if curl -sf http://127.0.0.1:8000/health > /dev/null; then
  echo "✓ API opérationnelle : http://127.0.0.1:8000/docs"
else
  echo "⚠ API en cours de démarrage — voir logs/api.log"
fi

echo "✓ Streamlit : http://127.0.0.1:8501"
echo ""
echo "PIDs : API=$API_PID  Streamlit=$UI_PID"
echo "Logs : logs/api.log  logs/streamlit.log"
echo "Arrêt : kill $API_PID $UI_PID"

wait
