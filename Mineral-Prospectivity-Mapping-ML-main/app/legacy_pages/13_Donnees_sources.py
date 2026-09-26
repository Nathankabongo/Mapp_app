"""13 — Données & sources."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.data_table import render_data_table
from app.components.detail_panel import render_detail_panel
from app.components.section_header import render_section
from app.components.status_badge import status_badge_html
from app.shell import bootstrap, close_page, masthead
from compass_core.constants import DATA_CLASSES
from compass_core.models.confidence import stars
from compass_core.validation.data_quality import SOURCE_CATALOG, class_label

filters = bootstrap("Sources", active_page="Données & sources")
masthead(
    "Données & sources",
    "Catalogue de transparence — licence, CRS, couverture, confiance. "
    "Vérifier chaque source avant de la déclarer disponible.",
    sources="Registre Compass (liens) · fichiers locaux",
)

render_section("Classes de vérité")
badges = " ".join(status_badge_html(k) for k in DATA_CLASSES)
st.markdown(badges, unsafe_allow_html=True)

rows = []
for src in SOURCE_CATALOG:
    rows.append(
        {
            "Nom": src["name"],
            "Catégorie": src["category"],
            "Source": src["source"],
            "Date": src["date"],
            "Résolution": src["resolution"],
            "CRS": src["crs"],
            "Format": src["format"],
            "Maj": src["updated"],
            "Qualité": src["quality"],
            "Disponibilité": src["availability"],
            "Classe": class_label(src["data_class"])
            if src["data_class"] in DATA_CLASSES
            else src["data_class"],
            "Officiel ?": src["official"],
            "Vérifiable ?": src["verifiable"],
            "Confiance": stars(int(src["confidence"])),
        }
    )

render_section("Catalogue")
render_data_table(pd.DataFrame(rows), search_placeholder="CAMI, USGS, WorldPop…", key="src_tbl", height=380)

render_section("Fiche détaillée")
choice = st.selectbox("Couche", [s["name"] for s in SOURCE_CATALOG])
src = next(s for s in SOURCE_CATALOG if s["name"] == choice)
render_detail_panel(
    choice,
    [
        ("Description", src["description"]),
        ("Catégorie", src["category"]),
        ("Disponibilité", src["availability"]),
        ("Qualité", src["quality"]),
        ("Officiel", src["official"]),
        ("Vérifiable", src["verifiable"]),
    ],
    data_class=src["data_class"] if src["data_class"] in DATA_CLASSES else "historical",
    source_block={
        "source": src["source"],
        "date": src["date"],
        "crs": src["crs"],
        "confidence": stars(int(src["confidence"])),
    },
)

_ = filters
close_page()
