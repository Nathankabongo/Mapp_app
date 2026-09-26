"""08 — Risques & environnement."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.data_table import render_data_table
from app.components.empty_state import render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from compass_core.analysis.site_evaluation import evaluate_site
from compass_core.models.risk import load_rules, score_risk

filters = bootstrap("Risques", active_page="Risques")
masthead(
    "Risques & environnement",
    "Indicateurs d'aide à la décision — géotechnique, hydrologique, environnemental, social, infrastructure.",
    sources="Règles config/risk_rules.json · MNT / démographie si disponibles",
)
render_warning_state(
    "Ces scores ne constituent pas un diagnostic réglementaire ni une expertise de terrain.",
    title="Aide à la décision",
)

render_section("Position évaluée")
c1, c2 = st.columns(2)
lat = c1.number_input("Latitude", value=-10.716, format="%.4f")
lon = c2.number_input("Longitude", value=25.465, format="%.4f")
report = evaluate_site(lat, lon)
rules = load_rules()
risk = score_risk(
    slope_deg=None if report.terrain.risk_level == "inconnu" else report.terrain.slope_deg,
    water_distance_km=report.terrain.water_distance_km if report.terrain.risk_level != "inconnu" else None,
    density_per_km2=report.demographics.density_per_km2,
    rules=rules,
)

render_section("Score global")
render_kpi_row(
    [
        {
            "label": "Risque global",
            "value": f"{risk.global_score}/100",
            "footnote": risk.global_label,
            "data_class": "computed",
        },
        {"label": "Géotechnique", "value": risk.geotech, "data_class": "computed"},
        {"label": "Hydrologique", "value": risk.hydro, "data_class": "computed"},
        {"label": "Social", "value": risk.social, "data_class": "computed"},
    ]
)

render_section("Matrice de risques")
matrix = pd.DataFrame(
    [
        ["Géotechnique", risk.geotech],
        ["Hydrologique", risk.hydro],
        ["Environnemental", risk.environmental],
        ["Social", risk.social],
        ["Infrastructure", risk.infrastructure],
    ],
    columns=["Famille", "Niveau"],
)
render_data_table(matrix, search_placeholder="Filtrer…", height=220, key="risk_matrix")

from compass_core.environment.assessment import environmental_state

env = environmental_state(lat, lon)
render_section("État environnemental (télédétection)")
render_kpi_row(
    [
        {
            "label": "État",
            "value": env["state"],
            "footnote": "BON · MOYEN · DÉGRADÉ · CRITIQUE",
            "data_class": env.get("data_class", "unavailable"),
        },
        {
            "label": "NDVI",
            "value": env["ndvi"].get("status", "—") if isinstance(env["ndvi"], dict) else "—",
            "data_class": "unavailable",
        },
    ]
)
st.caption(env["justification"])

render_section("Règles actives")
for msg in risk.messages:
    st.write(f"— {msg}")
if not risk.messages:
    st.caption("Aucune règle haute intensité déclenchée (ou données manquantes).")
st.json(rules)
st.caption(risk.disclaimer)
st.caption("Zones protégées : information non disponible tant qu'un fichier WDPA/ICCN n'est pas chargé.")
_ = filters
close_page()
