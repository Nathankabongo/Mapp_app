"""12 — Rapports & export."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from compass_core.analysis.site_evaluation import evaluate_site
from compass_core.reports.generator import (
    export_csv,
    export_excel,
    export_geojson,
    export_gpkg,
    export_pdf,
    report_payload,
)

filters = bootstrap("Rapports", active_page="Rapports")
masthead(
    "Rapports & export",
    "Génération de livrables décideur avec sources, méthodologie et niveau de confiance.",
    sources="Point analysé · atlas · modèle si emprise",
)

render_section("Paramètres du rapport")
c1, c2, c3 = st.columns(3)
lat = c1.number_input("Latitude", value=-10.716, format="%.4f")
lon = c2.number_input("Longitude", value=25.465, format="%.4f")
author = c3.text_input("Auteur", "Analyste")

report = evaluate_site(lat, lon)
payload = report_payload(report, author=author)

render_section("Plan du rapport")
for i, section in enumerate(
    [
        "Résumé exécutif",
        "Carte / localisation",
        "Coordonnées",
        "Minerais",
        "Géologie",
        "Cadastre",
        "Favorabilité",
        "Risques",
        "Population",
        "Infrastructure",
        "Conclusion",
        "Sources & confiance",
    ],
    1,
):
    st.caption(f"{i}. {section}")

with st.expander("Aperçu JSON du payload"):
    st.json(payload)

render_section("Générer")
out = Path("outputs/reports")
if st.button("Générer un rapport", type="primary"):
    pdf = export_pdf(payload, out / "analyse.pdf")
    csv = export_csv(payload, out / "analyse.csv")
    geojson = export_geojson(report, out / "analyse.geojson")
    gpkg = export_gpkg(report, out / "analyse.gpkg")
    try:
        xlsx = export_excel(payload, out / "analyse.xlsx")
        st.success(f"Excel : {xlsx}")
    except Exception as exc:
        st.warning(f"Excel indisponible ({exc}). CSV généré.")
    st.success(f"CSV {csv} · GeoJSON {geojson} · GPKG {gpkg}")
    if pdf:
        st.success(f"PDF {pdf}")
        st.download_button("Télécharger PDF", pdf.read_bytes(), "compass_rdc.pdf", "application/pdf")
    else:
        st.warning("PDF : installez reportlab (`pip install -e '.[report]'`).")
    st.download_button("Télécharger CSV", csv.read_bytes(), "compass_rdc.csv", "text/csv")

_ = filters
close_page()
