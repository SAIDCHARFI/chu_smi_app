import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.express as px

# Supabase client (tu peux réutiliser les mêmes clés que dans run_app.py)
SUPABASE_URL = "https://pvjdgddzuzarygaxyxuw.supabase.co"
SUPABASE_KEY = "sb_publishable_ilPGwOE_zkgfeqp-PosqPA_7mxrgfbF"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def run_objectifs():
    st.subheader("🎯 Objectifs et indicateurs calculés")

    # Récupération des données
    records = supabase.table("indicateurs_cliniques").select("*").execute().data
    df_db = pd.DataFrame(records)

    if df_db.empty:
        st.info("Aucune donnée disponible pour calculer les objectifs")
        return

    # ------------------------
    # CALCUL DES INDICATEURS
    # ------------------------
    # Exemple : calcul taux incidents
    df_db["taux_incidents"] = df_db["incident"].apply(lambda x: 1 if x == "Oui" else 0)
    taux_moyen_incidents = df_db["taux_incidents"].mean()

    st.metric("Taux moyen d’incidents", f"{taux_moyen_incidents:.2%}")

    # Ici tu pourras ajouter toutes tes autres formules
    # st.write(df_db)  # pour debug ou afficher tableau complet

    # Exemple de graphique
    fig = px.histogram(df_db, x="taux_incidents", title="Distribution des incidents")
    st.plotly_chart(fig, use_container_width=True)
