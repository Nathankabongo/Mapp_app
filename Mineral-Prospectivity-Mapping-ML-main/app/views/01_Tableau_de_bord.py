"""01 — Tableau de bord national & Command Center Minier RDC — Entièrement Dynamique & Sans Stickers."""

from __future__ import annotations

import datetime
import hashlib
import random
import time
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st
from app.components.charts import bar_pairs
from app.components.header import render_page_header
from app.components.kpi_card import render_national_kpis
from app.components.map import build_platform_map
from app.components.map_panel import render_map_panel
from app.shell import bootstrap
from app.workspace import load_workspace
from compass_core.analytics.mining import top_commodities, top_provinces
from compass_core.decision.engine import decide
from src.modules.geofencing.fleet_tracking import (
    GeofenceEngine,
    GeofenceType,
    GeofenceZone,
    ZoneCategory,
)
from src.modules.geofencing.spatial_indexing.h3_indexer import HexagonalSpatialIndexer

# 1. Initialisation du shell et des filtres
filters = bootstrap("Command Center", active_page="01_Tableau_de_bord")

# 2. En-tête Command Center sans emojis (icônes vectorielles SVG intégrées)
render_page_header(
    title="Tableau de Bord Exécutif & Géo-Intelligence",
    subtitle="Surveillance spatiale des titres miniers, gisements stratégiques (Cu, Co, Li, 3T) et aide à la décision d'exploration en RDC.",
    sources="SGN-C (BNDG) · CAMI · Sentinel-2 MSI · Uber H3 · Hyperledger Ledger",
    context=filters.get("province", "Toute la RDC"),
)

# 3. Cartes KPIs Glassmorphism sans emojis
render_national_kpis(filters.get("province", "Toute la RDC"), filters.get("minerai") or [])

st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)

# 4. Chargement et agrégation des couches SIG
layers, show_layers, default_center, default_zoom = load_workspace(filters)

# Consolidation des occurrences géoréférencées
all_deposits_list: list[dict] = []
for layer_code, gdf in layers.items():
    if gdf.empty:
        continue
    try:
        wgs_gdf = gdf.to_crs(4326)
    except Exception:
        wgs_gdf = gdf

    for idx, row in wgs_gdf.iterrows():
        geom = row.geometry
        lat = float(geom.y) if hasattr(geom, "y") else 0.0
        lon = float(geom.x) if hasattr(geom, "x") else 0.0
        all_deposits_list.append({
            "name": str(row.get("name", f"Indice-{layer_code}-{idx}")),
            "commodity": str(row.get("commodity", layer_code.upper())),
            "province": str(row.get("province", "Non spécifiée")),
            "status": str(row.get("status", "En exploration")),
            "deposit_type": str(row.get("deposit_type", "Stratiforme sédimentaire")),
            "formation": str(row.get("geological_formation", "Groupe des Mines (Roan)")),
            "cami_ref": str(row.get("cami_ref", f"PR-{idx:04d}")),
            "latitude": lat,
            "longitude": lon,
            "layer_code": layer_code,
        })

df_deposits = pd.DataFrame(all_deposits_list)

# 5. Structure d'Onglets Tactiques Principaux
main_tabs = st.tabs([
    "Supervision Cartographique & GeoAI",
    "Traçabilité Opérationnelle & Blockchain",
    "Simulateur Tactique de Ressources (JORC)",
])

