"""09 — Démographie & impact social."""

from __future__ import annotations

import streamlit as st

from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.analysis.site_evaluation import evaluate_site
from compass_core.analytics.demographic import social_impact_label
from compass_core.constants import UNAVAILABLE
from compass_core.io.population import worldpop_status

filters = bootstrap("Démographie", active_page="Démographie")
masthead(
    "Démographie & impact social",
    "Population autour d'un projet — estimations, pas un recensement officiel.",
    sources="WorldPop si GeoTIFF · sinon proxy synthétique",
)

pop = worldpop_status()
render_warning_state(pop["note"], title="Population")

render_section("Sélection")
c1, c2 = st.columns(2)
lat = c1.number_input("Latitude", value=-10.716, format="%.4f")
lon = c2.number_input("Longitude", value=25.465, format="%.4f")
choice = st.radio("Rayon", ["1 km", "5 km", "10 km", "20 km", "personnalisé"], index=2, horizontal=True)
radius = float(st.number_input("Rayon (km)", 0.5, 50.0, 12.0)) if choice == "personnalisé" else float(choice.split()[0])

report = evaluate_site(lat, lon, demographics_radius_km=float(radius))
d = report.demographics
data_class = pop.get("data_class", "estimated") if pop.get("status") == "local" else "unavailable"

render_section("Indicateurs")
render_kpi_row(
    [
        {
            "label": "Population estimée",
            "value": f"{d.population_estimate:,}",
            "footnote": f"Rayon {d.radius_km:.0f} km",
            "data_class": data_class,
        },
        {
            "label": "Densité",
            "value": f"{d.density_per_km2:.0f}",
            "footnote": "hab./km²",
            "data_class": data_class,
        },
        {
            "label": "Impact social",
            "value": social_impact_label(d),
            "footnote": d.density_class,
            "data_class": "computed",
        },
    ]
)

render_detail_panel(
    "Contexte social",
    [
        ("Établissements", UNAVAILABLE),
        ("Routes", UNAVAILABLE),
        ("Centres urbains", UNAVAILABLE),
        ("Infrastructures critiques", UNAVAILABLE),
        ("Conseil", d.implantation_advice),
        ("Année / résolution", UNAVAILABLE if pop["status"] != "local" else pop.get("path", "—")),
    ],
    data_class=data_class,
    source_block={
        "source": pop.get("note", UNAVAILABLE),
        "date": UNAVAILABLE,
        "crs": "selon raster",
        "confidence": "Estimation",
    },
)

layers, show_layers, _, _ = load_workspace(filters)
fmap = build_platform_map(
    layers=layers,
    show_layers=show_layers,
    center=(lat, lon),
    zoom=9,
    highlight=(lat, lon),
    basemap="osm",
)
render_map_panel(fmap, height=440, key="demo_map", legend="Site · buffer conceptuel")
close_page()
