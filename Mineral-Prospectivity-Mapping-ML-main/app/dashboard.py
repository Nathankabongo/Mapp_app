"""Composants du dashboard exécutif RDC."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.map_display import render_folium_map
from app.national_map import build_national_dashboard_map
from compass_core.analysis.atlas_catalog import load_catalog
from compass_core.analysis.mineral_layers import generate_atlas_layers, load_all_layers
from compass_core.analysis.national import (
    commodity_filter_options,
    compute_national_kpis,
    filter_layers_by_commodities,
    list_province_options,
    locate_province,
    map_view_for_selection,
    primary_commodity_code,
)
from compass_core.analysis.site_evaluation import evaluate_site, resolve_favorability_path
from compass_core.io.data_sources import list_available_sources


def render_kpi_header(province: str, commodities: list[str]) -> None:
    """Affiche les 4 KPIs nationaux."""
    kpis = compute_national_kpis(province=province, commodity_labels=commodities)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites répertoriés (RDC)", f"{kpis.total_sites:,}")
    c2.metric("Forte favorabilité IA", f"{kpis.high_favorability:,}")
    c3.metric("Concessions actives (CAMI)", f"{kpis.active_permits:,}")
    risk_icon = "[ALERTE]" if kpis.risk_alerts > 5 else "[ATTENTION]" if kpis.risk_alerts else "[NOMINAL]"
    c4.metric("Alertes risque", f"{risk_icon} {kpis.risk_alerts}")


def render_sidebar_filters() -> dict:
    """Panneau latéral de contrôle — retourne l'état des filtres."""
    sb = st.sidebar
    sb.markdown("### Filtres nationaux")
    province = sb.selectbox("Zone / Province", list_province_options(), index=0)
    commodities = sb.multiselect(
        "Substances",
        commodity_filter_options(),
        default=["Cu-Co", "Lithium", "Or (Au)"],
    )
    sb.divider()
    sb.markdown("**GPS — évaluation rapide**")
    lat = sb.number_input("Latitude", value=-4.0375, format="%.4f", key="dash_lat")
    lon = sb.number_input("Longitude", value=21.7587, format="%.4f", key="dash_lon")
    demo_radius = sb.slider("Rayon démographique (km)", 5, 20, 10, key="dash_radius")
    sb.divider()
    sb.markdown("**Couches cartographiques**")
    show_cadastre = sb.checkbox("Cadastre CAMI", value=True)
    show_hotspots = sb.checkbox("Hotspots IA (>85%)", value=False)
    show_population = sb.checkbox("Population (WorldPop)", value=False)
    show_geotech = sb.checkbox("Risques géotechniques", value=True)
    basemap = sb.selectbox(
        "Fond de carte",
        ["esri_satellite", "osm"],
        format_func=lambda x: "Satellite ESRI" if x == "esri_satellite" else "OpenStreetMap",
    )

    if sb.button("Générer atlas national", width="stretch"):
        with st.spinner("Génération…"):
            generate_atlas_layers()
        st.rerun()

    with sb.expander("Sources de données"):
        for row in list_available_sources():
            st.caption(f"**{row['label']}** — {row['status']}")
            st.caption(f"`{row['local']}`")

    return {
        "province": province,
        "commodities": commodities,
        "latitude": lat,
        "longitude": lon,
        "demo_radius": demo_radius,
        "show_cadastre": show_cadastre,
        "show_hotspots": show_hotspots,
        "show_population": show_population,
        "show_geotech": show_geotech,
        "basemap": basemap,
        "evaluate": sb.button("Évaluer le point GPS", type="primary", width="stretch"),
    }


