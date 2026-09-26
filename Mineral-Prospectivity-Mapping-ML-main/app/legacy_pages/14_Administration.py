"""14 — Administration / configuration."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from app.components.empty_state import render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.section_header import render_section
from app.helpers import DEFAULT_API_URL, DEFAULT_DATA_DIR, check_api_health, generate_sample_dataset, render_api_status
from app.shell import bootstrap, close_page, masthead
from compass_core.analysis.mineral_layers import generate_atlas_layers
from compass_core.constants import ROLES, UNAVAILABLE
from compass_core.io.data_sources import list_available_sources
from compass_core.models.risk import load_rules
from compass_core.validation.data_quality import system_health

filters = bootstrap("Administration", active_page="Configuration")
masthead(
    "Administration & configuration",
    "Sources, seuils, modèles, synchronisation et qualité des données. "
    "Rôles prévus — login UI non imposé en local.",
    sources="config/ · logs/ · API JWT optionnelle",
)

health = system_health()
render_section("État système")
render_kpi_row(
    [
        {
            "label": "Dernière sync",
            "value": health["last_sync"].split(" ")[0],
            "footnote": health["last_sync"],
            "data_class": "computed",
        },
        {"label": "Dernière erreur", "value": "—", "footnote": UNAVAILABLE, "data_class": "unavailable"},
        {
            "label": "Qualité",
            "value": "Partielle",
            "footnote": health["quality"],
            "data_class": "demo",
        },
    ]
)

render_section("Sources")
for row in list_available_sources():
    st.caption(f"{row['label']} — {row['status']} (`{row['local']}`)")

render_section("Rôles prévus")
st.write(", ".join(ROLES))
render_warning_state(
    f"Authentification JWT côté API (COMPASS_JWT_ENABLED={os.getenv('COMPASS_JWT_ENABLED', 'false')}). "
    "L'UI Streamlit locale n'impose pas encore de login.",
    title="Sécurité",
)

render_section("Seuils de risque")
st.json(load_rules())

render_section("Actions")
a1, a2 = st.columns(2)
with a1:
    if st.button("Régénérer l'atlas de démonstration", use_container_width=True):
        generate_atlas_layers()
        st.success("Atlas écrit dans data/rdc/atlas")
with a2:
    if st.button("Générer dataset Kolwezi d'exemple", use_container_width=True):
        generate_sample_dataset(DEFAULT_DATA_DIR)
        st.success("Dataset Kolwezi")

render_section("API")
render_api_status(DEFAULT_API_URL)
health_api = check_api_health(DEFAULT_API_URL)
st.caption("Santé API : " + ("OK" if health_api else "indisponible — mode offline UI"))

render_section("Logs")
st.caption(f"API log : {'présent' if Path('logs/api.log').exists() else UNAVAILABLE}")
st.caption(f"UI log : {'présent' if Path('logs/streamlit.log').exists() else UNAVAILABLE}")
st.caption("Ne placez aucun export CAMI sensible dans le dépôt git.")

_ = filters
close_page()
