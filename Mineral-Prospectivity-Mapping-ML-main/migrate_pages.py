import os
import shutil

pages_dir = "app/pages"
legacy_dir = "app/legacy_pages"

if not os.path.exists(legacy_dir):
    os.makedirs(legacy_dir)

# Move all existing .py files to legacy
for f in os.listdir(pages_dir):
    if f.endswith(".py") and f != "__init__.py":
        src = os.path.join(pages_dir, f)
        dst = os.path.join(legacy_dir, f)
        shutil.move(src, dst)

# Create a helper module to run legacy pages
with open("app/legacy_runner.py", "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
import os

def run_legacy_page(filename, active_page_name):
    path = os.path.join("app", "legacy_pages", filename)
    if not os.path.exists(path):
        st.warning(f"Fichier non trouvé : {filename}")
        return
        
    with open(path, "r", encoding="utf-8") as file:
        code = file.read()
        
    # Patch bootstrap to not call set_page_config
    import app.shell
    original_bootstrap = app.shell.bootstrap
    
    def mocked_bootstrap(page_title, active_page=None):
        return original_bootstrap(page_title, active_page=active_page_name)
        
    app.shell.bootstrap = mocked_bootstrap
    
    try:
        # Patch st.set_page_config
        original_spc = st.set_page_config
        st.set_page_config = lambda *args, **kwargs: None
        
        # Execute the page code in a separate namespace
        namespace = {'__name__': '__main__'}
        exec(code, namespace)
    except Exception as e:
        st.error(f"Erreur d'exécution de {filename}: {e}")
    finally:
        app.shell.bootstrap = original_bootstrap
        st.set_page_config = original_spc
""")

# Page 1: Dashboard
with open(os.path.join(pages_dir, "01_Dashboard.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Tableau de Bord National", active_page="01_Dashboard")

tabs = st.tabs(["🌍 Vue Nationale", "🗺️ Explorateur de zones", "👥 Démographie"])

with tabs[0]:
    run_legacy_page("02_Carte_miniere.py", "01_Dashboard")
with tabs[1]:
    run_legacy_page("21_Explorateur_zones.py", "01_Dashboard")
with tabs[2]:
    run_legacy_page("09_Demographie.py", "01_Dashboard")
""")

# Page 2: Cadastre & Projets
with open(os.path.join(pages_dir, "02_Cadastre_Projects.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Cadastre & Projets", active_page="02_Cadastre_Projects")
tabs = st.tabs(["📋 Cadastre", "⛏️ Sites Miniers", "🏗️ Projets"])

with tabs[0]:
    run_legacy_page("05_Cadastre_minier.py", "02_Cadastre_Projects")
with tabs[1]:
    run_legacy_page("04_Sites_miniers.py", "02_Cadastre_Projects")
with tabs[2]:
    run_legacy_page("11_Projets_miniers.py", "02_Cadastre_Projects")
""")

# Page 3: Prospectivité IA
with open(os.path.join(pages_dir, "03_Prospectivite_IA.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Prospectivité IA", active_page="03_Prospectivite_IA")
tabs = st.tabs(["🧠 Modèle Prédictif", "🗺️ Analyse Géospatiale"])

with tabs[0]:
    run_legacy_page("07_Potentiel_mineral_IA.py", "03_Prospectivite_IA")
with tabs[1]:
    run_legacy_page("06_Analyse_geospatiale.py", "03_Prospectivite_IA")
""")

# Page 4: Modèles 3D
with open(os.path.join(pages_dir, "04_Modeles_3D.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Modèles 3D", active_page="04_Modeles_3D")
run_legacy_page("20_Geo_Model_3D.py", "04_Modeles_3D")
""")

# Page 5: Incertitudes
with open(os.path.join(pages_dir, "05_Incertitudes.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Incertitudes & Limites", active_page="05_Incertitudes")
run_legacy_page("22_Incertitude.py", "05_Incertitudes")
""")

# Page 6: Exploration
with open(os.path.join(pages_dir, "06_Exploration.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Campagnes d'Exploration", active_page="06_Exploration")
tabs = st.tabs(["🎯 Cibles", "📍 Forages", "🔬 Smart Sampling", "📅 Historique", "🛠️ Campagne"])

with tabs[0]:
    run_legacy_page("18_Cibles.py", "06_Exploration")
with tabs[1]:
    run_legacy_page("19_Drillholes.py", "06_Exploration")
with tabs[2]:
    run_legacy_page("23_Smart_Sampling.py", "06_Exploration")
with tabs[3]:
    run_legacy_page("24_Historique_campagnes.py", "06_Exploration")
with tabs[4]:
    run_legacy_page("17_Campagne_exploration.py", "06_Exploration")
""")

# Page 7: Environnement & Risques
with open(os.path.join(pages_dir, "07_Environment_Risks.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Environnement & Risques", active_page="07_Environment_Risks")
run_legacy_page("08_Risques_environnement.py", "07_Environment_Risks")
""")

# Page 8: Données & Administration
with open(os.path.join(pages_dir, "08_Data_Admin.py"), "w", encoding="utf-8") as f:
    f.write("""
import streamlit as st
from app.legacy_runner import run_legacy_page
from app.shell import bootstrap

filters = bootstrap("Données, Rapports & Admin", active_page="08_Data_Admin")
tabs = st.tabs(["📊 Comparateur", "📑 Rapports Export", "🗄️ Sources", "🔌 Data API Hub", "⚖️ Décision", "⚙️ Administration"])

with tabs[0]:
    run_legacy_page("10_Comparateur.py", "08_Data_Admin")
with tabs[1]:
    run_legacy_page("12_Rapports_export.py", "08_Data_Admin")
with tabs[2]:
    run_legacy_page("13_Donnees_sources.py", "08_Data_Admin")
with tabs[3]:
    run_legacy_page("15_Data_API_Hub.py", "08_Data_Admin")
with tabs[4]:
    run_legacy_page("16_Decision.py", "08_Data_Admin")
with tabs[5]:
    run_legacy_page("14_Administration.py", "08_Data_Admin")
""")

print("Refactor complete! Created 8 pages grouping the legacy pages.")
