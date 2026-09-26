import os

pages_dir = "app/pages"

# 1. Tableau de bord
with open(os.path.join(pages_dir, "01_Tableau_de_bord.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Tableau de bord", active_page="01_Tableau_de_bord")

run_legacy_page("02_Carte_miniere.py", "01_Tableau_de_bord")

with st.expander("Couches Démographiques", expanded=False):
    run_legacy_page("09_Demographie.py", "01_Tableau_de_bord")
""")

# 2. Modélisation & IA
with open(os.path.join(pages_dir, "02_Modelisation_IA.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Modélisation & IA", active_page="02_Modelisation_IA")

mode = st.radio(
    "Sélectionnez le mode de visualisation analytique :",
    ["🗺️ Carte Prédictive 2D (XAI)", "🧊 Jumeau Numérique 3D", "⚖️ Évaluation des Incertitudes"],
    horizontal=True
)

st.markdown("---")

if "Carte Prédictive" in mode:
    run_legacy_page("07_Potentiel_mineral_IA.py", "02_Modelisation_IA")
elif "Jumeau Numérique" in mode:
    run_legacy_page("20_Geo_Model_3D.py", "02_Modelisation_IA")
else:
    run_legacy_page("22_Incertitude.py", "02_Modelisation_IA")
""")

# 3. Gestion du territoire
with open(os.path.join(pages_dir, "03_Gestion_du_territoire.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Gestion du territoire", active_page="03_Gestion_du_territoire")

tabs = st.tabs(["📋 Registre Foncier", "🎯 Opérations Terrain", "⚠️ Risques Environnementaux"])

with tabs[0]:
    run_legacy_page("05_Cadastre_minier.py", "03_Gestion_du_territoire")
    st.markdown("---")
    st.subheader("Sites Miniers Existants")
    run_legacy_page("04_Sites_miniers.py", "03_Gestion_du_territoire")
    st.markdown("---")
    st.subheader("Projets en Développement")
    run_legacy_page("11_Projets_miniers.py", "03_Gestion_du_territoire")

with tabs[1]:
    run_legacy_page("17_Campagne_exploration.py", "03_Gestion_du_territoire")
    st.markdown("---")
    run_legacy_page("18_Cibles.py", "03_Gestion_du_territoire")
    st.markdown("---")
    run_legacy_page("19_Drillholes.py", "03_Gestion_du_territoire")
    with st.expander("Recommandations d'Échantillonnage", expanded=False):
        run_legacy_page("23_Smart_Sampling.py", "03_Gestion_du_territoire")
    with st.expander("Historique des Campagnes", expanded=False):
        run_legacy_page("24_Historique_campagnes.py", "03_Gestion_du_territoire")

with tabs[2]:
    run_legacy_page("08_Risques_environnement.py", "03_Gestion_du_territoire")
""")

# 4. Administration
with open(os.path.join(pages_dir, "04_Administration.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Administration", active_page="04_Administration")
tabs = st.tabs(["📊 Business Intelligence", "🗄️ Intégration Data (Datawarehouse)", "⚙️ Système"])

with tabs[0]:
    run_legacy_page("10_Comparateur.py", "04_Administration")
    st.markdown("---")
    run_legacy_page("16_Decision.py", "04_Administration")
    with st.expander("Exports et Rapports PDF", expanded=False):
        run_legacy_page("12_Rapports_export.py", "04_Administration")

with tabs[1]:
    st.info("Le Datawarehouse et la passerelle SGN-C (BNDG) tournent en arrière-plan comme source de vérité.")
    run_legacy_page("15_Data_API_Hub.py", "04_Administration")
    with st.expander("Détails des sources brutes", expanded=False):
        run_legacy_page("13_Donnees_sources.py", "04_Administration")

with tabs[2]:
    run_legacy_page("14_Administration.py", "04_Administration")
""")

print("Successfully refactored into the 4 ultimate hubs!")
