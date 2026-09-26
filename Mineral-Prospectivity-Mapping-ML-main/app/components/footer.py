"""Pied de page et traçabilité."""

from __future__ import annotations

import streamlit as st

from app.components.theme import PLATFORM_NAME


def render_footer() -> None:
    st.markdown(
        f"""
        <div class="cmc-footer">
            <div>
                <strong>{PLATFORM_NAME}</strong>
                · Données · Sources · Méthodologie · CRS · Mise à jour
            </div>
            <div>© {PLATFORM_NAME} — aide à la décision, non une certification géologique</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trace(
    *,
    source: str,
    date: str = "—",
    crs: str = "EPSG:4326",
    resolution: str = "—",
    method: str = "—",
    confidence: str = "—",
) -> None:
    st.markdown(
        f'<div class="cmc-trace">'
        f"Source : {source} · Date : {date} · CRS : {crs} · "
        f"Résolution : {resolution} · Méthode : {method} · Confiance : {confidence}"
        f"</div>",
        unsafe_allow_html=True,
    )
