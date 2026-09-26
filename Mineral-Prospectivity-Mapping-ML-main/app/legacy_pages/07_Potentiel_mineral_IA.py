"""07 — Potentiel minéral & moteur de prospectivité."""

from __future__ import annotations

import importlib

import streamlit as st

from app.components.detail_panel import render_detail_panel
from app.components.empty_state import render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.components.prospectivity_map import (
    build_prospectivity_map_layers,
    commodity_labels_for_mineral,
)
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from app.workspace import load_workspace
from app.helpers import render_results_panel
from compass_core.config.demo import build_demo_config
from compass_core.config.schema import SUPPORTED_MODELS
from compass_core.constants import FAVORABILITY_BANDS, UNAVAILABLE
from compass_core.pipeline import core as _pipeline_core
from compass_core.pipeline import runner as _pipeline_runner
from compass_core.prospectivity.models import list_models
from compass_core.prospectivity.prediction import ZONE_PRESETS, run_prospectivity

# Rechargement forcé : Streamlit peut garder un ancien module en cache
from compass_core.minerals import zone_knowledge as _zk

_zk = importlib.reload(_zk)
_pipeline_core = importlib.reload(_pipeline_core)
_pipeline_runner = importlib.reload(_pipeline_runner)
run_pipeline_synthetic = _pipeline_runner.run_pipeline_synthetic
minerals_for_zone = _zk.minerals_for_zone
recommended_model_for = _zk.recommended_model_for
resolve_zone_defaults = _zk.resolve_zone_defaults

filters = bootstrap("Potentiel IA", active_page="Potentiel minéral")
masthead(
    "Mineral Prospectivity Mapping",
    "Moteur de prospectivité minérale — indice prédictif explicable, jamais un gisement confirmé.",
    sources="Pipeline DONNÉES → FEATURES → MODÈLE → CARTE → VALIDATION → CONFIANCE",
)

render_warning_state(
    "Le résultat est un indice prédictif de favorabilité. "
    "Hors emprise : Score non évalué — données hors emprise. "
    "Jamais de score 0 déguisé en certitude. Potentiel élevé ≠ gisement confirmé.",
    title="PRÉDICTION IA",
)

render_section("Sélection zone · minerai · modèle")
c1, c2, c3 = st.columns(3)
zone = c1.selectbox("Zone", list(ZONE_PRESETS.keys()), help="Le minerai cible se remplit automatiquement.")

preset = ZONE_PRESETS[zone]
province = str(preset.get("province") or "RDC")
# Localité = nom de zone si ce n'est pas « Personnalisée »
locality = None if zone == "Personnalisée" else zone
defaults = resolve_zone_defaults(province=province, locality=locality)

# Sync auto quand la zone change
if st.session_state.get("_mpm_zone") != zone:
    st.session_state["_mpm_zone"] = zone
    st.session_state["mpm_lat"] = float(preset["lat"])
    st.session_state["mpm_lon"] = float(preset["lon"])
    auto_mineral = defaults.get("mineral") or preset.get("mineral_default")
    st.session_state["mpm_mineral_auto"] = auto_mineral

# Minerais de la province (contextuels) — fallback sur défaut zone
zone_minerals = minerals_for_zone(province)
mineral_names = [m.mineral for m in zone_minerals]
auto_m = st.session_state.get("mpm_mineral_auto") or defaults.get("mineral") or preset.get("mineral_default")

if mineral_names:
    if auto_m not in mineral_names:
        # garder le défaut preset s'il est dans la liste, sinon premier
        auto_m = (
            preset.get("mineral_default")
            if preset.get("mineral_default") in mineral_names
            else mineral_names[0]
        )
    mineral = c2.selectbox(
        "Minerai cible",
        mineral_names,
        index=mineral_names.index(auto_m),
        key=f"mpm_mineral_{zone}",
        help=f"Prérempli pour {zone} ({province}).",
    )
    info = next((m for m in zone_minerals if m.mineral == mineral), None)
else:
    # Province sans KB (ex. Kinshasa) — afficher le défaut ou saisie
    fallback_list = [
        x
        for x in [
            auto_m,
            preset.get("mineral_default"),
            "cuivre",
            "or",
            "lithium",
            "diamant",
        ]
        if x
    ]
    # unique preserve order
    seen = set()
    options = []
    for x in fallback_list:
        if x not in seen:
            seen.add(x)
            options.append(x)
    mineral = c2.selectbox(
        "Minerai cible",
        options,
        index=0,
        key=f"mpm_mineral_{zone}",
        help=f"Aucun catalogue riche pour {province} — valeur associée à la zone.",
    )
    info = None

