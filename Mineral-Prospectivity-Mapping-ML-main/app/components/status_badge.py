"""Badges de statut et de provenance des données."""

from __future__ import annotations

import html

import streamlit as st

from app.components.theme import BADGE_STYLES, COLORS


def status_badge_html(data_class: str) -> str:
    label, color = BADGE_STYLES.get(data_class, BADGE_STYLES["unavailable"])
    return (
        f'<span class="cmc-badge" style="color:{color};border-color:{color};'
        f'background:{color}18">{html.escape(label)}</span>'
    )


def render_status_badge(data_class: str) -> None:
    st.markdown(status_badge_html(data_class), unsafe_allow_html=True)


def render_source_badge(
    *,
    source: str,
    data_class: str = "historical",
    date: str | None = None,
    crs: str | None = None,
    confidence: str | None = None,
) -> None:
    parts = [status_badge_html(data_class)]
    meta = [f"Source : {html.escape(source)}"]
    if date:
        meta.append(f"Date : {html.escape(date)}")
    if crs:
        meta.append(f"CRS : {html.escape(crs)}")
    if confidence:
        meta.append(f"Confiance : {html.escape(confidence)}")
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center;'
        f'margin:0.35rem 0 0.75rem">{"".join(parts)}'
        f'<span style="font-size:0.75rem;color:{COLORS["text_muted"]}">'
        f'{" · ".join(meta)}</span></div>',
        unsafe_allow_html=True,
    )
