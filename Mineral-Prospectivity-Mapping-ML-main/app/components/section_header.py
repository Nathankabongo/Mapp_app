"""Titres de section standardisés."""

from __future__ import annotations

import streamlit as st


def render_section(title: str, hint: str | None = None) -> None:
    hint_html = f'<p class="cmc-section-hint">{hint}</p>' if hint else ""
    st.markdown(
        f"""
        <div class="cmc-section">
            <h2 class="cmc-section-title">{title}</h2>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