model_info = recommended_model_for(province=province, mineral=mineral, locality=locality)
catalog_codes = [m["code"] for m in list_models() if m.get("status") == "disponible"]
if not catalog_codes:
    catalog_codes = [m["code"] for m in list_models()]

model_ui = None
if model_info.get("prospectivity_ready") and model_info.get("code"):
    preferred = model_info["code"]
    model_options = catalog_codes if preferred in catalog_codes else [preferred, *catalog_codes]
    model_ui = c3.selectbox(
        "Modèle",
        model_options,
        index=model_options.index(preferred) if preferred in model_options else 0,
        key=f"mpm_model_{zone}_{mineral}",
        help=model_info.get("reason", ""),
    )
    model = model_ui
else:
    model_ui = c3.selectbox(
        "Modèle",
        ["N/E — aucun modèle pour cette emprise", *catalog_codes],
        index=0,
        key=f"mpm_model_ne_{zone}_{mineral}",
        help=model_info.get("reason", "Prospectivité N/E hors emprise pilote."),
    )
    # Pour l'appel moteur, garder un code technique si l'utilisateur choisit une alternative
    if str(model_ui).startswith("N/E"):
        model = "woe"  # requête → status N/E côté moteur si hors emprise
        st.caption("⚠ Aucun modèle entraîné pour cette zone × minerai — résultat attendu : N/E.")
    else:
        model = model_ui
        st.caption("Modèle choisi manuellement — l'emprise peut rester N/E sans raster.")

if info:
    st.caption(" · ".join(info.badges[:3]) if info.badges else defaults.get("model", {}).get("reason", "")[:120])
elif defaults.get("mineral"):
    st.caption(f"Minerai associé à **{zone}** : **{mineral}** ({province})")

lat = st.number_input("Latitude", format="%.4f", key="mpm_lat")
lon = st.number_input("Longitude", format="%.4f", key="mpm_lon")

result = run_prospectivity(
    zone=zone,
    mineral=mineral,
    latitude=lat,
    longitude=lon,
    model=model if model in catalog_codes or model in SUPPORTED_MODELS else "woe",
    province=province,
)

# Carte synchronisée sur Zone × Minerai × Modèle × Lat/Lon
render_section("Carte de prospectivité (emprise disponible)")
map_layers = build_prospectivity_map_layers(
    mineral=mineral,
    latitude=float(lat),
    longitude=float(lon),
    status=result.status,
    prospectivity_pct=result.prospectivity_pct,
    prospectivity_level=result.prospectivity_level,
    in_bounds=result.in_bounds,
    model_used=result.model_used,
)

if result.status == "evaluated" and result.in_bounds:
    st.success(
        f"Point dans l'emprise pilote — score **{result.prospectivity_pct:.0f} %** "
        f"({result.prospectivity_level}). Carte raster + hotspots affichés."
    )
elif map_layers.get("near_extent"):
    st.warning(
        "Raster Cu-Co Kolwezi à proximité, mais point **hors emprise** évaluable — "
        "score **N/E** (pas un 0)."
    )
elif map_layers["has_raster_for_mineral"]:
    st.info(
        f"Minerai **{mineral}** compatible avec le raster pilote Kolwezi, mais ce point "
        f"(**{zone}**) est loin de l'emprise — carte contextuelle sans overlay. Score **N/E**."
    )
else:
    st.info(
        f"Pas de carte raster de prospectivité pour **{mineral}** × **{zone}** — "
        "occurrences atlas + point GPS uniquement. Score **N/E**."
    )

# Couches atlas filtrées province + minerai (indépendant du sidebar générique)
map_filters = {
    **filters,
    "province": province if province not in {"RDC", ""} else "Toute la RDC",
    "minerai": commodity_labels_for_mineral(mineral) or filters.get("minerai") or [],
}
layers, show_layers, _, _ = load_workspace(map_filters)

# Zoom : serré si évalué / emprise visible, sinon vue zone
if result.in_bounds and result.status == "evaluated":
    zoom = 11
