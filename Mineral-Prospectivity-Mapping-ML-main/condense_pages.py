import os

pages_dir = "app/pages"

# 1. Dashboard
with open(os.path.join(pages_dir, "01_Dashboard.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Tableau de Bord National", active_page="01_Dashboard")

# Vue unifiée
run_legacy_page("02_Carte_miniere.py", "01_Dashboard")

with st.expander("Couches Démographiques & Explorateur de Zones", expanded=False):
    run_legacy_page("09_Demographie.py", "01_Dashboard")
""")

# 2. Cadastre & Projects
with open(os.path.join(pages_dir, "02_Cadastre_Projects.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Cadastre & Projets", active_page="02_Cadastre_Projects")
tabs = st.tabs(["📋 Registre Foncier (Cadastre & Sites)", "🏗️ Projets en Développement"])

with tabs[0]:
    run_legacy_page("05_Cadastre_minier.py", "02_Cadastre_Projects")
    st.markdown("---")
    st.subheader("Sites Miniers Existants")
    run_legacy_page("04_Sites_miniers.py", "02_Cadastre_Projects")
with tabs[1]:
    run_legacy_page("11_Projets_miniers.py", "02_Cadastre_Projects")
""")

# 3. Prospectivité IA
with open(os.path.join(pages_dir, "03_Prospectivite_IA.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Prospectivité IA", active_page="03_Prospectivite_IA")

# Interface unifiée (Zéro onglet)
run_legacy_page("07_Potentiel_mineral_IA.py", "03_Prospectivite_IA")
""")

# 6. Exploration
with open(os.path.join(pages_dir, "06_Exploration.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Campagnes d'Exploration", active_page="06_Exploration")
tabs = st.tabs(["📅 Planification & Historique", "🎯 Opérations Terrain (Cibles & Forages)"])

with tabs[0]:
    run_legacy_page("17_Campagne_exploration.py", "06_Exploration")
    st.markdown("---")
    with st.expander("Consulter l'historique complet", expanded=False):
        run_legacy_page("24_Historique_campagnes.py", "06_Exploration")
with tabs[1]:
    run_legacy_page("18_Cibles.py", "06_Exploration")
    st.markdown("---")
    run_legacy_page("19_Drillholes.py", "06_Exploration")
    with st.expander("Recommandations d'Échantillonnage (Smart Sampling)", expanded=False):
        run_legacy_page("23_Smart_Sampling.py", "06_Exploration")
""")

# 8. Data Admin
with open(os.path.join(pages_dir, "08_Data_Admin.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
import time
from compass_core.connectors.sgnc_bndg import SgncBndgConnector
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Données, Rapports & Admin", active_page="08_Data_Admin")
tabs = st.tabs(["🔌 Intégration & SGN-C", "📊 Business Intelligence", "⚙️ Paramètres Système"])

with tabs[0]:
    st.subheader("Passerelle Sécurisée BNDG (SGN-C)")
    st.markdown("Interface d'intégration et de validation des données géoscientifiques nationales.")
    
    if "bndg_connector" not in st.session_state:
        st.session_state.bndg_connector = SgncBndgConnector()
        
    if not st.session_state.bndg_connector.is_connected:
        st.info("Statut : Déconnecté")
        api_key = st.text_input("Clé d'API SGN-C", type="password")
        if st.button("Authentification"):
            with st.spinner("Connexion sécurisée en cours..."):
                time.sleep(1)
                st.session_state.bndg_connector.authenticate()
                st.success("Connecté à la BNDG avec succès.")
                st.rerun()
    else:
        st.success("✅ Connecté au réseau BNDG")
        if st.button("Déconnexion"):
            st.session_state.bndg_connector.is_connected = False
            st.rerun()
            
        catalog = st.session_state.bndg_connector.get_data_catalog()
        for record in catalog:
            with st.expander(f"📄 {record.name} ({record.category})"):
                st.write(f"**ID:** {record.dataset_id}")
                st.write(f"**Résolution:** {record.resolution}")
                st.write(f"**Qualité Globale:** {record.quality.global_score()}/100")
                if st.button(f"Intégrer au moteur", key=f"btn_{record.dataset_id}"):
                    st.toast(f"Données de {record.dataset_id} validées et prêtes.")
                    
    st.markdown("---")
    st.subheader("Data API & Sources")
    run_legacy_page("15_Data_API_Hub.py", "08_Data_Admin")
    with st.expander("Détails des sources brutes", expanded=False):
        run_legacy_page("13_Donnees_sources.py", "08_Data_Admin")

with tabs[1]:
    run_legacy_page("10_Comparateur.py", "08_Data_Admin")
    st.markdown("---")
    run_legacy_page("16_Decision.py", "08_Data_Admin")
    with st.expander("Exports et Rapports PDF", expanded=False):
        run_legacy_page("12_Rapports_export.py", "08_Data_Admin")

with tabs[2]:
    run_legacy_page("14_Administration.py", "08_Data_Admin")
""")

print("Condensation of sub-pages complete!")
