"""15 — Data & API Hub."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.data_table import render_data_table
from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.section_header import render_section
from app.components.status_badge import status_badge_html
from app.shell import bootstrap, close_page, masthead
from compass_core.api.connectors import probe_all
from compass_core.api.registry import registry_as_dicts, sources_by_category
from compass_core.constants import EVIDENCE_CHAIN
from compass_core.gis.crs import crs_strategy_doc
from compass_core.mining.cami import cami_status

filters = bootstrap("Data & API Hub", active_page="Data & API")
masthead(
    "Data & API Hub",
    "Centre de connexion aux sources externes et aux moteurs d'analyse — "
    "architecture API-first, sans téléchargement silencieux.",
    sources="Registre Compass · connecteurs locaux",
)

render_warning_state(
    "Aucune source distante n'est téléchargée automatiquement. "
    "Statut CONNECTÉ = tuiles/fonds déjà utilisés ; À CONFIGURER = credentials/import requis.",
    title="API-first",
)

# Chaîne de crédibilité
render_section("Chaîne de crédibilité scientifique")
chain = " → ".join(f"{status_badge_html(k)} {label}" for k, label in EVIDENCE_CHAIN)
st.markdown(
    f'<div class="cmc-panel"><p style="line-height:2">{chain}</p>'
    f"<p style=\"font-size:0.8rem;opacity:0.8\">"
    f"Une image satellite ne donne pas une teneur de gisement. "
    f"Observation → anomalie → prédiction → terrain → confirmation.</p></div>",
    unsafe_allow_html=True,
)

reg = registry_as_dicts()
by_status = {}
for r in reg:
    by_status[r["status"]] = by_status.get(r["status"], 0) + 1
render_section("Vue d'ensemble des sources")
render_kpi_row(
    [
        {"label": "Sources enregistrées", "value": str(len(reg)), "data_class": "computed"},
        {
            "label": "Connectées",
            "value": str(by_status.get("CONNECTÉ", 0)),
            "data_class": "open",
        },
        {
            "label": "À configurer",
            "value": str(by_status.get("À CONFIGURER", 0)),
            "data_class": "estimated",
        },
        {
            "label": "CAMI vérifié",
            "value": str(cami_status()["verified_count"]),
            "footnote": cami_status()["status"],
            "data_class": "unavailable" if cami_status()["verified_count"] == 0 else "official",
        },
    ]
)

render_section("Catalogue par catégorie")
grouped = sources_by_category()
tabs = st.tabs(list(grouped.keys()))
for tab, (cat, items) in zip(tabs, grouped.items()):
    with tab:
        rows = [
            {
                "Nom": s.name,
                "Fournisseur": s.provider,
                "Type": s.data_type,
                "Résolution": s.resolution,
                "Couverture": s.coverage,
                "Fréquence": s.frequency,
                "Dernière donnée": s.last_data,
                "API": s.api_available,
                "Licence": s.licence,
                "Accès": s.access_method,
                "Statut": s.status,
                "Fiabilité": s.reliability,
                "URL": s.url,
            }
            for s in items
        ]
        render_data_table(pd.DataFrame(rows), search_placeholder="Sentinel, CAMI, WorldPop…", key=f"hub_{cat}", height=280)
        choice = st.selectbox(f"Détail — {cat}", [s.name for s in items], key=f"sel_{cat}")
        src = next(s for s in items if s.name == choice)
        render_detail_panel(
            src.name,
            [
                ("Catégorie", src.category),
                ("Format", src.format),
                ("Statut", src.status),
                ("Note", src.note or "—"),
            ],
            data_class={
                "CONNECTÉ": "open",
                "DISPONIBLE": "imported",
                "À CONFIGURER": "estimated",
                "NON DISPONIBLE": "unavailable",
                "DÉMO": "demo",
            }.get(src.status, "unavailable"),
            source_block={
                "source": src.url or src.provider,
                "date": src.last_data,
                "crs": "selon source",
                "confidence": src.reliability,
            },
        )

render_section("Connecteurs locaux (probe)")
probes = probe_all()
render_data_table(pd.DataFrame(probes), key="hub_probes", height=200)

render_section("CAMI Data Connector")
st.caption(
    "Formats acceptés : CSV · GeoJSON · Shapefile · GeoPackage · API lorsque disponible. "
    "Placer un export officiel dans `data/rdc/official/` pour que Concessions vérifiées > 0."
)
cami = cami_status()
st.write(cami)

render_section("Stratégie CRS")
st.caption(crs_strategy_doc())

render_section("Architecture SOURCE → CONNECTOR → NORMALISATION → MOTEUR → UI")
st.code(
    "SOURCE → CONNECTOR → NORMALISATION → COMMON DATA MODEL → ANALYSIS ENGINE → STREAMLIT / API / REPORT",
    language="text",
)

_ = filters
close_page()
