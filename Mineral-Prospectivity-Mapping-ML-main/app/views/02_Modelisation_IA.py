"""02 — Moteur Prédictif GeoAI & Modélisation Géologique 3D — Sans Stickers."""

from __future__ import annotations

import streamlit as st
from app.components.header import render_page_header
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Modélisation & IA", active_page="02_Modelisation_IA")

render_page_header(
    title="Moteur Prédictif GeoAI & Modélisation 3D",
    subtitle="Cartographie de prospectivité minérale par fusion multi-critères, modélisation implicite 3D et réduction de l'incertitude épistémique.",
    sources="GeoCongo AI · GemPy RBF · Ensembles Random Forest & WoE",
    context=filters.get("province", "Ceinture Cupro-Cobaltifère Katanga"),
)

tabs = st.tabs([
    "Cartographie Prédictive 2D (XAI)",
    "Jumeau Numérique & Modèle 3D",
    "Évaluation des Incertitudes & VoI",
])

with tabs[0]:
    run_legacy_page("07_Potentiel_mineral_IA.py", "02_Modelisation_IA")

with tabs[1]:
    run_legacy_page("20_Geo_Model_3D.py", "02_Modelisation_IA")

with tabs[2]:
    run_legacy_page("22_Incertitude.py", "02_Modelisation_IA")
