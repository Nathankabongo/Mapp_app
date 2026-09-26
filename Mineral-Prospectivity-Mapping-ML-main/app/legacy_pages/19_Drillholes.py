"""19 — Drillholes : gestion et visualisation des forages."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.data_table import render_data_table
from app.components.empty_state import render_demo_notice, render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.drillholes.store import drillhole_count, load_demo_drillholes
from compass_core.drillholes.visualization import mineralized_segments

filters = bootstrap("Forages", active_page="Forages")
masthead(
    "Drillholes",
    "Import Collar / Survey / Lithology / Assay — trajectoires et intersections.",
    sources="data/rdc/demo/drillholes ou import CSV",
)
render_demo_notice("Les forages DEMO-* sont pédagogiques — aucune teneur inventée.")
render_warning_state(
    "Teneur mesurée ≠ interpolation ≠ prédiction IA. Sans analyse labo : assay = NON DISPONIBLE.",
    title="Assays",
)

info = drillhole_count()
holes = load_demo_drillholes()
render_kpi_row(
    [
        {"label": "Forages", "value": str(info["count"]), "footnote": info["status"], "data_class": info["data_class"]},
        {"label": "Source", "value": "DEMO" if holes else "—", "data_class": "demo" if holes else "unavailable"},
    ]
)

render_section("Import")
st.caption("Formats prévus : CSV (implémenté), Excel / GeoPackage / JSON (connecteurs à venir).")
up = st.file_uploader("Collar CSV (hole_id,x,y,z,depth_m,…)", type=["csv"])
if up is not None:
    st.info("Import sessionnel : placez le fichier sous data/rdc/demo/drillholes/collars.csv pour persistance.")
    st.dataframe(pd.read_csv(up))

if not holes:
    st.warning(info["message"])
    close_page()
    st.stop()

render_section("Collars")
collar_rows = [h.collar.to_dict() for h in holes]
render_data_table(pd.DataFrame(collar_rows), height=200, key="collars_tbl")

render_section("Carte des collars")
layers, show_layers, _, _ = load_workspace(filters)
fmap = build_platform_map(
    layers=layers,
    show_layers=show_layers,
    center=(collar_rows[0]["y"], collar_rows[0]["x"]),
    zoom=10,
    basemap="esri_satellite",
    drillhole_collars=collar_rows,
)
render_map_panel(fmap, height=400, key="dh_map", legend="Collars DEMO")

render_section("Logs & intersections")
hole_ids = [h.hole_id for h in holes]
sel = st.selectbox("Forage", hole_ids)
hole = next(h for h in holes if h.hole_id == sel)
iv_df = pd.DataFrame([i.to_dict() for i in hole.intervals])
if not iv_df.empty:
    render_data_table(iv_df, height=260, key="log_tbl")
segs = mineralized_segments(hole)
if segs:
    st.markdown("**Intersections minéralisées (lithologie / indice — sans teneur inventée)**")
    for s in segs:
        st.write(
            f"{s['hole_id']} · {s['from_m']:.0f}–{s['to_m']:.0f} m · "
            f"Intersection : {s['length_m']:.0f} m · {s['mineralization'] or s['lithology']} · "
            f"Assay : {s['assay_data_class']}"
        )
else:
    st.caption("Aucune intervalle minéralisée renseignée pour ce forage.")

render_section("Intelligence — lien Cible → Forage")
from compass_core.drillholes.intelligence import enrich_hole, link_targets_to_drillholes
from compass_core.exploration.campaign import run_campaign

if st.button("Relier aux cibles Kolwezi Cu"):
    camp = run_campaign(zone="Kolwezi", mineral="cuivre", max_targets=8)
    tree = link_targets_to_drillholes(camp.targets, radius_km=20.0)
    st.session_state["dh_tree"] = tree

tree = st.session_state.get("dh_tree")
if tree:
    st.caption(tree.get("disclaimer", ""))
    for tid, node in (tree.get("targets") or {}).items():
        st.markdown(f"**{node.get('mark', '·')} {node.get('chain', tid)}**")

with st.expander(f"Fiche enrichie {hole.hole_id}"):
    st.json(enrich_hole(hole))

_ = filters
close_page()
