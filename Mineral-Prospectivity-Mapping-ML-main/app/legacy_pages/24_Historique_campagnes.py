"""24 — Historique des campagnes d'exploration."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.empty_state import render_demo_notice
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from compass_core.exploration.campaign import run_campaign
from compass_core.exploration.history import (
    campaign_summary,
    list_campaigns,
    load_campaign,
    save_campaign,
    update_target_outcome,
)
from compass_core.prospectivity.prediction import ZONE_PRESETS

filters = bootstrap("Historique campagnes", active_page="Historique")
masthead(
    "Historique d'exploration",
    "Conserver les campagnes et les sorts des cibles pour éviter de refaire les mêmes travaux.",
    sources="outputs/campaigns/",
)
render_demo_notice("Historique fichier local — pas un ERP minier.")

render_section("Nouvelle entrée")
c1, c2 = st.columns(2)
zone = c1.selectbox("Zone", list(ZONE_PRESETS.keys()), index=0)
mineral = c2.selectbox("Minerai", ["cuivre", "cobalt", "lithium", "or"], index=0)
if st.button("Lancer & enregistrer une campagne", type="primary"):
    camp = run_campaign(zone=zone, mineral=mineral, max_targets=8)
    entry = save_campaign(camp.to_dict(), status="ouverte", note="Créée depuis l'UI Historique")
    st.session_state["history_last"] = entry.to_dict()
    st.success(f"Enregistré : {entry.campaign_id}")

render_section("Campagnes enregistrées")
items = list_campaigns()
if not items:
    st.info("Aucune campagne en historique. Enregistrer depuis cette page ou depuis Campagne exploration.")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "ID": i["campaign_id"],
                    "Zone": i.get("zone"),
                    "Minerai": i.get("mineral"),
                    "Cibles": i.get("n_targets"),
                    "Top": i.get("top_target_id"),
                    "Score": i.get("top_score"),
                    "Lacunes": i.get("n_gaps"),
                    "Statut": i.get("status"),
                }
                for i in items
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    ids = [i["campaign_id"] for i in items]
    sel = st.selectbox("Détail campagne", ids)
    summary = campaign_summary(sel)
    st.json(summary)

    camp = load_campaign(sel)
    targets = (camp or {}).get("targets") or []
    if targets:
        render_section("Mettre à jour le sort d'une cible")
        tid = st.selectbox("Cible", [t["target_id"] for t in targets])
        outcome = st.selectbox("Résultat", ["confirmé", "abandonné", "approfondir", "en_cours"])
        if st.button("Enregistrer le résultat"):
            updated = update_target_outcome(sel, tid, outcome)
            if updated:
                st.success(f"{tid} → {outcome}")
                st.json(updated.get("outcomes"))

_ = filters
close_page()
