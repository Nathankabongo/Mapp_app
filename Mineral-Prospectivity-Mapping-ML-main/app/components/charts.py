"""Visualisations analytiques — Style Command Center Palantir."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from app.components.theme import COLORS


def bar_pairs(
    pairs: list[tuple[str, int]],
    title: str,
    color: str = COLORS["accent"],
    orientation: str = "horizontal",
) -> None:
    """Graphique en barres haute technologie avec palette néon et infobulles soignées."""
    if not pairs:
        st.markdown(
            f"<div style='font-size:0.75rem; color:{COLORS['text_muted']}; padding: 0.5rem 0;'>Aucune donnée disponible pour le filtre actif.</div>",
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(pairs, columns=["label", "valeur"])

    if orientation == "horizontal":
        chart = (
            alt.Chart(df)
            .mark_bar(cornerRadiusEnd=4, height=18)
            .encode(
                x=alt.X("valeur:Q", title=None, axis=alt.Axis(labels=True, grid=True, gridColor="rgba(255,255,255,0.06)", tickColor="rgba(255,255,255,0.1)", labelColor="#94A3B8")),
                y=alt.Y("label:N", title=None, sort="-x", axis=alt.Axis(labels=True, tickColor="transparent", labelColor="#E2E8F0")),
                color=alt.value(color),
                tooltip=[
                    alt.Tooltip("label:N", title="Entité"),
                    alt.Tooltip("valeur:Q", title="Occurrences / Score"),
                ],
            )
            .properties(height=200)
            .configure_view(strokeWidth=0)
        )
    else:
        chart = (
            alt.Chart(df)
            .mark_bar(cornerRadiusTop=4, width=22)
            .encode(
                x=alt.X("label:N", title=None, axis=alt.Axis(labels=True, labelAngle=-30, labelColor="#E2E8F0")),
                y=alt.Y("valeur:Q", title=None, axis=alt.Axis(grid=True, gridColor="rgba(255,255,255,0.06)", labelColor="#94A3B8")),
                color=alt.value(color),
                tooltip=[
                    alt.Tooltip("label:N", title="Entité"),
                    alt.Tooltip("valeur:Q", title="Volume"),
                ],
            )
            .properties(height=200)
            .configure_view(strokeWidth=0)
        )

    st.altair_chart(chart, use_container_width=True)


def radar_table(df: pd.DataFrame) -> None:
    """Tableau interactif compact et sombre pour l'analyse multicritère."""
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )
