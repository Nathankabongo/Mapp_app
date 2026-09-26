import sys
from pathlib import Path
import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

st.set_page_config(
    page_title="CriticalMineralsCompass RDC",
    page_icon=":material/radar:",
    layout="wide",
    initial_sidebar_state="expanded",
)

p1 = st.Page("views/01_Tableau_de_bord.py", title="Tableau de bord", icon=":material/dashboard:")
p2 = st.Page("views/02_Modelisation_IA.py", title="Modélisation & IA", icon=":material/analytics:")
p3 = st.Page("views/03_Gestion_du_territoire.py", title="Gestion du territoire", icon=":material/layers:")
p4 = st.Page("views/04_Administration.py", title="Administration", icon=":material/settings:")

pg = st.navigation([p1, p2, p3, p4])
pg.run()
