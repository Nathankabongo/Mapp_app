"""Affichage fiable des cartes Folium dans Streamlit."""

from __future__ import annotations

import streamlit as st


def render_folium_map(
    folium_map,
    *,
    height: int = 560,
    key: str | None = None,
    capture_click: bool = False,
) -> dict | None:
    """
    Affiche une carte Folium dans Streamlit.

    Utilise streamlit-folium si disponible (recommandé), sinon iframe HTML.
    """
    try:
        from streamlit_folium import st_folium

        returned = ["last_clicked"] if capture_click else []
        event = st_folium(
            folium_map,
            width=None,
            height=height,
            returned_objects=returned,
            key=key,
        )
        return event if capture_click else None
    except ImportError:
        pass

    try:
        import streamlit.components.v1 as components

        root = folium_map.get_root()
        root.render()
        html = root._repr_html_()
        components.html(
            f'<div style="width:100%">{html}</div>',
            height=height,
            scrolling=True,
        )
    except Exception as exc:
        st.error(f"Impossible d'afficher la carte Folium : {exc}")
        _render_fallback_map(folium_map)
    return None


def _render_fallback_map(folium_map) -> None:
    """Fallback avec st.map si Folium échoue."""
    points: list[dict[str, float]] = []
    for child in folium_map._children.values():
        loc = getattr(child, "location", None)
        if loc and len(loc) == 2:
            points.append({"lat": loc[0], "lon": loc[1]})
    if points:
        st.map(points)
    else:
        st.info("Carte non disponible — installez : `pip install streamlit-folium folium`")
