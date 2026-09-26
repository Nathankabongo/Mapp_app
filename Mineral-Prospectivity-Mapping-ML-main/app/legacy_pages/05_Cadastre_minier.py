"""05 — Cadastre minier."""

from __future__ import annotations

import streamlit as st

from app.components.data_table import render_data_table
from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_empty_state, render_warning_state
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.analysis.mineral_layers import load_cadastre
from compass_core.constants import UNAVAILABLE

filters = bootstrap("Cadastre", active_page="Cadastre")
masthead(
    "Cadastre minier",
    "Permis et concessions — uniquement d'après une couche locale vérifiable. "
    "Trois états : officiellement vérifié · non vérifié · non disponible.",
    sources="CAMI (si export) · sinon couche locale DEMO",
)

render_warning_state(
    "Ne jamais traiter cette page comme le cadastre officiel du CAMI "
    "sauf si un export CAMI daté a été importé. "
    "Source officielle à vérifier : https://cami.cd/",
    title="Cadastre",
)

cadastre = load_cadastre()
layers, show_layers, center, zoom = load_workspace(filters)

render_section("Couche cadastrale")
if cadastre is None or cadastre.empty:
    render_empty_state(
        "Données cadastrales indisponibles",
        "Information non disponible dans les sources utilisées. "
        "Placez un GeoPackage CAMI vérifiable ou générez la couche de démonstration.",
        expected_source="https://cami.cd/ / CAMI",
        status="NON CONNECTÉE",
    )
else:
    wgs = cadastre.to_crs(epsg=4326)
    display = wgs.drop(columns="geometry", errors="ignore").copy()
    # Classification visuelle
    if "source" in display.columns:
        display["Classe"] = display["source"].apply(
            lambda s: "DÉMONSTRATION"
            if "demo" in str(s).lower()
            else ("OFFICIEL" if "cami" in str(s).lower() else "NON VÉRIFIÉ")
        )
    view = render_data_table(display, search_placeholder="N° permis, province…", key="cad_tbl")

    render_section("Carte des polygones")
    fmap = build_platform_map(
        layers=layers,
        show_layers=show_layers,
        show_cadastre=True,
        center=center,
        zoom=zoom,
    )
    render_map_panel(
        fmap,
        height=520,
        key="cadastre_map",
        legend="Polygones locaux — vérifier la classe",
        source="cadastre_demo ou CAMI si importé",
    )

    if len(wgs):
        idx = st.number_input("Ligne à analyser", min_value=0, max_value=max(0, len(wgs) - 1), value=0)
        row = wgs.iloc[int(idx)]
        src = str(row.get("source", ""))
        official = src.lower() in {"cami", "cami_officiel", "rdc.mines-rdc.cd"}
        data_class = "official" if official else ("demo" if "demo" in src.lower() else "historical")
        render_detail_panel(
            "Détail de la concession",
            [
                ("Numéro", row.get("numero_permis") or UNAVAILABLE),
                ("Type / statut", row.get("statut") or UNAVAILABLE),
                ("Titulaire", row.get("titulaire") or UNAVAILABLE),
                ("Province", row.get("province") or UNAVAILABLE),
                ("Substance", row.get("commodity") or UNAVAILABLE),
                (
                    "État de vérification",
                    "OFFICIELLEMENT VÉRIFIÉ" if official else "DONNÉE NON VÉRIFIÉE",
                ),
            ],
            data_class=data_class,
            source_block={
                "source": src or UNAVAILABLE,
                "date": UNAVAILABLE,
                "crs": str(wgs.crs),
                "confidence": "Élevée" if official else "Faible — démonstration",
            },
            actions=True,
        )
        csv = display.to_csv(index=False).encode("utf-8")
        st.download_button("Exporter CSV", csv, "cadastre_local.csv", "text/csv")

_ = filters
close_page()
