"""21 — Explorateur de zones + diagnostic automatique."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_demo_notice, render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.exploration.campaign import run_campaign
from compass_core.exploration.diagnostic import diagnose_zone
from compass_core.exploration.explainability import compare_targets, explain_target
from compass_core.minerals.profiles import get_profile, list_mineral_names
from compass_core.prospectivity.prediction import ZONE_PRESETS

filters = bootstrap("Explorateur de zones", active_page="Explorateur de zones")
masthead(
    "Explorateur de zones",
    "Sélectionner une zone → inventaire des données → diagnostic des lacunes → cibles et explications.",
    sources="Diagnostic · profils minéraux · prospectivité",
)
render_demo_notice("Diagnostic honnête : absence de donnée = « Donnée indisponible », jamais inventée.")
render_warning_state(
    "Prédiction IA ≠ gisement confirmé. Les cibles sont des hypothèses d'exploration.",
    title="Rappel",
)

render_section("1 — Sélection de la zone")
c1, c2, c3 = st.columns(3)
zone = c1.selectbox("Zone / preset", list(ZONE_PRESETS.keys()), index=0)
preset = ZONE_PRESETS[zone]
minerals = list_mineral_names()
default_m = preset.get("mineral_default", "cuivre")
m_idx = minerals.index(default_m) if default_m in minerals else 0
mineral = c2.selectbox("Minerai cible", minerals, index=m_idx)
mode = c3.selectbox(
    "Mode de sélection",
    ["Preset zone", "Coordonnées", "Rayon autour d'une occurrence (via lat/lon)"],
)
lat = st.number_input("Latitude", value=float(preset["lat"]), format="%.4f", key="zone_lat")
lon = st.number_input("Longitude", value=float(preset["lon"]), format="%.4f", key="zone_lon")
st.caption(
    f"Province preset : {preset.get('province', '—')} · "
    f"Mode « {mode} » — polygone dessiné : à venir (utiliser lat/lon pour AOI ponctuelle)."
)

profile = get_profile(mineral)
if profile:
    with st.expander("Profil minéral", expanded=False):
        st.markdown(f"**{profile.display_name}** — {profile.geological_context}")
        st.caption(
            "Lithologies favorables : "
            + (", ".join(profile.favorable_lithologies) or "Donnée indisponible")
        )
        st.caption(
            "Éléments géochimiques : "
            + (", ".join(profile.geochemical_elements) or "Donnée indisponible")
        )
        if not profile.supports_raster_targets():
            st.info(
                "Pas de raster de prospectivité pour ce minerai — "
                "diagnostic et inventaire disponibles, cibles automatiques = liste vide."
            )

run = st.button("Analyser la zone", type="primary")
if run:
    diag = diagnose_zone(zone=zone, mineral=mineral, latitude=lat, longitude=lon)
    camp = run_campaign(
        zone=zone, mineral=mineral, latitude=lat, longitude=lon, max_targets=10
    )
    st.session_state["zone_diagnostic"] = diag.to_dict()
    st.session_state["zone_campaign"] = camp.to_dict()

diag = st.session_state.get("zone_diagnostic")
camp = st.session_state.get("zone_campaign")
if not diag:
    st.info("Choisir une zone et lancer l'analyse.")
    close_page()
    st.stop()

render_section("2 — Diagnostic automatique")
st.caption(diag.get("disclaimer", ""))
render_kpi_row(
    [
        {"label": "Zone", "value": diag["zone"][:12], "data_class": "computed"},
        {"label": "Province", "value": str(diag["province"])[:14], "data_class": "computed"},
        {"label": "Minerai", "value": diag["mineral"], "data_class": "prediction"},
        {
            "label": "Prospectivité",
            "value": (
                f"{diag['prospectivity'].get('prospectivity_pct')}%"
                if diag["prospectivity"].get("prospectivity_pct") is not None
                else "N/E"
            ),
            "data_class": "prediction",
        },
    ]
)

domains = [
    ("geology", "GÉOLOGIE"),
    ("geochemistry", "GÉOCHIMIE"),
    ("geophysics", "GÉOPHYSIQUE"),
    ("satellite", "SATELLITE"),
    ("exploration_history", "HISTORIQUE"),
    ("cadastre", "CADASTRE"),
]
cols = st.columns(3)
for i, (key, title) in enumerate(domains):
    block = diag.get(key, {})
    counts = block.get("counts") or {}
    rows = [("Statut", block.get("status", "—"))]
    for ck, cv in list(counts.items())[:4]:
        rows.append((ck.replace("_", " "), str(cv)))
    with cols[i % 3]:
        render_detail_panel(
            title,
            rows,
            data_class=(
                "unavailable"
                if "NON" in str(block.get("status", ""))
                else ("demo" if "DÉMO" in str(block.get("status", "")) else "computed")
            ),
        )

render_section("3 — Lacunes de données")
gaps = diag.get("gaps") or []
if gaps:
    for g in gaps:
        st.markdown(f"- ⚠ {g}")
else:
    st.success("Aucune lacune majeure signalée (couverture relative).")

avail = diag.get("available_summary") or []
if avail:
    render_section("Données disponibles")
    for a in avail:
        st.markdown(f"- ✓ {a}")

render_section("4 — Carte de contexte")
layers, show_layers, center, zoom = load_workspace(filters)
fmap = build_platform_map(
    layers=layers,
    show_layers=show_layers,
    show_cadastre=True,
    show_hotspots=True,
    center=(diag["latitude"], diag["longitude"]),
    zoom=max(zoom, 8),
    basemap="esri_satellite",
)
render_map_panel(fmap, height=480, key="zone_explorer_map", legend="Zone · atlas · cadastre")

targets = (camp or {}).get("targets") or []
render_section("5 — Cibles classées")
if not targets:
    st.warning(
        "Aucune cible générée — raster absent ou minerai non couvert par le modèle pilote Cu-Co."
    )
else:
    rows = [
        {
            "ID": t["target_id"],
            "Score": t.get("exploration_priority_score"),
            "Prospectivité": t.get("prospectivity_score"),
            "Confiance %": t.get("confidence_pct"),
            "Incertitude": t.get("uncertainty_label", "—"),
            "Priorité": t.get("stars"),
        }
        for t in targets
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    ids = [t["target_id"] for t in targets]
    t_sel = st.selectbox("Expliquer la cible", ids)
    chosen = next(t for t in targets if t["target_id"] == t_sel)
    exp = explain_target(chosen)
    st.markdown(f"**Pourquoi {exp.target_id} ?** {exp.why}")
    factor_rows = [
        {
            "Facteur": f["label"],
            "Dispo": "oui" if f["available"] else "non",
            "Contribution": f["contribution"],
            "Note": f["note"],
        }
        for f in exp.factors
    ]
    st.dataframe(pd.DataFrame(factor_rows), use_container_width=True, hide_index=True)
    st.caption(exp.disclaimer)

    if len(targets) >= 2:
        render_section("6 — Comparaison de cibles")
        a_id = st.selectbox("Cible A", ids, key="cmp_a")
        b_id = st.selectbox("Cible B", [i for i in ids if i != a_id] or ids, key="cmp_b")
        if a_id != b_id:
            ta = next(t for t in targets if t["target_id"] == a_id)
            tb = next(t for t in targets if t["target_id"] == b_id)
            cmp = compare_targets(ta, tb)
            st.info(cmp.narrative)
            st.dataframe(pd.DataFrame(cmp.deltas), use_container_width=True, hide_index=True)

close_page()
