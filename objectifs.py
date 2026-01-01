import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
from io import BytesIO

# ------------------------
# SUPABASE CLIENT
# ------------------------
SUPABASE_URL = "https://pvjdgddzuzarygaxyxuw.supabase.co"
SUPABASE_KEY = "sb_publishable_ilPGwOE_zkgfeqp-PosqPA_7mxrgfbF"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------
# FONCTION PRINCIPALE
# ------------------------
def run_objectifs():
    st.subheader("🎯 Objectifs et indicateurs calculés")

    # Récupérer les données
    records = supabase.table("indicateurs_cliniques").select("*").execute().data
    df = pd.DataFrame(records)

    if df.empty:
        st.info("Aucune donnée disponible pour calculer les objectifs")
        return

    # ------------------------
    # CALCUL DES INDICATEURS
    # ------------------------

    # 1️⃣ Taux d'incidents
    df["taux_incidents"] = df["incident"].apply(lambda x: 1 if x == "Oui" else 0)
    taux_moyen_incidents = df["taux_incidents"].mean()

    # 2️⃣ Taux de réadmissions
    df["taux_readmission"] = df["readmission"].apply(lambda x: 1 if x == "Oui" else 0)
    taux_moyen_readmission = df["taux_readmission"].mean()

    # 3️⃣ Taux d'échec de traitement
    df["taux_echec"] = df["echec_traitement"].apply(lambda x: 1 if x == "Oui" else 0)
    taux_moyen_echec = df["taux_echec"].mean()

    # 4️⃣ Satisfaction moyenne
    satisfaction_moyenne = df["satisfaction_patient"].mean()

    # Ajouter ici d'autres indicateurs selon tes formules
    # Exemple : df["taux_rechute"] = df["rechute"].apply(lambda x: 1 if x == "Oui" else 0)

    # ------------------------
    # AFFICHAGE DES KPI
    # ------------------------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Taux moyen d'incidents", f"{taux_moyen_incidents:.2%}")
    col2.metric("Taux moyen de réadmissions", f"{taux_moyen_readmission:.2%}")
    col3.metric("Taux moyen d'échec de traitement", f"{taux_moyen_echec:.2%}")
    col4.metric("Satisfaction moyenne", f"{satisfaction_moyenne:.1f}/5")

    st.divider()

    # ------------------------
    # GRAPHIQUES
    # ------------------------
    st.subheader("📊 Graphiques des indicateurs")

    # Histogramme incidents
    fig_incidents = px.histogram(df, x="taux_incidents", title="Distribution des incidents", nbins=2)
    st.plotly_chart(fig_incidents, use_container_width=True)

    # Histogramme réadmissions
    fig_readm = px.histogram(df, x="taux_readmission", title="Distribution des réadmissions", nbins=2)
    st.plotly_chart(fig_readm, use_container_width=True)

    # Histogramme satisfaction
    fig_satisf = px.histogram(df, x="satisfaction_patient", title="Distribution de la satisfaction", nbins=5)
    st.plotly_chart(fig_satisf, use_container_width=True)

    st.divider()

    # ------------------------
    # TABLEAU RÉSUMÉ
    # ------------------------
    st.subheader("🗂️ Tableau récapitulatif")
    summary = df[[
        "patient_first_name", "patient_last_name", "incident", "readmission",
        "echec_traitement", "satisfaction_patient"
    ]]
    st.dataframe(summary, use_container_width=True)

    # ------------------------
    # EXPORT EXCEL
    # ------------------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        summary.to_excel(writer, index=False, sheet_name="Objectifs")
    st.download_button(
        label="⬇️ Télécharger les indicateurs",
        data=output.getvalue(),
        file_name="indicateurs_objectifs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