def render_evaluation_panel(report, *, show_geotech: bool = True) -> None:
    """Panneau droit — fiche d'évaluation dynamique."""
    st.markdown("### Fiche d'évaluation")

    st.progress(report.favorability.score, text=f"Favorabilité IA : {report.favorability.score:.0%}")

    if show_geotech:
        g1, g2 = st.columns(2)
        g1.metric("Pente", f"{report.terrain.slope_deg:.1f}°")
        g2.metric("Cours d'eau", f"{report.terrain.water_distance_km * 1000:.0f} m")
        st.caption(f"Couverture données : {report.data_coverage}")

    for label, value in report.to_summary_rows():
        st.markdown(f"**{label}**")
        st.caption(value.replace("**", ""))

    risk = report.terrain.risk_level
    if risk == "élevé":
        st.error(report.terrain.risk_message)
    elif risk == "modéré":
        st.warning(report.terrain.risk_message)
    else:
        st.success(report.terrain.risk_message)

    if report.hotspots:
        st.markdown("**Hotspots détectés**")
        for zone in report.hotspots[:3]:
            st.caption(f"• {zone.score_max:.0%} — {zone.area_km2:.2f} km² — {zone.distance_m / 1000:.1f} km")


def render_executive_dashboard() -> None:
    """Dashboard exécutif principal — carte 65% + fiche 35%."""
    st.markdown(
        """
        <div class="compass-hero">
            <h1>CriticalMineralsCompass — Dashboard RDC</h1>
            <p>Tableau de bord décisionnel national — prospectivité minière, cadastre CAMI, risques & démographie</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filters = render_sidebar_filters()
    render_kpi_header(filters["province"], filters["commodities"])

    province_filter = None if filters["province"] == "Toute la RDC" else filters["province"]
    catalog = load_catalog()
    all_codes = catalog.available_codes()
    layers_raw = load_all_layers(all_codes, province=province_filter)
    layers = filter_layers_by_commodities(layers_raw, filters["commodities"])
    show_layers = list(layers.keys()) or all_codes

    center, zoom = map_view_for_selection(filters["province"])
    if filters["evaluate"]:
        center = (filters["latitude"], filters["longitude"])
        zoom = max(zoom, 9)

    report = None
    if filters["evaluate"]:
        fav_ok = resolve_favorability_path() is not None
        if not fav_ok:
            st.sidebar.warning("Carte IA absente — évaluation partielle.")
        try:
            report = evaluate_site(
                filters["latitude"],
                filters["longitude"],
                commodity=primary_commodity_code(filters["commodities"]),
                demographics_radius_km=float(filters["demo_radius"]),
            )
            st.session_state["dash_report"] = report
        except Exception as exc:
            st.sidebar.error(f"Évaluation : {exc}")
    elif "dash_report" in st.session_state:
        report = st.session_state["dash_report"]

    hotspots = report.hotspots if report and filters["show_hotspots"] else []
    highlight = (report.point.latitude, report.point.longitude) if report else None

    map_col, panel_col = st.columns([0.65, 0.35])

    with map_col:
        st.markdown("#### Carte géospatiale RDC")
        if not layers and not Path("data/rdc/atlas").exists():
            st.info("Générez l'atlas via la barre latérale.")
        try:
            fmap = build_national_dashboard_map(
                layers=layers,
                show_layers=show_layers,
                show_cadastre=filters["show_cadastre"],
                show_hotspots=filters["show_hotspots"],
                hotspots=hotspots,
                center=center,
                zoom=zoom,
                highlight=highlight,
                basemap=filters["basemap"],
            )
            render_folium_map(fmap, height=620, key="national_dashboard_map")
        except Exception as exc:
            st.error(f"Carte : {exc}")
            pts = []
            for gdf in layers.values():
                wgs = gdf.to_crs(epsg=4326)
                for _, row in wgs.iterrows():
                    if row.geometry is not None:
                        pts.append({"lat": row.geometry.y, "lon": row.geometry.x})
            if pts:
                st.map(pts)

    with panel_col:
        if report:
            render_evaluation_panel(report, show_geotech=filters["show_geotech"])
        else:
            st.markdown("### Fiche d'évaluation")
            st.info(
                "Saisissez des coordonnées GPS dans la barre latérale "
                "et cliquez **Évaluer le point GPS** pour afficher le diagnostic 360°."
            )
            prov, basin = locate_province(filters["latitude"], filters["longitude"])
            st.metric("Province détectée", prov)
            st.caption(f"Bassin : {basin}")
            st.metric("Couches actives", len(show_layers))
            st.metric("Gisements affichés", sum(len(g) for g in layers.values()))
