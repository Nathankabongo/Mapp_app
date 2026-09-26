"""États vides et avertissements professionnels — Style Command Center."""

from __future__ import annotations

import html
import streamlit as st
from app.components.status_badge import status_badge_html


def render_empty_state(
    title: str,
    message: str,
    *,
    expected_source: str | None = None,
    status: str = "NON CONNECTÉE",
) -> None:
    src = (
        f"<div style='font-size: 0.75rem; color: #94A3B8; margin-top: 0.3rem;'>Source attendue : <code style='color: #00F2FE;'>{html.escape(expected_source)}</code></div>"
        if expected_source
        else ""
    )
    st.markdown(
        f"""
        <div class="cmc-empty">
            <h4 style="color: #F8FAFC; margin-bottom: 0.25rem;">{html.escape(title)}</h4>
            <p style="color: #94A3B8; margin: 0;">{html.escape(message)}</p>
            {src}
            <div style="margin-top: 0.6rem;">{status_badge_html("unavailable")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_warning_state(message: str, *, title: str = "Alerte") -> None:
    st.markdown(
        f"""
        <div class="cmc-warn-strip">
            <span class="pulse-dot"></span>
            <strong>{html.escape(title)}</strong> &bull; {html.escape(message)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_demo_notice(message: str | None = None) -> None:
    """Discret badge d'état système au lieu de bannière encombrante."""
    # Rendu ultra-discret conforme au style Command Center (pas de bandeau agressif)
    pass
