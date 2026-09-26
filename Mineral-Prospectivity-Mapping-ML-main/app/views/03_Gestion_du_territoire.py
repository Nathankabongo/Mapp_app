"""03 — Gestion du Territoire, Cadastre & Opérations Terrain — Sans Stickers."""

from __future__ import annotations

import streamlit as st
from app.components.header import render_page_header
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Gestion du territoire", active_page="03_Gestion_du_territoire")

render_page_header(
    title="Gestion du Territoire & Opérations Minières",
    subtitle="Contrôle des permis CAMI (PR, PE, ZEA), suivi des forages d'exploration, smart sampling et gestion des risques de surface.",
    sources="Cadastre Minier (CAMI) · BIGEMIP · SENTECH · ICCN",
    context=filters.get("province", "Toute la RDC"),
)

tabs = st.tabs([
    "Registre Foncier & Titres",
    "Campagnes & Forages (Drillholes)",
    "Analyse des Risques ESG & Pentes",
])

with tabs[0]:
    run_legacy_page("05_Cadastre_minier.py", "03_Gestion_du_territoire")
    st.markdown("---")
    st.subheader("Sites Miniers Existants")
    run_legacy_page("04_Sites_miniers.py", "03_Gestion_du_territoire")
    st.markdown("---")
    st.subheader("Projets en Développement")
    run_legacy_page("11_Projets_miniers.py", "03_Gestion_du_territoire")

with tabs[1]:
    run_legacy_page("17_Campagne_exploration.py", "03_Gestion_du_territoire")
    st.markdown("---")
    run_legacy_page("18_Cibles.py", "03_Gestion_du_territoire")
    st.markdown("---")
    run_legacy_page("19_Drillholes.py", "03_Gestion_du_territoire")
    with st.expander("Recommandations de Smart Sampling", expanded=False):
        run_legacy_page("23_Smart_Sampling.py", "03_Gestion_du_territoire")
    with st.expander("Historique des Campagnes Antérieures", expanded=False):
        run_legacy_page("24_Historique_campagnes.py", "03_Gestion_du_territoire")

with tabs[2]:
    run_legacy_page("08_Risques_environnement.py", "03_Gestion_du_territoire")
