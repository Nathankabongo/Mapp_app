"""11 — Projets miniers."""

from __future__ import annotations

import streamlit as st

from app.components.data_table import render_data_table
from app.components.empty_state import render_demo_notice, render_empty_state
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from compass_core.analytics.mining import sites_table
from compass_core.constants import UNAVAILABLE

filters = bootstrap("Projets", active_page="Projets")
masthead(
    "Projets miniers",
    "Suivi des phases documentées — Exploration à Fermé. Aucun statut inventé.",
    sources="Atlas local (statut) · opérateurs non disponibles",
)
render_demo_notice(
    "Les phases sont dérivées du statut atlas lorsqu'il est renseigné. "
    "Sinon : Statut non disponible."
)

PHASES = {
    "prospect": "Exploration",
    "recherche": "Étude",
    "exploitation": "Production",
    "artisanal": "Production (artisanale)",
    "abandonne": "Fermé / Suspendu",
}

render_section("Base projets")
df = sites_table(None if filters["province"] == "Toute la RDC" else filters["province"])
if df.empty:
    render_empty_state(
        "Aucun projet",
        "Information non disponible dans les sources utilisées.",
        status="VIDE",
    )
else:
    df = df.copy()
    df["Phase"] = df["status_code"].map(PHASES)
    df["Phase"] = df["Phase"].fillna("Statut non disponible.")
    df["Opérateur"] = UNAVAILABLE
    df["Ressources"] = UNAVAILABLE
    df["Superficie"] = UNAVAILABLE
    df["Date de mise à jour"] = UNAVAILABLE
    show = df[
        ["Site", "Province", "Minerai", "Phase", "Statut", "Opérateur", "Latitude", "Longitude", "Source"]
    ]
    render_data_table(show, search_placeholder="Projet, province, minerai…", key="proj_tbl")

    render_section("Répartition des phases (atlas)")
    counts = (
        df["Phase"]
        .value_counts()
        .reindex(
            [
                "Exploration",
                "Étude",
                "Développement",
                "Construction",
                "Production",
                "Production (artisanale)",
                "Fermé / Suspendu",
                "Statut non disponible.",
            ]
        )
        .fillna(0)
    )
    st.bar_chart(counts)
    st.caption("Développement / Construction : non renseignés dans l'atlas actuel.")

close_page()