elif map_layers.get("near_extent"):
    zoom = 10
elif zone == "Personnalisée":
    zoom = 5
else:
    zoom = 8

fmap = build_platform_map(
    layers=layers,
    show_layers=show_layers,
    show_cadastre=True,
    show_hotspots=map_layers["show_hotspots"],
    hotspots=map_layers["hotspots"],
    center=(float(lat), float(lon)),
    zoom=zoom,
    highlight=(float(lat), float(lon)),
    highlight_popup=map_layers["highlight_popup"],
    basemap="esri_satellite",
    extent_overlays=map_layers["extent_overlays"],
    image_overlays=map_layers["image_overlays"],
)
# Clé dynamique → streamlit-folium rafraîchit la carte à chaque modification
map_key = (
    f"mpm_map_{zone}_{mineral}_{model}_{result.status}_"
    f"{round(float(lat), 4)}_{round(float(lon), 4)}"
)
legend = (
    "Raster prospectivité (pilote) · emprise · hotspots >70 % · occurrences minerai"
    if map_layers.get("near_extent")
    else "Occurrences atlas (minerai) · point GPS — pas de raster pour ce couple"
)
render_map_panel(
    fmap,
    height=460,
    key=map_key,
    legend=legend,
    source=result.raster_path or UNAVAILABLE,
)
st.caption(
    f"Carte liée à : **{zone}** · **{mineral}** · modèle `{model}` · "
    f"({float(lat):.4f}, {float(lon):.4f}) · statut **{result.prospectivity_level}**"
)

render_section("Scores")
render_kpi_row(
    [
        {
            "label": "Prospectivité",
            "value": f"{result.prospectivity_pct:.0f} %"
            if result.prospectivity_pct is not None
            else "N/E",
            "footnote": result.prospectivity_level,
            "data_class": "prediction",
        },
        {
            "label": "Confiance modèle",
            "value": f"{result.model_confidence_pct:.0f} %",
            "footnote": result.evidence_stage,
            "data_class": "computed",
        },
        {
            "label": "Province",
            "value": result.province[:12],
            "footnote": result.metric_crs,
            "data_class": "computed",
        },
        {
            "label": "Emprise",
            "value": "Oui" if result.in_bounds else "Non",
            "footnote": result.model_used,
            "data_class": "prediction" if result.in_bounds else "unavailable",
        },
    ]
)

if result.prospectivity_pct is not None:
    st.progress(min(1.0, result.prospectivity_pct / 100.0))

st.caption("Classification carte :")
for lo, hi, label in FAVORABILITY_BANDS:
    st.caption(f"{int(lo * 100)}–{int(min(100, hi * 100))}  {label}")

from app.components.validation_panel import render_validation_panel
from compass_core.exploration.explainability import get_xai_for_prospectivity

a, b = st.columns(2)
with a:
    if result.prospectivity_pct is not None:
        st.markdown(get_xai_for_prospectivity(result.prospectivity_pct, zone))
        render_validation_panel(zone, result.prospectivity_pct)
    else:
        render_detail_panel(
        "Données disponibles",
        [(x, "✓") for x in (result.available_layers or ["Aucune couche complète"])],
        data_class="imported",
    )
with b:
    render_detail_panel(
        "Données manquantes",
        [(x, "⚠") for x in result.missing_layers[:8]],
        data_class="unavailable",
    )

st.caption(result.disclaimer)
st.info(result.recommendation_hint)

render_section("Catalogue de modèles (comparaison)")
for m in list_models():
    st.caption(f"`{m['code']}` — {m['label']} · {m['status']} · deps: {m['needs']}")

render_section("Laboratoire ML synthétique")
lab = st.selectbox("Modèle démo mémoire", SUPPORTED_MODELS, key="lab_model")
if st.button("Exécuter démo synthétique"):
    cfg = build_demo_config(model=lab, output_dir="outputs/streamlit_demo", seed=42, project_name="mpm-demo")
    with st.spinner("Entraînement…"):
        try:
            out = run_pipeline_synthetic(cfg)
            st.success(
                f"Run `{out.run_id}` — AUC {out.metrics['auc']:.4f} · "
                f"Kappa {out.metrics['kappa']:.4f}"
            )
            render_results_panel(out, model_name=lab)
        except Exception as exc:
            st.error(str(exc))

_ = filters
close_page()
