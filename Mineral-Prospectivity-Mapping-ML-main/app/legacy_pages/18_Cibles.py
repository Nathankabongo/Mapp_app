"""18 — Cibles d'exploration."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.data_table import render_data_table
from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_warning_state
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.exploration.campaign import run_campaign
from compass_core.prospectivity.prediction import ZONE_PRESETS

filters = bootstrap("Cibles", active_page="Cibles")
masthead(
    "Cibles d'exploration",
    "Génération, classement et priorisation — potentiel géologique vs faisabilité.",
    sources="Hotspots prospectivité IA",
)
render_warning_state(
    "Chaque cible est une hypothèse d'exploration (PRÉDICTION IA), pas une découverte confirmée.",
    title="Cibles",
)

camp = st.session_state.get("exploration_campaign")
if camp is None:
    zone = st.selectbox("Zone", list(ZONE_PRESETS.keys()))
    mineral = st.selectbox("Minerai", ["cuivre", "cobalt", "lithium", "or"])
    if st.button("Générer les cibles", type="primary"):
        camp = run_campaign(zone=zone, mineral=mineral).to_dict()
        st.session_state["exploration_campaign"] = camp
else:
    st.caption(f"Campagne active : {camp.get('campaign_id')}")

if not camp:
    close_page()
    st.stop()

targets = camp.get("targets") or []
render_section("TOP cibles")
if not targets:
    st.warning("Aucune cible.")
    close_page()
    st.stop()

for t in targets[:5]:
    with st.container():
        st.markdown(
            f"**{t['target_id']}** — Prospectivité **{t['prospectivity_score']}/100** · "
            f"Confiance **{t['confidence_pct']} %** · {t['stars']} {t['priority_label']} · "
            f"{t['area_km2']} km²"
        )
        c1, c2 = st.columns(2)
        with c1:
            st.write("Facteurs :")
            for f in t.get("factors", [])[:5]:
                st.write(f"✓ {f}")
        with c2:
            st.write("Contraintes / manques :")
            for f in t.get("constraints", [])[:5]:
                st.write(f"⚠ {f}")
        render_detail_panel(
            "Scores dimensionnels",
            [
                ("Potentiel géologique", f"{t['geological_potential']}/100"),
                ("Confiance modèle", f"{t['confidence_pct']}/100"),
                ("Qualité données", f"{t['data_quality']}/100"),
                ("Accessibilité", t["accessibility"] if t.get("accessibility") is not None else "NON DISPONIBLE"),
                ("Contraintes env.", t["env_constraint"] if t.get("env_constraint") is not None else "NON DISPONIBLE"),
                ("Contraintes sociales", t["social_constraint"] if t.get("social_constraint") is not None else "NON DISPONIBLE"),
                ("Priorité exploration", f"{t['exploration_priority_score']}/100"),
            ],
            data_class="prediction",
        )

df = pd.DataFrame(targets)
render_data_table(
    df[["target_id", "prospectivity_score", "confidence_pct", "exploration_priority_score", "priority_label", "area_km2"]],
    height=240,
    key="cibles_table",
)

layers, show_layers, _, _ = load_workspace(filters)
fmap = build_platform_map(
    layers=layers,
    show_layers=show_layers,
    center=(camp["latitude"], camp["longitude"]),
    zoom=9,
    basemap="esri_satellite",
    exploration_targets=targets,
)
render_map_panel(fmap, height=420, key="cibles_map", legend="Cibles priorisées")
_ = filters
close_page()
