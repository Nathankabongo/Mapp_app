"""17 — Campagne d'exploration nationale RDC (Minerai × Zone × Données × Modèle)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.data_table import render_data_table
from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_demo_notice, render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from compass_core.drilling.next_best_drillhole import next_best_drillhole
from compass_core.exploration.campaign import run_campaign
from compass_core.exploration.history import save_campaign
from compass_core.exploration.planning import plan_for_target
import importlib
from compass_core.minerals import zone_knowledge as _zk

_zk = importlib.reload(_zk)
list_all_provinces = _zk.list_all_provinces
list_localities = _zk.list_localities
minerals_for_zone = _zk.minerals_for_zone
recommended_model_for = _zk.recommended_model_for
resolve_zone_defaults = _zk.resolve_zone_defaults
zone_fact_sheet = _zk.zone_fact_sheet


filters = bootstrap("Campagne exploration", active_page="Campagne exploration")
masthead(
    "Campagne d'exploration minière — RDC",
    "Module national : province → minerais documentés → données → prospectivité (ou N/E) → cibles.",
    sources="Knowledge base Minerai×Zone · atlas · raster pilote Kolwezi Cu-Co",
)
render_demo_notice("La campagne couvre toute la RDC. Kolwezi = seule emprise avec raster de prospectivité automatique.")
render_warning_state(
    "Présence documentée ≠ prospectivité. N/E = non évalué (pas un score 0). "
    "Prédiction IA ≠ gisement confirmé.",
    title="Règles",
)

# —— Formulaire national : Zone → Minerai + Modèle automatiques ——
render_section("1 — Zone → Minerai cible → Modèle")
provinces = list_all_provinces()
c1, c2, c3 = st.columns(3)
province = c1.selectbox(
    "Zone (province)",
    provinces,
    index=provinces.index("Lualaba") if "Lualaba" in provinces else 0,
    help="Toute la RDC. Le minerai et le modèle se mettent à jour automatiquement.",
)

locs = list_localities(province=province)
loc_names = ["(Centroïde province)", *[L["name"] for L in locs]]
locality = c2.selectbox("Localité (optionnel)", loc_names)
exp_type = c3.selectbox("Type d'exploration", ["Régionale", "Semi-détaillée", "Détaillée"])

loc_key = None if locality == "(Centroïde province)" else locality
defaults = resolve_zone_defaults(province=province, locality=loc_key)

# Synchroniser lat/lon quand la zone change
zone_sig = f"{province}|{locality}"
if st.session_state.get("_camp_zone_sig") != zone_sig:
    st.session_state["_camp_zone_sig"] = zone_sig
    st.session_state["camp_lat"] = float(defaults["latitude"])
    st.session_state["camp_lon"] = float(defaults["longitude"])
    st.session_state["camp_mineral_auto"] = defaults.get("mineral")
    st.session_state["camp_model_auto"] = (defaults.get("model") or {}).get("code")

lat = st.number_input("Latitude", format="%.4f", key="camp_lat")
lon = st.number_input("Longitude", format="%.4f", key="camp_lon")

zone_label = defaults["zone"]
zone_minerals = minerals_for_zone(province)
mineral_names = [m.mineral for m in zone_minerals]

mcol, modcol = st.columns(2)
with mcol:
    if not mineral_names:
        st.warning(f"Aucun minerai documenté pour « {province} » — saisie libre (prospectivité N/E).")
        mineral = st.text_input(
            "Minerai cible (à exploiter)",
            value=st.session_state.get("camp_mineral_auto") or "cuivre",
            key="camp_mineral_free",
        )
        selected_info = None
    else:
        auto_m = st.session_state.get("camp_mineral_auto") or defaults.get("mineral") or mineral_names[0]
        if auto_m not in mineral_names:
            auto_m = mineral_names[0]
        mineral = st.selectbox(
            "Minerai cible (à exploiter)",
            mineral_names,
            index=mineral_names.index(auto_m),
            key=f"camp_mineral_{province}",
            help="Prérempli selon la zone sélectionnée — vous pouvez changer parmi les minerais documentés.",
        )
        selected_info = next((m for m in zone_minerals if m.mineral == mineral), None)

with modcol:
    model_info = recommended_model_for(
        province=province,
        mineral=mineral,
        locality=loc_key,
    )
    if model_info.get("prospectivity_ready") and model_info.get("code"):
        alt = model_info.get("alternatives") or [model_info["code"]]
        default_code = model_info["code"]
        if default_code not in alt:
            alt = [default_code, *alt]
        model = st.selectbox(
            "Modèle",
            alt,
            index=alt.index(default_code) if default_code in alt else 0,
            key=f"camp_model_{province}_{mineral}",
            help="Modèle recommandé pour cette zone × minerai.",
        )
        st.caption(f"✓ {model_info.get('label')} — {model_info.get('reason', '')[:120]}")
    else:
        model = None
        st.selectbox(
            "Modèle",
            ["N/E — aucun modèle pour cette emprise"],
            index=0,
            disabled=True,
            key=f"camp_model_ne_{province}_{mineral}",
        )
        st.caption(f"⚠ {model_info.get('reason', 'Prospectivité N/E')[:160]}")

if selected_info:
    st.markdown("**Pourquoi ce minerai pour cette zone**")
    for b in selected_info.badges:
        st.write(b)
    for w in selected_info.why[:3]:
        st.caption(f"→ {w}")

    with st.expander("Tous les minerais documentés dans cette zone"):
        rows = [
            {
                "Minerai": m.mineral,
                "Evidence": m.evidence_level,
                "Occurrences atlas": str(m.occurrence_count) if m.occurrence_count is not None else "—",
                "Modèle": "WoE (pilote)" if m.prospectivity_available else "N/E",
                "Badges": " · ".join(m.badges[:2]),
            }
            for m in zone_minerals
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# —— Fiche zone ——
sheet = zone_fact_sheet(province, latitude=lat, longitude=lon)
render_section(f"2 — Fiche zone : {sheet.province}")
st.caption(f"Bassin : {sheet.basin} · Minerai retenu : **{mineral}** · Modèle : **{model or 'N/E'}**")
cov = sheet.data_coverage or {}
kpi_cov = []
for key in ("geology", "satellite", "geochemistry", "geophysics", "drillholes", "prospectivity"):
    block = cov.get(key) or {}
    pct = int(block.get("pct", 0))
    bar = "█" * max(0, pct // 10) + "░" * max(0, 10 - pct // 10)
    kpi_cov.append({"label": block.get("label", key), "value": f"{pct}%", "footnote": bar, "data_class": "computed"})
render_kpi_row(kpi_cov[:3])
render_kpi_row(kpi_cov[3:])

max_t = st.slider("Nb cibles max (si prospectivité évaluée)", 3, 15, 10)

if st.button("Lancer l'analyse nationale", type="primary"):
    campaign = run_campaign(
        zone=zone_label,
        province=province,
        mineral=mineral,
        model=model or "woe",
        exploration_type=exp_type,
        latitude=lat,
        longitude=lon,
        max_targets=max_t,
    )
    st.session_state["exploration_campaign"] = campaign.to_dict()

camp = st.session_state.get("exploration_campaign")
if not camp:
    st.info("Sélectionner province + minerai, puis lancer l'analyse.")
    # Carte nationale occurrences
    render_section("Carte — minerais de la RDC (atlas)")
    layers, show_layers, center, zoom = load_workspace(filters)
    fmap = build_platform_map(
        layers=layers,
        show_layers=show_layers,
        show_cadastre=True,
        center=(lat, lon),
        zoom=max(6, zoom - 1),
        basemap="esri_satellite",
    )
    render_map_panel(fmap, height=420, key="camp_pre_map", legend="Occurrences atlas (filtres latéraux)")
    close_page()
    st.stop()

prosp = camp["prospectivity"]
targets = camp["targets"]
zctx = camp.get("zone_context") or {}

render_section("4 — Résultat prospectivité")
is_ne = prosp.get("status") == "N/E" or prosp.get("prospectivity_pct") is None
prosp_display = "N/E" if is_ne else f"{prosp['prospectivity_pct']:.0f} %"
render_kpi_row(
    [
        {"label": "Province", "value": camp["province"][:16], "data_class": "computed"},
        {"label": "Minerai", "value": camp["mineral"], "data_class": "prediction"},
        {
            "label": "Prospectivité",
            "value": prosp_display,
            "footnote": prosp.get("prospectivity_level", "—"),
            "data_class": "unavailable" if is_ne else "prediction",
        },
        {
            "label": "Cibles",
            "value": str(len(targets)),
            "data_class": "prediction" if targets else "unavailable",
        },
    ]
)

if is_ne:
    st.error(
        "⚠ Prospectivité : **N/E** — Non évalué. "
        "Ce n'est pas un score de favorabilité nulle (0)."
    )
    ne = prosp.get("ne_guidance") or zctx.get("ne_guidance") or {}
    st.markdown(f"**Pourquoi :** {ne.get('why_ne', prosp.get('disclaimer', ''))}")
    if ne.get("mineral_documented"):
        st.success("✓ Minerai documenté dans cette zone — mais sans modèle raster.")
    st.markdown("**Recommandations :**")
    for step in ne.get("recommendations") or []:
        st.write(f"→ {step}")
    st.caption(ne.get("pilot_available_elsewhere", ""))
else:
    st.success(
        f"Prospectivité évaluée sur emprise pilote ({prosp.get('model_used', 'raster')})."
    )

render_section("5 — Inventaire & lacunes")
inv = camp["data_inventory"]
cols = st.columns(5)
for i, key in enumerate(["satellite", "geology", "geophysics", "geochemistry", "prospectivity_raster"]):
    block = inv.get(key, {})
    with cols[i % 5]:
        render_detail_panel(
            key.replace("_", " ").upper(),
            [("Statut", block.get("status", "—")), ("Note", str(block.get("note", ""))[:40] or ", ".join(block.get("items", [])[:2]))],
            data_class="unavailable" if "NON" in str(block.get("status", "")) or block.get("status") == "N/E" else "computed",
        )

diag = camp.get("diagnostic") or {}
if diag.get("gaps"):
    for g in diag["gaps"][:8]:
        st.markdown(f"- ⚠ {g}")

render_section("6 — Cibles & planification")
if is_ne:
    st.info(
        "Aucune cible automatique : la génération de hotspots nécessite une prospectivité évaluée. "
        "Utiliser le diagnostic + Smart Sampling pour préparer l'acquisition de données."
    )
elif targets:
    df = pd.DataFrame(
        [
            {
                "ID": t["target_id"],
                "Prospectivité": t["prospectivity_score"],
                "Confiance %": t["confidence_pct"],
                "Incertitude": t.get("uncertainty_label", "—"),
                "Priorité": f"{t['stars']} {t['priority_label']}",
                "Score": t["exploration_priority_score"],
            }
            for t in targets
        ]
    )
    render_data_table(df, search_placeholder="Filtrer cibles…", height=260, key="exp_targets")
    top = targets[0]
    gaps = diag.get("gaps") or []
    plan = plan_for_target(top, diagnostic_gaps=gaps)
    block = plan[top["target_id"]]
    nbd = next_best_drillhole(targets=targets, existing_holes=0)
    p1, p2 = st.columns(2)
    with p1:
        render_detail_panel(
            f"Plan — {top['target_id']}",
            [
                ("Prochaine action", block.get("next_action", "—")),
                ("Forage", block.get("drill_decision", "—")),
                ("Coût relatif", block.get("estimated_relative_cost", "—")),
            ],
            data_class="prediction",
        )
    with p2:
        render_detail_panel(
            "Next Best Drillhole",
            [
                ("Cible", nbd.get("target_id", "—")),
                ("VOI", nbd.get("voi_score", "—")),
                ("Statut", nbd.get("status", "—")),
            ],
            data_class="prediction",
        )
else:
    st.warning("Aucune cible générée malgré statut évalué — raster sans hotspot.")

render_section("7 — Carte")
layers, show_layers, _, _ = load_workspace(filters)
fmap = build_platform_map(
    layers=layers,
    show_layers=show_layers,
    show_cadastre=True,
    center=(camp["latitude"], camp["longitude"]),
    zoom=8 if camp["province"] != "RDC" else 5,
    highlight=(camp["latitude"], camp["longitude"]),
    basemap="esri_satellite",
    exploration_targets=targets,
)
render_map_panel(
    fmap,
    height=460,
    key="exp_map",
    legend="Occurrences atlas · cibles IA si évaluées",
    source="Campagne nationale RDC",
)

render_section("8 — Historique")
if st.button("Enregistrer la campagne"):
    entry = save_campaign(camp, status="ouverte")
    st.success(f"Sauvegardé : {entry.campaign_id}")

st.caption(camp["disclaimer"])
with st.expander("JSON campagne"):
    st.json(camp)

_ = filters
close_page()
