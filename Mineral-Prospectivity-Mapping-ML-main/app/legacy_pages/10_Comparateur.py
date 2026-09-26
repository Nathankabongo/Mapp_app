"""10 — Comparateur de zones."""

from __future__ import annotations

import streamlit as st

from app.components.charts import radar_table
from app.components.empty_state import render_demo_notice
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from compass_core.analytics.comparison import compare_points

filters = bootstrap("Comparateur", active_page="Comparateur")
masthead(
    "Comparateur de zones",
    "Comparez jusqu'à 5 localisations avec les mêmes règles de vérité des données.",
    sources="Atlas · modèle IA (si emprise) · calculs SIG",
)
render_demo_notice()

render_section("Zones à comparer")
n = st.slider("Nombre de zones", 2, 5, 3)
defaults = [
    ("Manono", -7.283, 27.400, "li"),
    ("Kolwezi", -10.716, 25.465, "cu_co"),
    ("Kivu (Kamituga)", -3.080, 28.170, "au"),
    ("Kibali", 3.120, 29.450, "au"),
    ("Mbuji-Mayi", -6.150, 23.600, "diamond"),
]
points = []
cols = st.columns(n)
for i in range(n):
    with cols[i]:
        name, lat0, lon0, com0 = defaults[i]
        st.markdown(f"**Zone {chr(65 + i)}**")
        name = st.text_input("Nom", name, key=f"n{i}")
        lat = st.number_input("Lat", value=lat0, format="%.4f", key=f"la{i}")
        lon = st.number_input("Lon", value=lon0, format="%.4f", key=f"lo{i}")
        commodity = st.selectbox(
            "Minerai modèle",
            ["cu_co", "li", "au", "coltan", "diamond"],
            index=["cu_co", "li", "au", "coltan", "diamond"].index(com0),
            key=f"c{i}",
        )
        points.append({"name": name, "lat": lat, "lon": lon, "commodity": commodity})

if st.button("Comparer", type="primary"):
    render_section("Tableau comparatif")
    df = compare_points(points)
    radar_table(df)

_ = filters
close_page()
