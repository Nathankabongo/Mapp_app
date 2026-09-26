"""Carte interactive de l'atlas minier RDC."""

from __future__ import annotations

import folium
from folium import plugins
from folium.plugins import MarkerCluster

from compass_core.analysis.atlas_catalog import load_catalog
from compass_core.analysis.mineral_layers import STATUS_LABELS, load_cadastre


def build_atlas_map(
    *,
    layers: dict,
    show_layers: list[str],
    show_cadastre: bool = False,
    center: tuple[float, float] = (-4.0, 23.5),
    zoom: int = 5,
    highlight: tuple[float, float] | None = None,
) -> folium.Map:
    """
    Carte nationale RDC avec contrôle des couches par minéral.

    Chaque commodité est un FeatureGroup activable dans la légende Folium.
    """
    catalog = load_catalog()
    m = folium.Map(location=list(center), zoom_start=zoom, tiles="OpenStreetMap")

    for code in show_layers:
        gdf = layers.get(code)
        meta = catalog.layers.get(code)
        if gdf is None or gdf.empty or meta is None:
            continue

        fg = folium.FeatureGroup(name=f"{meta.label}", show=True)
        wgs = gdf.to_crs(epsg=4326)
        cluster = MarkerCluster(name=meta.label)

        for _, row in wgs.iterrows():
            if row.geometry is None or row.geometry.is_empty:
                continue
            lat, lon = row.geometry.y, row.geometry.x
            name = row.get("name", meta.label)
            status = STATUS_LABELS.get(str(row.get("status", "")), row.get("status", "—"))
            province = row.get("province", "—")
            formation = row.get("geological_formation", "—")
            popup_html = (
                f"<b>{name}</b><br>"
                f"<span style='color:{meta.color}'>● {meta.label}</span><br>"
                f"Province : {province}<br>"
                f"Statut : {status}<br>"
                f"Formation : {formation}"
            )
            folium.CircleMarker(
                location=[lat, lon],
                radius=6 if row.get("Value", 1) == 1 else 4,
                color=meta.color,
                fill=True,
                fill_color=meta.color,
                fill_opacity=0.75 if row.get("Value", 1) == 1 else 0.35,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=name,
            ).add_to(cluster)

        cluster.add_to(fg)
        fg.add_to(m)

    if show_cadastre:
        cadastre = load_cadastre()
        if cadastre is not None and not cadastre.empty:
            fg_cad = folium.FeatureGroup(name="Cadastre CAMI (permis)", show=False)
            folium.GeoJson(
                cadastre.to_crs(epsg=4326).__geo_interface__,
                style_function=lambda _x: {
                    "fillColor": "#FBBF24",
                    "color": "#D97706",
                    "weight": 1,
                    "fillOpacity": 0.15,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["numero_permis", "statut", "commodity"],
                    aliases=["Permis", "Statut", "Minerai"],
                    localize=True,
                ),
            ).add_to(fg_cad)
            fg_cad.add_to(m)

    if highlight:
        lat, lon = highlight
        folium.Marker(
            [lat, lon],
            icon=folium.Icon(color="red", icon="star"),
            tooltip="Point ciblé",
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    plugins.MiniMap(toggle_display=True).add_to(m)
    return m


def build_legend_html(catalog_layers: list) -> str:
    """HTML de légende pour l'interface Streamlit."""
    items = "".join(
        f"<div style='display:flex;align-items:center;margin:4px 0'>"
        f"<span style='width:14px;height:14px;border-radius:50%;background:{m.color};"
        f"display:inline-block;margin-right:8px'></span>"
        f"<span>{m.label}</span></div>"
        for m in catalog_layers
    )
    return (
        f"<div style='background:#fff;border:1px solid #E4E8EE;border-radius:8px;"
        f"padding:10px 14px;font-size:0.88rem'>"
        f"<b>Légende</b>{items}</div>"
    )
