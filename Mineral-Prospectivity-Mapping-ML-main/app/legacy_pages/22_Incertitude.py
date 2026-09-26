"""22 — Incertitude cartographique."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.empty_state import render_demo_notice, render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.exploration.campaign import run_campaign
from compass_core.exploration.uncertainty_map import build_uncertainty_map
from compass_core.prospectivity.prediction import ZONE_PRESETS

filters = bootstrap("Incertitude", active_page="Incertitude")
masthead(
    "Incertitude cartographique",
    "Prospectivité ≠ confiance. Cartographier ce que l'on ne sait pas.",
    sources="Raster prospectivité · occurrences · forages DEMO",
)
render_demo_notice("L'incertitude est dérivée des preuves locales — pas une carte de réserves.")
render_warning_state(
    "Une zone à prospectivité 90 % avec confiance 40 % reste une hypothèse fragile.",
    title="Lecture",
)

c1, c2 = st.columns(2)
zone = c1.selectbox("Zone", list(ZONE_PRESETS.keys()), index=0)
mineral = c2.selectbox("Minerai", ["cuivre", "cobalt", "lithium", "or"], index=0)

if st.button("Calculer la carte d'incertitude", type="primary"):
    camp = run_campaign(zone=zone, mineral=mineral, max_targets=5)
    conf = float((camp.prospectivity or {}).get("model_confidence_pct") or 50)
    report = build_uncertainty_map(
        zone=zone,
        mineral=mineral,
        latitude=camp.latitude,
        longitude=camp.longitude,
        base_confidence=conf,
    )
    st.session_state["uncertainty_report"] = report.to_dict()
    st.session_state["uncertainty_campaign"] = camp.to_dict()

report = st.session_state.get("uncertainty_report")
if not report:
    st.info("Lancer le calcul pour afficher la carte d'incertitude.")
    close_page()
    st.stop()

summary = report.get("summary") or {}
render_kpi_row(
    [
        {"label": "Bien connues", "value": str(summary.get("bien_connue", 0)), "data_class": "computed"},
        {"label": "Transition", "value": str(summary.get("transition", 0)), "data_class": "computed"},
        {"label": "Mal connues", "value": str(summary.get("mal_connue", 0)), "data_class": "prediction"},
        {
            "label": "Incert. moyenne",
            "value": f"{summary.get('mean_uncertainty', 0):.0f}",
            "data_class": "computed",
        },
    ]
)
st.caption(report.get("disclaimer", ""))

render_section("Zones mal connues (priorité acquisition)")
poor = (report.get("zones") or {}).get("poorly_known") or []
if poor:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Lat": p["latitude"],
                    "Lon": p["longitude"],
                    "Incertitude": p["uncertainty"],
                    "Prospectivité": p.get("prospectivity"),
                    "Drivers": " · ".join(p.get("drivers") or [])[:80],
                }
                for p in poor[:15]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.success("Peu de cellules « mal connues » sur l'emprise échantillonnée.")

render_section("Carte contexte")
layers, show_layers, _, _ = load_workspace(filters)
fmap = build_platform_map(
    layers=layers,
    show_layers=show_layers,
    center=(report["latitude"], report["longitude"]),
    zoom=9,
    basemap="esri_satellite",
    exploration_targets=[
        {
            "target_id": f"U{i}",
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "prospectivity_score": c.get("uncertainty"),
        }
        for i, c in enumerate((report.get("zones") or {}).get("poorly_known") or [][:8], start=1)
    ],
)
render_map_panel(
    fmap,
    height=420,
    key="unc_map",
    legend="Marqueurs = cellules à forte incertitude",
    source="Incertitude dérivée",
)

close_page()
