
import streamlit as st
import os

def run_legacy_page(filename, active_page_name):
    path = os.path.join("app", "legacy_pages", filename)
    if not os.path.exists(path):
        st.warning(f"Fichier non trouvé : {filename}")
        return
        
    with open(path, "r", encoding="utf-8") as file:
        code = file.read()
        
    # Patch bootstrap to not call set_page_config and not duplicate sidebar widgets
    import app.shell
    original_bootstrap = app.shell.bootstrap
    
    def mocked_bootstrap(page_title, active_page=None):
        # Ne pas appeler le vrai bootstrap pour éviter les widgets dupliqués.
        # Retourner simplement les filtres de la session s'ils existent.
        if "filters" in st.session_state:
            return st.session_state.filters
        return {"province": "Toutes", "minerai": []}
        
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
