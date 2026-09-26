"""01 — Tableau de bord national."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.components.charts import bar_pairs
from app.components.empty_state import render_demo_notice
from app.components.kpi_card import render_national_kpis
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.analysis.mineral_layers import generate_atlas_layers
from compass_core.analytics.mining import top_commodities, top_provinces
from compass_core.validation.data_quality import system_health


def render_home() -> None:
    filters = bootstrap("Dashboard", active_page="Dashboard")
    masthead(
        "Dashboard national d'intelligence minière",
        "Vue exécutive de l'activité minière et géospatiale sur le territoire de la "
        "République Démocratique du Congo.",
        sources="Atlas local · fonds tuiles · modèle IA (emprise pilote)",
    )
    render_demo_notice()

    render_section("Indicateurs principaux", "Agrégats de l'atlas local — non officiels CAMI")
    render_national_kpis(filters["province"], filters.get("minerai") or [])

    layers, show_layers, center, zoom = load_workspace(filters)
    health = system_health()

    render_section("Carte nationale", "République Démocratique du Congo")
    map_col, panel_col = st.columns([0.72, 0.28], gap="medium")

    with map_col:
        if not layers and not Path("data/rdc/atlas").exists():
            from app.components.empty_state import render_empty_state

            render_empty_state(
                "Atlas local absent",
                "Générez l'atlas de démonstration ou importez un GeoPackage vérifiable.",
                expected_source="data/rdc/atlas",
                status="ABSENT",
            )
            if st.button("Générer l'atlas de démonstration", type="primary"):
                generate_atlas_layers()
                st.rerun()
        else:
            fmap = build_platform_map(
                layers=layers,
                show_layers=show_layers,
                show_cadastre=True,
                show_hotspots=False,
                center=center,
                zoom=zoom,
                basemap="esri_satellite",
            )
            render_map_panel(
                fmap,
                height=620,
                key="dash_map",
                legend="Sites atlas · cadastre local (DEMO)",
                source="Atlas Compass · ESRI / OSM",
            )

    with panel_col:
        render_section("Vue analytique")
        bar_pairs(top_commodities(), "Top minerais (atlas)")
        bar_pairs(top_provinces(), "Top provinces (atlas)")
        st.markdown('<div class="cmc-panel">', unsafe_allow_html=True)
        st.markdown("**État du système**")
        st.caption(f"Sync : {health['last_sync']}")
        st.caption(f"Sources locales : {health['active_sources']}/{health['registered_sources']}")
        st.caption(f"Qualité : {health['quality']}")
        if health["missing"]:
            st.caption("Manquant : " + ", ".join(health["missing"][:4]))
        st.caption(health["offline_note"])
        st.markdown("</div>", unsafe_allow_html=True)

    close_page()


if __name__ == "__main__":
    render_home()
