"""En-tête de page professionnel — Style Command Center / Palantir Foundry."""

from __future__ import annotations

from datetime import datetime, timezone
import streamlit as st
from app.components.theme import PLATFORM_NAME, PLATFORM_REGION


def render_page_header(
    title: str,
    subtitle: str,
    *,
    sources: str | None = None,
    updated: str | None = None,
    context: str | None = None,
) -> None:
    """En-tête haute technologie avec télémétrie et métadonnées précises sans emojis."""
    if updated is None:
        updated = datetime.now(timezone.utc).strftime("%d/%m/%Y · %H:%M UTC")
    src = sources or "SGN-C (BNDG) · CAMI · Sentinel-2 MSI"
    ctx = context or PLATFORM_REGION

    st.markdown(
        f"""
        <div class="cmc-page-header">
            <div class="cmc-header-top">
                <div class="cmc-status-pill">
                    <span class="pulse-radar"></span>
                    <span>SYSTÈME EN LIGNE &bull; SECTEUR MINIER RDC</span>
                </div>
                <div class="cmc-coords-readout">
                    <span>SECTEUR RÉFÉRENCE : 10°43'S 25°28'E [KATANGA COPPERBELT]</span>
                </div>
            </div>
            <div class="cmc-header-main">
                <div>
                    <div class="cmc-page-kicker">{PLATFORM_NAME} &bull; COUCHE DÉCISIONNELLE D'EXPLORATION</div>
                    <h1 class="cmc-page-title">{title}</h1>
                    <p class="cmc-page-subtitle">{subtitle}</p>
                </div>
            </div>
            <div class="cmc-page-meta">
                <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2" style="vertical-align: -1px; margin-right: 4px;"><circle cx="12" cy="12" r="10"></circle><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg><strong>Juridiction</strong> : {ctx}</span>
                <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2" style="vertical-align: -1px; margin-right: 4px;"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg><strong>Flux de Données</strong> : {src}</span>
                <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2" style="vertical-align: -1px; margin-right: 4px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg><strong>Horodatage</strong> : {updated}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
