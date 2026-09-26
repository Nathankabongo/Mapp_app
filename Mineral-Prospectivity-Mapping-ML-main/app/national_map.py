"""Carte nationale RDC — dashboard exécutif."""

from __future__ import annotations

import folium
from folium import plugins
from folium.plugins import MarkerCluster

from compass_core.analysis.atlas_catalog import load_catalog
from compass_core.analysis.mineral_layers import STATUS_LABELS, load_cadastre
from compass_core.io.data_sources import TILE_SOURCES


def build_national_dashboard_map(
    *,
    layers: dict,
    show_layers: list[str],
    show_cadastre: bool = False,
    show_hotspots: bool = False,
    hotspots: list | None = None,
    exploration_targets: list[dict] | None = None,
    drillhole_collars: list[dict] | None = None,
    center: tuple[float, float] = (-4.0375, 21.7587),
    zoom: int = 5,
    highlight: tuple[float, float] | None = None,
    highlight_popup: str | None = None,
    basemap: str = "esri_satellite",
    extent_overlays: list[dict] | None = None,
    image_overlays: list[dict] | None = None,
) -> folium.Map:
    """Carte RDC avec fond satellite ESRI, gisements, cadastre et point GPS."""
    tile = TILE_SOURCES.get(basemap, TILE_SOURCES["osm"])
    m = folium.Map(location=list(center), zoom_start=zoom, tiles=None, control_scale=True)
    folium.TileLayer(
        tiles=tile.url,
        attr=tile.attribution,
        name=tile.label,
        overlay=False,
        control=True,
    ).add_to(m)
    folium.TileLayer(
        tiles=TILE_SOURCES["osm"].url,
        attr=TILE_SOURCES["osm"].attribution,
        name="OpenStreetMap",
        overlay=False,
        control=True,
    ).add_to(m)
    if "opentopo" in TILE_SOURCES:
        topo = TILE_SOURCES["opentopo"]
        folium.TileLayer(
            tiles=topo.url,
            attr=topo.attribution,
            name=topo.label,
            overlay=False,
            control=True,
        ).add_to(m)

    catalog = load_catalog()

    for code in show_layers:
        gdf = layers.get(code)
        meta = catalog.layers.get(code)
        if gdf is None or gdf.empty or meta is None:
            continue

        fg = folium.FeatureGroup(name=meta.label, show=True)
        wgs = gdf.to_crs(epsg=4326)
        cluster = MarkerCluster(name=meta.label)

        for _, row in wgs.iterrows():
            if row.geometry is None or row.geometry.is_empty:
                continue
            name = row.get("name", meta.label)
            status = STATUS_LABELS.get(str(row.get("status", "")), row.get("status", "—"))
            popup = (
                f"<b>{name}</b><br><span style='color:{meta.color}'>● {meta.label}</span><br>"
                f"Province : {row.get('province', '—')}<br>Statut : {status}"
            )
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=7 if row.get("Value", 1) == 1 else 4,
                color=meta.color,
                fill=True,
                fill_color=meta.color,
                fill_opacity=0.8,
                popup=folium.Popup(popup, max_width=300),
                tooltip=name,
            ).add_to(cluster)
        cluster.add_to(fg)
        fg.add_to(m)

    if show_cadastre:
        cadastre = load_cadastre()
        if cadastre is not None and not cadastre.empty:
            fg_cad = folium.FeatureGroup(name="Cadastre CAMI", show=True)
            folium.GeoJson(
                cadastre.to_crs(epsg=4326).__geo_interface__,
                style_function=lambda _x: {
                    "fillColor": "#FBBF24",
                    "color": "#D97706",
                    "weight": 1,
                    "fillOpacity": 0.12,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["numero_permis", "statut", "commodity"],
                    aliases=["Permis", "Statut", "Minerai"],
                ),
            ).add_to(fg_cad)
            fg_cad.add_to(m)

    if show_hotspots and hotspots:
        fg_hot = folium.FeatureGroup(name="Hotspots IA (>85%)", show=True)
        for zone in hotspots:
            folium.GeoJson(
                zone.polygon_wgs84.__geo_interface__,
                style_function=lambda _x: {
                    "fillColor": "#DC2626",
                    "color": "#991B1B",
                    "weight": 2,
                    "fillOpacity": 0.35,
                },
            ).add_to(fg_hot)
        fg_hot.add_to(m)

    if exploration_targets:
        fg_t = folium.FeatureGroup(name="Cibles d'exploration", show=True)
        for t in exploration_targets:
            lat = float(t["latitude"])
            lon = float(t["longitude"])
            score = t.get("prospectivity_score", "—")
            tid = t.get("target_id", "CIBLE")
            color = "#E63946" if float(score or 0) >= 70 else "#C4A35A" if float(score or 0) >= 50 else "#2A9D8F"
            folium.CircleMarker(
                location=[lat, lon],
                radius=9,
                color="#FFFFFF",
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                popup=folium.Popup(
                    f"<b>{tid}</b><br>Prospectivité : {score}/100<br>"
                    f"Confiance : {t.get('confidence_pct', '—')} %<br>"
                    f"Priorité : {t.get('stars', '')} {t.get('priority_label', '')}<br>"
                    f"<i>PRÉDICTION IA — validation terrain requise</i>",
                    max_width=280,
                ),
                tooltip=f"{tid} · {score}",
            ).add_to(fg_t)
            if t.get("polygon_wkt"):
                try:
                    from shapely import wkt as shapely_wkt

                    geom = shapely_wkt.loads(t["polygon_wkt"])
                    folium.GeoJson(
                        geom.__geo_interface__,
                        style_function=lambda _x, c=color: {
                            "fillColor": c,
                            "color": "#FFFFFF",
                            "weight": 2,
                            "fillOpacity": 0.25,
                        },
                    ).add_to(fg_t)
                except Exception:
                    pass
        fg_t.add_to(m)

    if drillhole_collars:
        fg_d = folium.FeatureGroup(name="Forages", show=True)
        for d in drillhole_collars:
            folium.CircleMarker(
                location=[float(d["y"]), float(d["x"])],
                radius=6,
                color="#C4A35A",
                fill=True,
                fill_color="#C4A35A",
                fill_opacity=0.9,
                popup=folium.Popup(
                    f"<b>{d.get('hole_id')}</b><br>Profondeur : {d.get('depth_m')} m<br>"
                    f"Classe : {d.get('data_class', 'imported')}",
                    max_width=220,
                ),
                tooltip=d.get("hole_id", "DH"),
            ).add_to(fg_d)
        fg_d.add_to(m)

    if image_overlays:
        for ov in image_overlays:
            img = ov.get("image")
            bounds = ov.get("bounds")  # [[south, west], [north, east]]
            if not img or not bounds:
                continue
            folium.raster_layers.ImageOverlay(
                image=img,
                bounds=bounds,
                opacity=float(ov.get("opacity", 0.55)),
                name=ov.get("name", "Prospectivité"),
                interactive=False,
                cross_origin=False,
            ).add_to(m)

    if extent_overlays:
        fg_ext = folium.FeatureGroup(name="Emprise modèle", show=True)
        for ext in extent_overlays:
            geom = ext.get("polygon")
            if geom is None:
                continue
            style = {
                "fillColor": ext.get("fill", "#38BDF8"),
                "color": ext.get("color", "#0284C7"),
                "weight": int(ext.get("weight", 2)),
                "fillOpacity": float(ext.get("fill_opacity", 0.08)),
            }
            if ext.get("dash"):
                style["dashArray"] = ext["dash"]
            folium.GeoJson(
                geom.__geo_interface__,
                style_function=lambda _x, s=style: s,
                tooltip=ext.get("label", "Emprise raster"),
            ).add_to(fg_ext)
        fg_ext.add_to(m)

    if highlight:
        lat, lon = highlight
        popup_txt = highlight_popup or "Point évalué"
        folium.Marker(
            [lat, lon],
            icon=folium.Icon(color="red", icon="star"),
            popup=folium.Popup(popup_txt, max_width=320),
            tooltip="Cible GPS",
        ).add_to(m)
        folium.Circle(
            location=[lat, lon],
            radius=800,
            color="#E63946",
            weight=2,
            fill=False,
            popup="Point interrogé",
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    plugins.MiniMap(toggle_display=True).add_to(m)
    plugins.MeasureControl(primary_length_unit="kilometers").add_to(m)
    plugins.Draw(export=True).add_to(m)
    return m
