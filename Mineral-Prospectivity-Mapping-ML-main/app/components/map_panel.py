"""Panneau carte standard (légende / CRS / sources)."""

from __future__ import annotations

import streamlit as st

from app.map_display import render_folium_map


def render_map_panel(
    folium_map,
    *,
    height: int = 560,
    key: str = "map_panel",
    capture_click: bool = False,
    legend: str | None = None,
    crs: str = "EPSG:4326 (affichage)",
    source: str = "Atlas local · fonds tuiles",
) -> dict | None:
    """Affiche une carte Folium avec bandeau de traçabilité uniforme."""
    event = render_folium_map(
        folium_map,
        height=height,
        key=key,
        capture_click=capture_click,
    )
    legend_txt = legend or "Couches actives selon le gestionnaire de couches"
    st.markdown(
        f'<div class="cmc-trace">Légende : {legend_txt} · CRS : {crs} · Source : {source}</div>',
        unsafe_allow_html=True,
    )
    return event
