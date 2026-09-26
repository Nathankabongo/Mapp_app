"""Tableaux professionnels standardisés."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.empty_state import render_empty_state


def render_data_table(
    df: pd.DataFrame,
    *,
    search_placeholder: str = "Rechercher…",
    height: int = 420,
    key: str = "data_table",
) -> pd.DataFrame:
    """Affiche un tableau avec recherche. Retourne le DataFrame filtré."""
    if df is None or df.empty:
        render_empty_state(
            "Aucune donnée à afficher",
            "Aucun enregistrement ne correspond aux filtres ou à la source connectée.",
            status="VIDE",
        )
        return df if df is not None else pd.DataFrame()

    q = st.text_input(
        "Recherche",
        "",
        placeholder=search_placeholder,
        key=f"{key}_search",
        label_visibility="collapsed",
    )
    view = df
    if q.strip():
        mask = pd.Series(False, index=df.index)
        for col in df.columns:
            mask = mask | df[col].astype(str).str.contains(q.strip(), case=False, na=False)
        view = df[mask]

    st.caption(f"{len(view):,} ligne(s) · {len(df.columns)} colonnes")
    st.dataframe(view, use_container_width=True, hide_index=True, height=height)
    return view
