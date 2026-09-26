"""Coquille commune : design system + filtres + navigation."""

from __future__ import annotations

from app.components.footer import render_footer
from app.components.header import render_page_header
from app.components.layout import configure_page
from app.components.sidebar import DEFAULT_FILTERS, render_sidebar

# Réexport pour imports historiques
inject_platform_css = None  # remplacé par configure_page


def bootstrap(page_title: str, *, active_page: str | None = None) -> dict:
    configure_page(page_title)
    return render_sidebar(active_page=active_page or page_title)


def masthead(
    title: str,
    subtitle: str,
    *,
    sources: str | None = None,
    updated: str | None = None,
) -> None:
    render_page_header(title, subtitle, sources=sources, updated=updated)


def close_page() -> None:
    render_footer()


def init_filters() -> None:
    import streamlit as st

    if "filters" not in st.session_state:
        st.session_state.filters = dict(DEFAULT_FILTERS)


def render_global_sidebar() -> dict:
    return render_sidebar(active_page="")


def inject_platform_css() -> None:
    from app.components.layout import inject_design_system_css

    inject_design_system_css()
