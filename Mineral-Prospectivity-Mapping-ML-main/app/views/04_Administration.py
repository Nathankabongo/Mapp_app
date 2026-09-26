"""04 — Administration, Business Intelligence & Data Hub."""

from __future__ import annotations

import streamlit as st
from app.components.header import render_page_header
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Administration", active_page="04_Administration")

render_page_header(
    title="Administration, Data Hub & Gouvernance",
    subtitle="Supervision du Datawarehouse spatial, connecteurs BNDG / SGN-C, traçabilité des blocs et paramétrage système.",
    sources="SGN-C (BNDG) · LOGEMA · SETEM RDC · Blockchain Ledger",
    context="Gouvernance Nationale",
)

tabs = st.tabs([
    "Business Intelligence & Décision",
    "Hub de Données & Passerelle SGN-C",
    "Paramètres & Sécurité",
])

with tabs[0]:
    run_legacy_page("10_Comparateur.py", "04_Administration")
    st.markdown("---")
    run_legacy_page("16_Decision.py", "04_Administration")
    with st.expander("Exports et Rapports PDF", expanded=False):
        run_legacy_page("12_Rapports_export.py", "04_Administration")

with tabs[1]:
    # Connexion en arrière-plan
    if "bndg_connector" not in st.session_state:
        from compass_core.connectors.sgnc_bndg import SgncBndgConnector
        st.session_state.bndg_connector = SgncBndgConnector()
        st.session_state.bndg_connector.authenticate()
    
    run_legacy_page("15_Data_API_Hub.py", "04_Administration")
    with st.expander("Détails des sources brutes", expanded=False):
        run_legacy_page("13_Donnees_sources.py", "04_Administration")

with tabs[2]:
    run_legacy_page("14_Administration.py", "04_Administration")
