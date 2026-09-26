"""23 — Smart Sampling."""

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
from compass_core.exploration.smart_sampling import recommend_samples
from compass_core.prospectivity.prediction import ZONE_PRESETS

filters = bootstrap("Smart Sampling", active_page="Smart Sampling")
masthead(
    "Smart Sampling",
    "Où collecter les prochaines données pour réduire l'incertitude ?",
    sources="Incertitude · forages DEMO · raster prospectivité",
)
render_demo_notice("Les points sont des recommandations — pas des ordres de mission.")
render_warning_state(
    "Proxy « échantillons actuels » = forages DEMO locaux, pas un inventaire géochimique complet.",
    title="Limite",
)

c1, c2, c3 = st.columns(3)
zone = c1.selectbox("Zone", list(ZONE_PRESETS.keys()), index=0)
mineral = c2.selectbox("Minerai", ["cuivre", "cobalt", "lithium", "or"], index=0)
n_pts = c3.slider("Points max", 6, 30, 18)

if st.button("Recommander des points", type="primary"):
    plan = recommend_samples(zone=zone, mineral=mineral, n_points=n_pts)
    st.session_state["sampling_plan"] = plan.to_dict()

plan = st.session_state.get("sampling_plan")
if not plan:
    st.info("Lancer la recommandation.")
    close_page()
    st.stop()

counts = plan.get("priority_counts") or {}
render_kpi_row(
    [
        {
            "label": "Échantillons proxy",
            "value": str(plan.get("current_samples_proxy", 0)),
            "data_class": "demo",
        },
        {
            "label": "Points reco.",
            "value": str(plan.get("recommended_count", 0)),
            "data_class": "prediction",
        },
        {
            "label": "Δ incertitude est.",
            "value": (
                f"-{plan['expected_uncertainty_reduction_pct']:.0f} %"
                if plan.get("expected_uncertainty_reduction_pct") is not None
                else "N/E"
            ),
            "data_class": "computed",
        },
        {
            "label": "P1 / P2 / P3",
            "value": f"{counts.get('P1', 0)}/{counts.get('P2', 0)}/{counts.get('P3', 0)}",
            "data_class": "computed",
        },
    ]
)
st.caption(plan.get("disclaimer", ""))

points = plan.get("points") or []
render_section("Points recommandés")
if not points:
    st.warning("Aucune recommandation — couverture raster insuffisante.")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "ID": p["sample_id"],
                    "Priorité": p["priority"],
                    "Lat": p["latitude"],
                    "Lon": p["longitude"],
                    "Incertitude": p["uncertainty"],
                    "Prospectivité": p.get("prospectivity"),
                    "Objectif": p.get("objective"),
                    "Pourquoi": " · ".join(p.get("justification") or [])[:90],
                }
                for p in points
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    render_section("Carte")
    layers, show_layers, _, _ = load_workspace(filters)
    preset = ZONE_PRESETS[zone]
    fmap = build_platform_map(
        layers=layers,
        show_layers=show_layers,
        center=(preset["lat"], preset["lon"]),
        zoom=9,
        basemap="esri_satellite",
        exploration_targets=[
            {
                "target_id": p["sample_id"],
                "latitude": p["latitude"],
                "longitude": p["longitude"],
                "prospectivity_score": p.get("uncertainty"),
            }
            for p in points
        ],
    )
    render_map_panel(fmap, height=440, key="smp_map", legend="Points Smart Sampling")

close_page()
