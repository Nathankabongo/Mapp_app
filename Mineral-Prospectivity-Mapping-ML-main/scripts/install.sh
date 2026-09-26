#!/usr/bin/env bash
# Installation locale CriticalMineralsCompass (Kali / Debian)
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
  echo "Environnement virtuel créé : .venv/"
fi

.venv/bin/pip install -U pip
.venv/bin/pip install -e .

echo ""
echo "Installation terminée. Commandes utiles :"
echo "  source .venv/bin/activate"
echo "  critical-compass demo"
echo "  critical-compass list-models"
echo "  pytest"
