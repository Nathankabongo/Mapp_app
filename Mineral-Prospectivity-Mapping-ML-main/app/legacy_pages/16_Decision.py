"""16 — Exploration Decision : quelle cible explorer en premier ?"""

from __future__ import annotations

import streamlit as st

from app.components.empty_state import render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.components.status_badge import status_badge_html
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.constants import EXPLORATION_TRUTH_CHAIN
from compass_core.drilling.next_best_drillhole import next_best_drillhole
from compass_core.exploration.campaign import run_campaign
from compass_core.modelling.uncertainty import scenario_frame
from compass_core.prospectivity.prediction import ZONE_PRESETS

filters = bootstrap("Décision exploration", active_page="Décision")
masthead(
    "Exploration Decision",
    "Quelle cible faut-il explorer en premier ? — potentiel × confiance × contraintes.",
    sources="Campagne exploration · Next Best Drillhole",
)
render_warning_state(
    "Proposition d'exploration à valider par un géologue. Potentiel élevé ≠ gisement confirmé.",
    title="Aide à la décision",
)

c1, c2 = st.columns(2)
zone = c1.selectbox("Zone", list(ZONE_PRESETS.keys()), index=0)
mineral = c2.selectbox("Minerai", ["cuivre", "cobalt", "lithium", "or", "coltan"])

if st.button("Produire le classement", type="primary"):
    st.session_state["exploration_campaign"] = run_campaign(zone=zone, mineral=mineral).to_dict()

camp = st.session_state.get("exploration_campaign")
if not camp:
    st.info("Lancer le classement ici, ou d'abord la page Exploration.")
    close_page()
    st.stop()

targets = camp.get("targets") or []
prosp = camp["prospectivity"]

render_section("TOP 5 TARGETS")
if not targets:
    st.warning("Aucune cible — minerai hors emprise ou raster absent.")
else:
    for i, t in enumerate(targets[:5], start=1):
        st.markdown(
            f"**{i}. {t['target_id']}** — {t['prospectivity_score']}/100 · "
            f"confiance {t['confidence_pct']} % · priorité {t['exploration_priority_score']} · "
            f"{t['stars']} {t['priority_label']}"
        )
        with st.expander(f"Pourquoi {t['target_id']} ?"):
            for f in t.get("factors", []):
                st.write(f"→ {f}")
            for c_ in t.get("constraints", [])[:4]:
                st.write(f"⚠ {c_}")
            scen = scenario_frame(
                potential_label=t["priority_label"],
                confidence_pct=float(t["confidence_pct"]),
            )
            st.caption(scen["rule"])

render_section("Next Best Drillhole")
nbd = next_best_drillhole(targets=targets, existing_holes=0)
render_kpi_row(
    [
        {"label": "Cible NBD", "value": str(nbd.get("target_id", "—")), "data_class": "prediction"},
        {"label": "VOI", "value": str(nbd.get("voi_score", "—")), "data_class": "computed"},
        {
            "label": "Prospectivité zone",
            "value": f"{prosp['prospectivity_pct']:.0f} %"
            if prosp.get("prospectivity_pct") is not None
            else "N/E",
            "data_class": "prediction",
        },
        {"label": "CAMI", "value": "0", "footnote": "vérifié", "data_class": "unavailable"},
    ]
)
st.caption(nbd.get("disclaimer", ""))

render_section("Carte décisionnelle")
layers, show_layers, _, _ = load_workspace(filters)
fmap = build_platform_map(
    layers=layers,
    show_layers=show_layers,
    center=(camp["latitude"], camp["longitude"]),
    zoom=9,
    basemap="esri_satellite",
    exploration_targets=targets[:5],
    highlight=(camp["latitude"], camp["longitude"]),
)
render_map_panel(fmap, height=420, key="decision_exp_map", legend="Top cibles")

render_section("Chaîne de vérité")
st.markdown(
    " → ".join(status_badge_html(k) for k, _ in EXPLORATION_TRUTH_CHAIN),
    unsafe_allow_html=True,
)
st.caption("Étape modèle : " + prosp.get("evidence_stage", "—"))
st.caption(camp.get("disclaimer", ""))
_ = filters
close_page()