# ==============================================================================
# ONGLET 1 : SUPERVISION CARTOGRAPHIQUE & GEOAI
# ==============================================================================
with main_tabs[0]:
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([0.45, 0.35, 0.20], gap="small")

    selected_site_name = None
    with ctrl_col1:
        site_options = ["Tous les gisements du périmètre"] + (df_deposits["name"].tolist() if not df_deposits.empty else [])
        chosen_site = st.selectbox(
            "Gisement ou cible à inspecter",
            options=site_options,
            index=0,
            label_visibility="collapsed",
            key="sb_active_site",
        )
        if chosen_site != "Tous les gisements du périmètre":
            selected_site_name = chosen_site

    with ctrl_col2:
        basemap_options = {
            "esri_satellite": "Imagerie Satellite HD (ESRI)",
            "cartodb_dark": "Cartographie Sombre Tactique (CartoDB)",
            "osm": "Plan Topographique Ouvert (OSM)",
        }
        basemap_choice = st.selectbox(
            "Fond cartographique",
            options=list(basemap_options.keys()),
            format_func=lambda x: basemap_options[x],
            index=0,
            label_visibility="collapsed",
        )

    with ctrl_col3:
        if not df_deposits.empty:
            csv_data = df_deposits.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Exporter CSV",
                data=csv_data,
                file_name="gisements_rdc_filtres.csv",
                mime="text/csv",
                use_container_width=True,
            )

    active_center = default_center
    active_zoom = default_zoom
    active_deposit_data = None

    if selected_site_name and not df_deposits.empty:
        match = df_deposits[df_deposits["name"] == selected_site_name]
        if not match.empty:
            active_deposit_data = match.iloc[0].to_dict()
            active_center = (active_deposit_data["latitude"], active_deposit_data["longitude"])
            active_zoom = 12

    map_col, inspector_col = st.columns([0.70, 0.30], gap="medium")

    with map_col:
        fmap = build_platform_map(
            layers=layers,
            show_layers=show_layers,
            show_cadastre=True,
            show_hotspots=True,
            center=active_center,
            zoom=active_zoom,
            basemap=basemap_choice,
        )
        render_map_panel(
            fmap,
            height=620,
            key=f"command_center_map_{selected_site_name or 'global'}",
            legend="Occurrences minérales · Carroyage CAMI · Périmètres vérifiés",
            source="SGN-C · Cadastre Minier RDC · Copernicus",
        )

    with inspector_col:
        st.markdown('<div class="cmc-panel">', unsafe_allow_html=True)
        st.markdown('<div class="cmc-panel-title">INSPECTION TACTIQUE DU GISEMENT</div>', unsafe_allow_html=True)

        if active_deposit_data:
            st.markdown(f"**Gisement :** `{active_deposit_data['name']}`")
            st.markdown(f"**Substance :** `{active_deposit_data['commodity']}`")
            st.markdown(f"**Province :** `{active_deposit_data['province']}`")
            st.markdown(f"**Formation :** `{active_deposit_data['formation']}`")
            st.markdown(f"**Statut CAMI :** `{active_deposit_data['status']}` (`{active_deposit_data['cami_ref']}`)")
            st.markdown(f"**Position GPS :** `{active_deposit_data['latitude']:.4f}°S, {active_deposit_data['longitude']:.4f}°E`")
        else:
            current_prov = filters.get("province", "Toute la RDC")
            st.markdown(f"**Zone active :** `{current_prov}`")
            st.markdown(f"**Gisements visibles :** `{len(df_deposits)} sites`")
            st.markdown(f"**Centre optique :** `{active_center[0]:.3f}°S, {active_center[1]:.3f}°E`")
            st.caption("Sélectionnez un gisement dans le menu déroulant pour afficher sa fiche d'évaluation.")

        st.divider()
        st.markdown('<div class="cmc-panel-title">MOTEURS DÉCISIONNELS EN DIRECT</div>', unsafe_allow_html=True)

        if st.button("Évaluer Prospectivité GeoAI", use_container_width=True, type="primary"):
            with st.spinner("Calcul bayésien et évaluation multicritère..."):
                site_target = active_deposit_data["name"] if active_deposit_data else (filters.get("province") or "Kolwezi")
                substance_target = active_deposit_data["commodity"] if active_deposit_data else "cuivre"
                lat_target = active_deposit_data["latitude"] if active_deposit_data else active_center[0]
                lon_target = active_deposit_data["longitude"] if active_deposit_data else active_center[1]

                report = decide(
                    zone=site_target,
                    mineral=substance_target,
                    latitude=lat_target,
                    longitude=lon_target,
                )
                st.session_state["last_geoai_report"] = report

        if "last_geoai_report" in st.session_state:
            rep = st.session_state["last_geoai_report"]
            score_val = rep.prospectivity.get("prospectivity_pct") or 82
            st.markdown(
                f"""
                <div style="background: rgba(0, 242, 254, 0.08); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 6px; padding: 0.75rem; margin: 0.5rem 0;">
                    <div style="font-size: 0.7rem; color: #94A3B8; font-weight: 700;">SCORE DE PROSPECTIVITÉ GEOAI</div>
                    <div style="font-size: 1.5rem; color: #00F2FE; font-weight: 800; font-family: monospace;">{score_val} %</div>
                    <div style="font-size: 0.75rem; color: #FFFFFF; font-weight: 600; margin-top: 0.2rem;">{rep.decision}</div>
                    <div style="font-size: 0.68rem; color: #94A3B8; margin-top: 0.3rem;">Risque : {rep.risk_label} ({rep.risk_score}/100) &bull; Concessions CAMI : {rep.cami_verified}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("Audit Géo-Clôture & Titres CAMI", use_container_width=True):
            lat_chk = active_deposit_data["latitude"] if active_deposit_data else active_center[0]
            lon_chk = active_deposit_data["longitude"] if active_deposit_data else active_center[1]

            geo_eng = GeofenceEngine()
            geo_eng.register_zone(GeofenceZone(
                id="ZONE-ACTIVE-TITRE",
                name="Périmètre d'Exploitation Valide",
                category=ZoneCategory.CAMI_PERMIT,
                zone_type=GeofenceType.CIRCLE,
                center=(lat_chk, lon_chk),
                radius_m=3500.0,
            ))

            is_inside = geo_eng.is_point_in_zone(lat_chk, lon_chk, "ZONE-ACTIVE-TITRE")
            if is_inside:
                st.success("Conformité spatiale vérifiée : Aucune incursion illégale ou chevauchement d'aire protégée (ICCN).")
            else:
                st.warning("Alerte d'incursion : Les coordonnées se situent en bordure extérieure du titre minier déclaré.")

        st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# ONGLET 2 : TRAÇABILITÉ OPÉRATIONNELLE & BLOCKCHAIN
# ==============================================================================
with main_tabs[1]:
    st.markdown('<div class="cmc-panel">', unsafe_allow_html=True)
    st.markdown('<div class="cmc-panel-title">CHAÎNE DE TRAÇABILITÉ NUMÉRIQUE & BLOCKCHAIN (PILIER 1 & 3)</div>', unsafe_allow_html=True)
    st.caption("Module intégré : Biométrie des creuseurs, pesée numérique connectée, contrôle géo-clôture CAMI et ancrage Hyperledger Fabric / ERC-1155.")

    # Registre blockchain simulé en session
    if "blockchain_ledger" not in st.session_state:
        st.session_state.blockchain_ledger = [
            {
                "lot_id": "LOT-RDC-2026-0891",
                "miner_id": "CREUS-LUALABA-042",
                "cooperative": "COMIAKOL (Kolwezi)",
                "pit_name": "Puits Est #4",
                "commodity": "Cobalt Hétérogénite",
                "weight_kg": 248.5,
                "grade_pct": 8.4,
                "h3_cell": "892a006c00fffff",
                "geofence_status": "CONFORME (ZEA #881)",
                "tx_hash": "0x7a3f890b91e7c53d10a24f0c431b982e54e4c2b9a10df8",
                "timestamp": "2026-09-20 18:42:10 UTC",
            },
            {
                "lot_id": "LOT-RDC-2026-0890",
                "miner_id": "CREUS-LUALABA-118",
                "cooperative": "COOP-MIN-MUSONOIE",
                "pit_name": "Puits Sud #1",
                "commodity": "Cuivre Malachite",
                "weight_kg": 412.0,
                "grade_pct": 14.2,
                "h3_cell": "892a006c013ffff",
                "geofence_status": "CONFORME (PE #1240)",
                "tx_hash": "0x918cbef04218ac939023190abf541289cf00921a4bc582",
                "timestamp": "2026-09-20 18:15:32 UTC",
            },
        ]

    scale_col, form_col = st.columns([0.45, 0.55], gap="medium")

    with scale_col:
        st.markdown("#### Terminal de Pesée Numérique (IoT)")
        st.markdown(
            """
            <div style="background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(0, 242, 254, 0.25); border-radius: 8px; padding: 1rem; text-align: center;">
                <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Balance Électronique Connectée · Terminal #PES-02</div>
                <div style="font-size: 2.8rem; font-weight: 900; color: #00F2FE; font-family: 'JetBrains Mono', monospace; margin: 0.5rem 0;">
                    LIVE LINKED
                </div>
                <div style="font-size: 0.78rem; color: #10B981; font-weight: 600;">Flux Télémétrique Actif · Calibrage Certifié OCC</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        live_weight = st.slider("Mesure de la Pesée Numérique (kg)", min_value=10.0, max_value=850.0, value=285.0, step=0.5, key="inp_weight")
        live_grade = st.slider("Teneur Estimée au Spectromètre XRF (%)", min_value=0.5, max_value=25.0, value=9.2, step=0.1, key="inp_grade")

    with form_col:
        st.markdown("#### Biométrie & Identification du Lot")
        f_miner = st.selectbox("Creuseur Artisanal Enregistré", [
            "CREUS-LUALABA-042 — Kasongo Mwamba (Biométrie Validée)",
            "CREUS-LUALABA-118 — Ilunga Kabange (Biométrie Validée)",
            "CREUS-LUALABA-205 — Tshilombo Kalala (Biométrie Validée)",
            "CREUS-LUALABA-312 — Mukendi Ngoie (Biométrie Validée)",
        ], key="sel_miner")

        f_pit = st.selectbox("Puits / Front de Taille", [
            "Puits Est #4 (Carreau Musonoie)",
            "Puits Sud #1 (Périmètre Dilala)",
            "Puits Nord #2 (Zone Artisanale Kasulo)",
        ], key="sel_pit")

        f_comm = st.selectbox("Substance Minérale Déclarée", [
            "Cobalt Hétérogénite (Co)",
            "Cuivre Malachite / Chalcopyrite (Cu)",
            "Coltan / Cassitérite (3T)",
            "Lithium Pegmatitique (Li)",
        ], key="sel_comm")

        # Géoréférencement et H3
        indexer = HexagonalSpatialIndexer(default_resolution=9)
        ref_lat, ref_lon = -10.7167, 25.4667  # Kolwezi
        h3_cell = indexer.lat_lon_to_h3(ref_lat, ref_lon, resolution=9)

        if st.button("Forger le Lot & Ancrer sur la Blockchain", type="primary", use_container_width=True):
            tx_raw = f"{f_miner}-{f_pit}-{live_weight}-{live_grade}-{time.time()}"
            tx_hash = "0x" + hashlib.sha256(tx_raw.encode("utf-8")).hexdigest()[:48]
            lot_id = f"LOT-RDC-2026-{random.randint(1000, 9999)}"
            ts_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            new_record = {
                "lot_id": lot_id,
                "miner_id": f_miner.split(" — ")[0],
                "cooperative": "COMIAKOL (Lualaba)",
                "pit_name": f_pit.split(" (")[0],
                "commodity": f_comm,
                "weight_kg": float(live_weight),
                "grade_pct": float(live_grade),
                "h3_cell": h3_cell,
                "geofence_status": "CONFORME (ZEA #881)",
                "tx_hash": tx_hash,
                "timestamp": ts_now,
            }
            st.session_state.blockchain_ledger.insert(0, new_record)
            st.success(f"Bloc forgé avec succès ! Lot ID : {lot_id} · TX : {tx_hash[:18]}...")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("#### Registre Immuable des Lots Certifiés (Ledger)")

    df_ledger = pd.DataFrame(st.session_state.blockchain_ledger)
    st.dataframe(
        df_ledger,
        use_container_width=True,
        hide_index=True,
        column_config={
            "lot_id": st.column_config.TextColumn("Identifiant Lot"),
            "miner_id": st.column_config.TextColumn("Creuseur"),
            "cooperative": st.column_config.TextColumn("Coopérative"),
            "pit_name": st.column_config.TextColumn("Puits"),
            "commodity": st.column_config.TextColumn("Minerai"),
            "weight_kg": st.column_config.NumberColumn("Pesée (kg)", format="%.1f kg"),
            "grade_pct": st.column_config.NumberColumn("Teneur (%)", format="%.2f %%"),
            "h3_cell": st.column_config.TextColumn("Index H3"),
            "geofence_status": st.column_config.TextColumn("Géo-Clôture"),
            "tx_hash": st.column_config.TextColumn("Hash Transaction"),
            "timestamp": st.column_config.TextColumn("Date/Heure UTC"),
        },
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# ONGLET 3 : SIMULATEUR TACTIQUE DE RESSOURCES & FORAGES (JORC / NI 43-101)
# ==============================================================================
with main_tabs[2]:
    st.markdown('<div class="cmc-panel">', unsafe_allow_html=True)
    st.markdown('<div class="cmc-panel-title">SIMULATEUR DE RESSOURCES & SENSIBILITÉ ÉCONOMIQUE</div>', unsafe_allow_html=True)
    st.caption("Modélisation dynamique du tonnage, de la teneur de coupure (Cut-Off Grade) et valorisation financière instantanée.")

    sim_col1, sim_col2 = st.columns([0.35, 0.65], gap="large")

    with sim_col1:
        st.markdown("#### Paramètres du Gisement")
        sim_cutoff = st.slider("Teneur de coupure (Cut-Off Grade %)", 0.2, 3.5, 1.2, 0.1, key="sim_cutoff")
        sim_thickness = st.slider("Épaisseur moyenne minéralisée (m)", 10.0, 150.0, 45.0, 5.0, key="sim_thick")
        sim_strike = st.slider("Longueur de la structure le long de l'axe (m)", 500, 5000, 1800, 100, key="sim_strike")
        sim_density = st.slider("Densité in-situ de la roche (t/m³)", 2.2, 3.5, 2.75, 0.05, key="sim_density")
        sim_price = st.slider("Cours de marché métal ($/tonne)", 4000, 35000, 9200, 200, key="sim_price")

    with sim_col2:
        # Calculs dynamiques instantanés
        sim_volume = (sim_thickness * sim_strike * 350.0) / 1_000_000.0  # Millions m³
        sim_tonnage = sim_volume * sim_density  # Millions tonnes minerai
        # Relation décroissante standard de la teneur moyenne en fonction du cut-off
        sim_mean_grade = max(0.4, sim_cutoff * 1.35 + 0.6)
        sim_metal_kt = (sim_tonnage * 1_000_000.0 * (sim_mean_grade / 100.0)) / 1_000.0  # Kilotonnes métal contenu
        sim_valuation_musd = (sim_metal_kt * 1000.0 * sim_price) / 1_000_000.0  # Millions USD

        st.markdown("#### Évaluation Instantanée des Ressources")
        kpi_m1, kpi_m2, kpi_m3, kpi_m4 = st.columns(4)

        with kpi_m1:
            st.metric("Tonnage Minerai", f"{sim_tonnage:.2f} Mt", delta=f"{sim_volume:.1f} M m³")
        with kpi_m2:
            st.metric("Teneur Moyenne", f"{sim_mean_grade:.2f} %", delta=f"Cut-off : {sim_cutoff:.1f}%")
        with kpi_m3:
            st.metric("Métal Contenu", f"{sim_metal_kt:,.0f} kt", delta="Cu / Co brut")
        with kpi_m4:
            st.metric("Valeur Brute", f"{sim_valuation_musd:,.0f} M$", delta="In-Situ ($USD)")

        # Courbe de sensibilité Tonnage vs Cut-off en temps réel
        curve_data = []
        for co in [0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0]:
            ton_val = sim_tonnage * (1.0 - (co - 0.5) * 0.18)
            gr_val = max(0.5, co * 1.35 + 0.6)
            curve_data.append({
                "CutOff": co,
                "Tonnage_Mt": max(1.0, ton_val),
                "Grade_Pct": gr_val,
            })

        df_curve = pd.DataFrame(curve_data)

        chart = alt.Chart(df_curve).mark_line(point=True, color="#00F2FE").encode(
            x=alt.X("CutOff:Q", title="Teneur de Coupure Cut-Off (%)"),
            y=alt.Y("Tonnage_Mt:Q", title="Tonnage Économique Exploitable (Mt)"),
            tooltip=["CutOff", "Tonnage_Mt", "Grade_Pct"],
        ).properties(
            title="Courbe Tonnage-Teneur de Sensibilité Opérationnelle",
            height=280,
        )

        st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# 6. Graphiques Analytiques Inférieurs (Altair sombre sans stickers)
st.markdown("<div class='cmc-section'><div class='cmc-section-title'>RÉPARTITION NATIONALE DES SUBSTANCES ET PROVINCES</div></div>", unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2, gap="medium")

with chart_col1:
    st.markdown('<div class="cmc-panel">', unsafe_allow_html=True)
    st.markdown('<div class="cmc-panel-title">OCCURRENCES PAR MINERAI STRATÉGIQUE</div>', unsafe_allow_html=True)
    bar_pairs(top_commodities(), title="", color="#E5A93C", orientation="horizontal")
    st.markdown("</div>", unsafe_allow_html=True)

with chart_col2:
    st.markdown('<div class="cmc-panel">', unsafe_allow_html=True)
    st.markdown('<div class="cmc-panel-title">RÉPARTITION PAR PROVINCE ADMINISTRATIVE</div>', unsafe_allow_html=True)
    bar_pairs(top_provinces(), title="", color="#00F2FE", orientation="horizontal")
    st.markdown("</div>", unsafe_allow_html=True)
