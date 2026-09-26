"""02 — Carte minière nationale."""

from __future__ import annotations

import streamlit as st

from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_demo_notice
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.analysis.national import locate_province
from compass_core.constants import UNAVAILABLE

filters = bootstrap("Carte minière", active_page="Carte minière")
masthead(
    "Carte minière nationale",
    "Visualisation et exploration du potentiel minier de la RDC — "
    "sites, occurrences et couches analytiques.",
    sources="Atlas local · OSM · ESRI · OpenTopoMap",
)
render_demo_notice()

layers, show_layers, center, zoom = load_workspace(filters)

render_section("Filtres cartographiques")
left, main = st.columns([0.26, 0.74], gap="medium")

with left:
    st.markdown('<div class="cmc-panel"><div class="cmc-panel-title">Recherche</div>', unsafe_allow_html=True)
    q_site = st.text_input("Site minier", label_visibility="collapsed", placeholder="Nom du site…")
    lat = st.number_input("Latitude", value=float(center[0]), format="%.4f")
    lon = st.number_input("Longitude", value=float(center[1]), format="%.4f")
    c1, c2, c3 = st.columns(3)
    go = c1.button("Rechercher", use_container_width=True)
    center_btn = c2.button("Centrer", use_container_width=True)
    if c3.button("Reset", use_container_width=True):
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="cmc-panel"><div class="cmc-panel-title">Couches</div>', unsafe_allow_html=True)
    from compass_core.gis.layers import inventory_layers

    layer_specs = inventory_layers()
    by_group: dict[str, list] = {}
    for spec in layer_specs:
        by_group.setdefault(spec.group, []).append(spec)

    show_sites = True
    show_cad = True
    for group, specs in by_group.items():
        st.caption(group)
        for spec in specs:
            enabled = spec.status in {"available", "demo", "remote"}
            default_on = spec.id in {"sites", "concessions", "imagery"}
            val = st.checkbox(
                f"{spec.label} [{spec.status}]",
                value=default_on and enabled,
                disabled=not enabled,
                key=f"ly_{spec.id}",
                help=spec.note or spec.data_class,
            )
            if spec.id == "sites":
                show_sites = val
            if spec.id == "concessions":
                show_cad = val
    basemap = st.selectbox(
        "Fond de carte",
        ["esri_satellite", "osm", "opentopo"],
        format_func=lambda x: {
            "esri_satellite": "Satellite",
            "osm": "OpenStreetMap",
            "opentopo": "Terrain / topo",
        }[x],
    )
    st.markdown("</div>", unsafe_allow_html=True)

if go or center_btn:
    center, zoom = (lat, lon), 9

with main:
    render_section("Carte — République Démocratique du Congo")
    if show_sites or show_cad:
        fmap = build_platform_map(
            layers=layers if show_sites else {},
            show_layers=show_layers,
            show_cadastre=show_cad,
            center=center,
            zoom=zoom,
            highlight=(lat, lon) if go or center_btn else None,
            basemap=basemap,
        )
        event = render_map_panel(
            fmap,
            height=640,
            key="mine_map",
            capture_click=True,
            legend="Sites · cadastre local",
            source="Atlas Compass · tuiles",
        )
        if event and event.get("last_clicked"):
            clat = event["last_clicked"]["lat"]
            clon = event["last_clicked"]["lng"]
            prov, basin = locate_province(clat, clon)
            render_detail_panel(
                "Détail du point sélectionné",
                [
                    ("Nom", "Point carte"),
                    ("Type", "Coordonnée"),
                    ("Province", prov),
                    ("Territoire", UNAVAILABLE),
                    ("Coordonnées", f"{clat:.5f}, {clon:.5f}"),
                    ("Bassin", basin),
                    ("Minerai", UNAVAILABLE),
                    ("Statut", UNAVAILABLE),
                ],
                data_class="computed",
                source_block={
                    "source": "Clic utilisateur",
                    "date": "—",
                    "crs": "EPSG:4326",
                    "confidence": "Position utilisateur",
                },
            )
    else:
        from app.components.empty_state import render_empty_state

        render_empty_state(
            "Aucune couche active",
            "Activez au moins une couche minière pour afficher la carte.",
            status="FILTRE",
        )

_ = q_site
close_page()
