"""04 — Catalogue des sites miniers."""

from __future__ import annotations

import streamlit as st

from app.components.data_table import render_data_table
from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_demo_notice
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.analytics.mining import sites_table
from compass_core.analysis.site_evaluation import evaluate_site
from compass_core.constants import UNAVAILABLE

filters = bootstrap("Sites miniers", active_page="Sites miniers")
masthead(
    "Catalogue des sites miniers",
    "Base interactive des occurrences et sites répertoriés — atlas Compass, pas un registre CAMI.",
    sources="Atlas local (reference_public · atlas_demo)",
)
render_demo_notice()

province = None if filters["province"] == "Toute la RDC" else filters["province"]
df = sites_table(province)
if filters.get("minerai") and not df.empty:
    df = df[
        df["Minerai"].isin(filters["minerai"])
        | df["Minerai"].str.contains("Cu|Co|Or|Lithium|Diamant|Coltan", case=False, na=False)
    ]
if filters.get("statut") and filters["statut"] != "Tous" and not df.empty:
    df = df[df["status_code"] == filters["statut"]]

render_section("Tableau des sites", "Recherche, filtres globaux, fiche détaillée")
display = df.drop(columns=["code", "status_code"], errors="ignore") if not df.empty else df
view = render_data_table(display, search_placeholder="Rechercher un site, une province…", key="sites_tbl")

if not view.empty:
    names = view["Site"].astype(str).tolist()
    chosen = st.selectbox("Fiche site", names)
    row = view[view["Site"] == chosen].iloc[0]
    left, right = st.columns([0.42, 0.58], gap="medium")
    with left:
        src = str(row.get("Source", ""))
        data_class = "demo" if "demo" in src.lower() else "historical"
        report = evaluate_site(float(row["Latitude"]), float(row["Longitude"]))
        render_detail_panel(
            "Détail du site",
            [
                ("Nom", row["Site"]),
                ("Type", row.get("Type") or UNAVAILABLE),
                ("Province", row["Province"] or UNAVAILABLE),
                ("Territoire", row.get("Territoire") or UNAVAILABLE),
                ("Coordonnées", f"{row['Latitude']}, {row['Longitude']}"),
                ("Minerai", row["Minerai"]),
                ("Statut", row["Statut"]),
                ("Opérateur", UNAVAILABLE),
                (
                    "Favorabilité",
                    f"{report.mineral_prediction} ({report.favorability.score:.0%})"
                    if report.favorability.in_bounds
                    else UNAVAILABLE,
                ),
                ("Risque terrain", report.terrain.risk_level),
                ("Cadastre", report.cadastral_status),
            ],
            data_class=data_class,
            source_block={
                "source": src or UNAVAILABLE,
                "date": UNAVAILABLE,
                "crs": "EPSG:4326",
                "confidence": "Référence publique / démo",
            },
            actions=True,
        )
    with right:
        layers, show_layers, _, _ = load_workspace(filters)
        fmap = build_platform_map(
            layers=layers,
            show_layers=show_layers,
            show_cadastre=True,
            center=(float(row["Latitude"]), float(row["Longitude"])),
            zoom=8,
            highlight=(float(row["Latitude"]), float(row["Longitude"])),
        )
        render_map_panel(fmap, height=460, key="site_fiche_map", legend="Site sélectionné")

close_page()
