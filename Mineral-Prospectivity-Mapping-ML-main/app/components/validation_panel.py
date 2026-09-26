import streamlit as st

def render_validation_panel(zone: str, score: float):
    """
    Rendu du composant de boucle de validation par les géologues (Expert Validation Loop).
    """
    st.markdown("---")
    st.subheader("Validation Expert (SGN-C)")
    st.caption("Protocole d'arbitrage géologique et boucle d'apprentissage supervisé.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Pertinent (Cible confirmée)", key=f"val_pert_{zone}_{score}"):
            st.success("Feedback enregistré : Échantillon positif calibré pour le modèle GeoAI.")
    with col2:
        if st.button("À vérifier (Travaux sol requis)", key=f"val_verif_{zone}_{score}"):
            st.warning("Feedback enregistré : Statut transmis aux équipes de terrain.")
    with col3:
        if st.button("Faux positif (Rejet géologique)", key=f"val_fp_{zone}_{score}"):
            st.error("Feedback enregistré : Signature écartée pour le réentraînement.")
            
    comment = st.text_input("Commentaire géologique", placeholder="Ex: Anomalie probablement liée à une structure connue...")
    if st.button("Soumettre le commentaire"):
        st.toast("Commentaire ajouté au dataset d'apprentissage.")
