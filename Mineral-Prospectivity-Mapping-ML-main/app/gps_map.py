"""Carte interactive Folium pour le ciblage GPS."""

from __future__ import annotations

from typing import TYPE_CHECKING

import folium
from folium import plugins

from compass_core.analysis.atlas_catalog import load_catalog

if TYPE_CHECKING:
    from compass_core.analysis.site_evaluation import SiteEvaluationReport


def build_evaluation_map(
    report: SiteEvaluationReport,
    *,
    mineral_layers: dict | None = None,
    show_layers: list[str] | None = None,
) -> folium.Map:
    """Construit une carte centrée sur le point évalué."""
    lat = report.point.latitude
    lon = report.point.longitude
    fav_pct = report.favorability.score

    m = folium.Map(location=[lat, lon], zoom_start=11, tiles="OpenStreetMap")

    # Marqueur principal
    color = "green" if fav_pct >= 0.65 else "orange" if fav_pct >= 0.35 else "red"
    folium.Marker(
        [lat, lon],
        popup=(
            f"<b>{report.sector_name}</b><br>"
            f"Favorabilité : {fav_pct:.0%}<br>"
            f"{report.mineral_prediction}"
        ),
        tooltip="Point ciblé",
        icon=folium.Icon(color=color, icon="map-marker"),
    ).add_to(m)

    # Hotspots
    for zone in report.hotspots:
        folium.GeoJson(
            zone.polygon_wgs84.__geo_interface__,
            style_function=lambda _x, score=zone.score_max: {
                "fillColor": "#DC2626",
                "color": "#991B1B",
                "weight": 2,
                "fillOpacity": 0.35,
            },
            tooltip=f"Hotspot — {score:.0%} (max)",
        ).add_to(m)

    # Gisements connus (couches activables)
    if mineral_layers and show_layers:
        catalog = load_catalog()

        for code in show_layers:
            gdf = mineral_layers.get(code)
            meta = catalog.layers.get(code)
            if gdf is None or gdf.empty or meta is None:
                continue
            wgs = gdf.to_crs(epsg=4326)
            for _, row in wgs.iterrows():
                if row.geometry is None or row.geometry.is_empty:
                    continue
                name = row.get("name", meta.label)
                status = row.get("status", "")
                folium.CircleMarker(
                    location=[row.geometry.y, row.geometry.x],
                    radius=5,
                    color=meta.color,
                    fill=True,
                    fill_opacity=0.75,
                    popup=f"<b>{name}</b><br>{meta.label}<br>Statut: {status}",
                    tooltip=name,
                ).add_to(m)

    # Rayon démographique
    folium.Circle(
        location=[lat, lon],
        radius=report.demographics.radius_km * 1000,
        color="#1B6B4A",
        fill=True,
        fill_opacity=0.08,
        weight=2,
        tooltip=f"Zone démographique {report.demographics.radius_km:.0f} km",
    ).add_to(m)

    plugins.MiniMap(toggle_display=True).add_to(m)
    return m
