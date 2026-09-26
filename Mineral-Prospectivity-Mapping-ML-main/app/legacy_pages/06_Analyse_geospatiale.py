"""06 — Analyse géospatiale."""

from __future__ import annotations

import streamlit as st

from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_demo_notice
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.analysis.site_evaluation import evaluate_site
from compass_core.constants import UNAVAILABLE
from compass_core.spatial.buffer import buffer_wgs84_km
from compass_core.spatial.proximity import proximity_summary

filters = bootstrap("Analyse SIG", active_page="Analyse géospatiale")
masthead(
    "Analyse géospatiale",
    "Laboratoire spatial — distances, relief et géologie disponible autour d'une cible.",
    sources="Atlas · MNT pilote · calcul SIG",
)
render_demo_notice("Les distances hydro/routes nationales restent NON DISPONIBLES sans couches vectorielles.")

layers, show_layers, center, zoom = load_workspace(filters)

render_section("Cible d'analyse")
mode = st.radio("Type de cible", ["Point GPS", "Site (saisie)", "Zone (dessin carte)"], horizontal=True)
c1, c2, c3 = st.columns(3)
lat = c1.number_input("Latitude", value=float(center[0]), format="%.4f")
lon = c2.number_input("Longitude", value=float(center[1]), format="%.4f")
radius = c3.slider("Buffer (km)", 1, 50, 10)

if st.button("Calculer", type="primary"):
    report = evaluate_site(lat, lon)
    prox = proximity_summary(lat, lon)
    _ = buffer_wgs84_km(lat, lon, radius)
    render_section("Résultats")
    a, b = st.columns(2)
    with a:
        render_detail_panel(
            "Distances",
            [
                (
                    "Site minier",
                    f"{prox['nearest_site_name']} — {prox['nearest_site_km']} km"
                    if prox["nearest_site_km"] is not None
                    else UNAVAILABLE,
                ),
                (
                    "Concession locale",
                    f"{prox['nearest_permit_id']} — {prox['nearest_permit_km']} km"
                    if prox["nearest_permit_km"] is not None
                    else UNAVAILABLE,
                ),
                (
                    "Rivière (proxy MNT)",
                    f"{report.terrain.water_distance_km:.2f} km"
                    if report.terrain.risk_level != "inconnu"
                    else UNAVAILABLE,
                ),
                ("Route / ville / village", UNAVAILABLE),
            ],
            data_class="computed",
            source_block={"source": "CALCULÉ SIG", "crs": "géodésique / UTM locale", "method": "Haversine / MNT"},
        )
    with b:
        render_detail_panel(
            "Relief & géologie",
            [
                (
                    "Altitude",
                    f"{report.terrain.elevation_m:.0f} m"
                    if report.terrain.risk_level != "inconnu"
                    else UNAVAILABLE,
                ),
                (
                    "Pente",
                    f"{report.terrain.slope_deg:.1f}°"
                    if report.terrain.risk_level != "inconnu"
                    else UNAVAILABLE,
                ),
                ("Orientation", UNAVAILABLE),
                ("Type de relief", report.terrain.soil_type),
                ("Formations", report.terrain.geology),
                ("Failles / anomalies", UNAVAILABLE),
            ],
            data_class="computed",
        )
    st.caption(f"Buffer {radius} km calculé · Mode cible : {mode}")

    from compass_core.environment.assessment import environmental_state
    from compass_core.mining.asm import asm_status
    from compass_core.satellite.change_detection import change_timeline

    env = environmental_state(lat, lon)
    asm = asm_status()
    chg = change_timeline()
    render_section("Environnement · ASM · activité minière")
    e1, e2, e3 = st.columns(3)
    with e1:
        render_detail_panel(
            "État environnemental",
            [
                ("État", env["state"]),
                ("NDVI", env["ndvi"].get("status", UNAVAILABLE) if isinstance(env["ndvi"], dict) else UNAVAILABLE),
                ("Justification", env["justification"][:120] + "…"),
            ],
            data_class=env.get("data_class", "unavailable"),
        )
    with e2:
        render_detail_panel(
            "ASM Detection",
            [("Statut", asm["status"]), ("Message", asm["message"][:120] + "…")],
            data_class=asm.get("data_class", "unavailable"),
        )
    with e3:
        render_detail_panel(
            "Mining Activity Detection",
            [
                ("Statut", chg.get("status", UNAVAILABLE)),
                ("Timeline", " → ".join(str(y) for y in chg.get("years", [])) or UNAVAILABLE),
            ],
            data_class=chg.get("data_class", "unavailable"),
        )

render_section("Carte")
fmap = build_platform_map(
    layers=layers,
    show_layers=show_layers,
    show_cadastre=True,
    center=(lat, lon),
    zoom=max(zoom, 7),
    highlight=(lat, lon),
)
render_map_panel(fmap, height=480, key="sig_lab_map", legend="Outils dessin / mesure Folium")
_ = filters
close_page()
