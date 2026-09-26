"""Panneau de détail universel (site, permis, zone, projet)."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from app.components.status_badge import status_badge_html
from compass_core.constants import UNAVAILABLE


def render_detail_panel(
    title: str,
    fields: list[tuple[str, Any]],
    *,
    data_class: str = "historical",
    source_block: dict | None = None,
    actions: bool = False,
) -> None:
    """
    Affiche un panneau de fiche standardisé.

    fields: [(label, value), ...]
    source_block: {source, date, crs, confidence}
    """
    rows = []
    for key, val in fields:
        display = UNAVAILABLE if val in (None, "", "—") else str(val)
        rows.append(
            f'<div class="cmc-detail-row">'
            f'<span class="cmc-detail-key">{html.escape(key)}</span>'
            f'<span class="cmc-detail-val">{html.escape(display)}</span>'
            f"</div>"
        )
    source_html = ""
    if source_block:
        method = source_block.get("method")
        method_row = (
            f'<div class="cmc-detail-row"><span class="cmc-detail-key">Méthode</span>'
            f'<span class="cmc-detail-val">{html.escape(str(method))}</span></div>'
            if method
            else ""
        )
        source_html = (
            f'<div style="margin-top:0.85rem">{status_badge_html(data_class)}</div>'
            f'<div class="cmc-detail-row"><span class="cmc-detail-key">Source</span>'
            f'<span class="cmc-detail-val">{html.escape(str(source_block.get("source", UNAVAILABLE)))}</span></div>'
            f'<div class="cmc-detail-row"><span class="cmc-detail-key">Date</span>'
            f'<span class="cmc-detail-val">{html.escape(str(source_block.get("date", UNAVAILABLE)))}</span></div>'
            f'<div class="cmc-detail-row"><span class="cmc-detail-key">CRS</span>'
            f'<span class="cmc-detail-val">{html.escape(str(source_block.get("crs", "EPSG:4326")))}</span></div>'
            f"{method_row}"
            f'<div class="cmc-detail-row"><span class="cmc-detail-key">Confiance</span>'
            f'<span class="cmc-detail-val">{html.escape(str(source_block.get("confidence", UNAVAILABLE)))}</span></div>'
        )
    st.markdown(
        f"""
        <div class="cmc-panel">
            <div class="cmc-panel-title">{html.escape(title)}</div>
            {"".join(rows)}
            {source_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if actions:
        a1, a2, a3 = st.columns(3)
        a1.button("Voir sur la carte", use_container_width=True, key=f"act_map_{title}")
        a2.button("Analyser", use_container_width=True, key=f"act_an_{title}")
        a3.button("Exporter", use_container_width=True, key=f"act_ex_{title}")
