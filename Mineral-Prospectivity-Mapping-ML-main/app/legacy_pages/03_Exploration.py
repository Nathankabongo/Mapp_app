"""03 — Exploration / recherche GPS."""

from __future__ import annotations

import streamlit as st

from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_demo_notice, render_warning_state
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.analysis.national import locate_province
from compass_core.analysis.site_evaluation import evaluate_site, resolve_favorability_path
from compass_core.constants import UNAVAILABLE
from compass_core.io.geological import load_faults, load_geology
from compass_core.models.prospectivity import classify_score
from compass_core.models.risk import score_risk
from compass_core.spatial.proximity import proximity_summary

filters = bootstrap("Exploration GPS", active_page="Exploration GPS")
masthead(
    "Exploration GPS",
    "Diagnostic spatial d'une position — localisation, mines, relief, cadastre, IA et risques.",
    sources="Atlas · MNT pilote · modèle IA (si emprise)",
)
render_demo_notice(
    "Les estimations hors emprise Kolwezi restent partielles. "
    "L'IA n'est jamais une découverte géologique."
)

layers, show_layers, center, zoom = load_workspace(filters)

render_section("Sélection de position")
col_a, col_b = st.columns([0.32, 0.68], gap="medium")
with col_a:
    lat = st.number_input("Latitude", value=-10.716, format="%.4f")
    lon = st.number_input("Longitude", value=25.472, format="%.4f")
    radius = st.select_slider("Rayon population (km)", options=[1, 5, 10, 20], value=10)
    analyze = st.button("Analyser cette position", type="primary", use_container_width=True)
    use_click = st.checkbox("Utiliser le clic carte", value=False)
    st.caption("Ou cliquez directement sur la carte.")

with col_b:
    fmap = build_platform_map(
        layers=layers,
        show_layers=show_layers,
        show_cadastre=True,
        center=center,
        zoom=zoom,
        highlight=(lat, lon),
        basemap="osm",
    )
    event = render_map_panel(
        fmap,
        height=480,
        key="expl_map",
        capture_click=True,
        legend="Cible GPS · sites atlas",
    )

click_lat, click_lon = lat, lon
if event and event.get("last_clicked"):
    click_lat = event["last_clicked"]["lat"]
    click_lon = event["last_clicked"]["lng"]

if analyze:
    use_lat, use_lon = (click_lat, click_lon) if use_click and event and event.get("last_clicked") else (lat, lon)
    prov, basin = locate_province(use_lat, use_lon)
    report = evaluate_site(use_lat, use_lon, demographics_radius_km=float(radius))
    prox = proximity_summary(use_lat, use_lon)
    fav = classify_score(report.favorability.score, in_bounds=report.favorability.in_bounds)
    risk = score_risk(
        slope_deg=None if report.terrain.risk_level == "inconnu" else report.terrain.slope_deg,
        water_distance_km=report.terrain.water_distance_km,
        density_per_km2=report.demographics.density_per_km2,
    )
    if resolve_favorability_path() is None:
        render_warning_state("Raster IA absent — évaluation partielle.", title="Modèle IA")

    render_section("Résultats du diagnostic")
    d1, d2 = st.columns(2, gap="medium")
    with d1:
        render_detail_panel(
            "Localisation",
            [
                ("Province", prov),
                ("Territoire", UNAVAILABLE),
                ("Ville", UNAVAILABLE),
                ("Zone / bassin", basin),
                ("Coordonnées", f"{use_lat:.5f}, {use_lon:.5f}"),
            ],
            data_class="computed",
            source_block={"source": "regions.json (bbox)", "crs": "EPSG:4326", "confidence": "Indicative"},
        )
        site_line = (
            f"{prox['nearest_site_name']} ({prox['nearest_site_km']:.1f} km)"
            if prox["nearest_site_km"] is not None
            else UNAVAILABLE
        )
        render_detail_panel(
            "Mines",
            [
                ("Site le plus proche", site_line),
                ("Minerai (atlas)", prox["nearest_site_commodity"]),
                ("Cadastre", report.cadastral_status),
            ],
            data_class="historical",
            source_block={"source": "Atlas Compass", "confidence": "Variable"},
        )
    with d2:
        fav_txt = (
            f"{fav['level']} ({fav['score_pct']} %)"
            if fav["score_pct"] is not None
            else "Score non évalué — données hors emprise."
        )
        render_detail_panel(
            "Relief · environnement · IA · risque",
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
                (
                    "Rivière (proxy MNT)",
                    f"{report.terrain.water_distance_km:.2f} km"
                    if report.terrain.risk_level != "inconnu"
                    else UNAVAILABLE,
                ),
                ("Géologie fichier", "couche locale" if load_geology() is not None else UNAVAILABLE),
                ("Failles", "couche locale" if load_faults() is not None else UNAVAILABLE),
                ("Population (buffer)", f"~{report.demographics.population_estimate:,} hab."),
                ("Favorabilité IA", fav_txt),
                ("Risque global", f"{risk.global_score}/100 — {risk.global_label}"),
            ],
            data_class="modeled",
            source_block={
                "source": "MNT pilote / modèle / règles config",
                "method": "CALCULÉ SIG + MODÈLE IA",
                "confidence": "Indicative",
            },
        )
    st.caption(str(fav["disclaimer"]))
    st.caption(risk.disclaimer)

_ = filters
close_page()
