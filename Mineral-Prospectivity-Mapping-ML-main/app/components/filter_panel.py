"""Panneau de filtres locaux (barre horizontale de page)."""

from __future__ import annotations

import streamlit as st


def render_filter_bar(title: str = "Filtres et contrôles") -> None:
    from app.components.section_header import render_section

    render_section(title)
