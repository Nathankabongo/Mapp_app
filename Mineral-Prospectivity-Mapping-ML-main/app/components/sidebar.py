"""Sidebar professionnelle — Style Command Center Palantir (Sans stickers)."""

from __future__ import annotations

import streamlit as st
from app.components.theme import PLATFORM_NAME, PLATFORM_REGION
from compass_core.analysis.national import commodity_filter_options, list_province_options
from compass_core.validation.data_quality import system_health

DEFAULT_FILTERS = {
    "province": "Toute la RDC",
    "territoire": "",
    "minerai": ["Cu-Co", "Lithium", "Or (Au)"],
    "statut": "Tous",
    "project_type": "Tous",
    "favorability_min": 0,
    "risque": "Tous",
    "periode": "Toutes",
}


def render_sidebar(*, active_page: str = "") -> dict:
    """Sidebar de contrôle géospatial : interface épurée sans stickers ni emojis."""
    if "filters" not in st.session_state:
        st.session_state.filters = dict(DEFAULT_FILTERS)
    f = st.session_state.filters

    with st.sidebar:
        st.markdown(
            f"""
            <div class="cmc-side-brand">
                <div class="cmc-brand-glow"></div>
                <div class="cmc-brand-title">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2" style="margin-right: 6px;">
                        <polygon points="12 2 19 21 12 17 5 21 12 2"></polygon>
                    </svg>
                    <span class="cmc-logo-text">CRITICAL MINERALS<br/><strong>COMPASS</strong></span>
                </div>
                <div class="cmc-brand-sub">
                    <span class="badge-tech">DECISION INTELLIGENCE</span>
                    <span class="badge-geo">RDC 2026</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="cmc-nav-cat">PARAMÈTRES DE FILTRAGE TACTIQUE</div>', unsafe_allow_html=True)

        with st.expander("JURIDICTION & TERRITOIRE", expanded=True):
            provinces = list_province_options()
            idx = provinces.index(f["province"]) if f.get("province") in provinces else 0
            f["province"] = st.selectbox("Province administrative", provinces, index=idx, key="sb_province")
            f["territoire"] = st.text_input("Territoire / Secteur", value=f.get("territoire", ""), placeholder="Filtrer territoire (ex: Kolwezi)...", key="sb_terr")

        with st.expander("SUBSTANCES & MÉTAUX CIBLES", expanded=True):
            options = commodity_filter_options()
            defaults = [x for x in f.get("minerai", []) if x in options] or options[:3]
            f["minerai"] = st.multiselect("Minerais sélectionnés", options, default=defaults, key="sb_minerai")

        with st.expander("CONFORMITÉ & FILTRES CADASTRAUX", expanded=False):
            f["statut"] = st.selectbox(
                "Statut du Permis CAMI",
                ["Tous", "exploitation", "recherche", "artisanal", "prospect", "abandonne"],
                key="sb_statut",
            )
            f["risque"] = st.selectbox("Niveau Risque ESG/Pente", ["Tous", "faible", "moyen", "élevé"], key="sb_risque")
            f["favorability_min"] = st.slider(
                "Seuil de Favorabilité IA (%)", 0, 100, int(f.get("favorability_min", 0)), key="sb_fav"
            )

        if st.button("Réinitialiser les filtres", use_container_width=True, key="sb_reset"):
            st.session_state.filters = dict(DEFAULT_FILTERS)
            st.rerun()

        # Bloc santé système
        health = system_health()
        st.markdown(
            f"""
            <div class="cmc-side-health">
                <div class="health-header">
                    <span class="pulse-dot"></span>
                    <span class="health-title">DATA INFRASTRUCTURE</span>
                </div>
                <div class="health-row">
                    <span>Intégrité des données</span>
                    <span class="health-val-ok">{health.get("quality", "OPÉRATIONNELLE")}</span>
                </div>
                <div class="health-row">
                    <span>Synchronisation BNDG</span>
                    <span class="health-val">{health.get("last_sync", "Aujourd'hui")}</span>
                </div>
                <div class="health-row">
                    <span>Connecteurs actifs</span>
                    <span class="health-val">{health.get("active_sources", 0)} / {health.get("registered_sources", 0)}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.session_state.filters = f
    return f
