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
    st.subheader("🎯 Objectifs & Indicateurs Cliniques")

    # ------------------------
    # CHARGEMENT DES DONNÉES
    # ------------------------
    records = supabase.table("indicateurs_cliniques").select("*").execute().data
    if not records:
        st.info("Aucune donnée disponible pour calculer les indicateurs.")
        return

    df = pd.DataFrame(records)

    # Sécurisation dates
    df["registration_time"] = pd.to_datetime(
        df["registration_time"],
        errors="coerce"
    )
    df = df.dropna(subset=["registration_time"])

    # ------------------------
    # FILTRES
    # ------------------------
    st.markdown("### 🔎 Filtres")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Date début",
            df["registration_time"].min().date()
        )
    with col2:
        end_date = st.date_input(
            "Date fin",
            df["registration_time"].max().date()
        )

    service_filter = st.text_input(
        "Service (laisser vide pour tous)"
    )

    df_filtered = df[
        (df["registration_time"].dt.date >= start_date)
        & (df["registration_time"].dt.date <= end_date)
    ]

    if service_filter:
        df_filtered = df_filtered[
            df_filtered["patient_service"]
            .str.contains(service_filter, case=False, na=False)
        ]

    if df_filtered.empty:
        st.warning("Aucune donnée pour ces filtres.")
        return

    # ------------------------
    # CALCUL DES INDICATEURS
    # ------------------------
    total_patients = len(df_filtered)

    df_filtered["nb_incidents"] = df_filtered["nb_incidents"].fillna(0)

    nb_incidents = df_filtered["nb_incidents"].sum()
    nb_ias = (df_filtered["infection_soins"] == "Oui").sum()
    nb_readmission = (df_filtered["readmission"] == "Oui").sum()
    nb_dossiers_complets = (df_filtered["dossier_complet"] == "Oui").sum()
    nb_effets_graves = (df_filtered["effets_graves"] == "Oui").sum()
    delai_moyen = df_filtered["delai_admission"].mean()
    nb_diag_ok = (df_filtered["diagnostic_etabli"] == "Oui").sum()
    nb_plaintes = (df_filtered["plaintes_reclamations"] == "Oui").sum()

    nb_remission = (df_filtered["evolution_patient"] == "Rémission").sum()
    nb_echec = (df_filtered["evolution_patient"] == "Échec de traitement").sum()
    nb_rechute = (df_filtered["evolution_patient"] == "Rechute").sum()
    nb_mortalite = (df_filtered["evolution_patient"] == "Mortalité").sum()

    indicateurs = {
        "Taux d'incidents (%)": nb_incidents / total_patients * 100,
        "Taux IAS (%)": nb_ias / total_patients * 100,
        "Taux de réadmission (%)": nb_readmission / total_patients * 100,
        "Traçabilité (%)": nb_dossiers_complets / total_patients * 100,
        "Effets indésirables graves (/1000 patients)": nb_effets_graves / total_patients * 1000,
        "Délai moyen admission (jours)": delai_moyen,
        "Dossiers complets avec diagnostic (%)": nb_diag_ok / total_patients * 100,
        "Rémission (%)": nb_remission / total_patients * 100,
        "Échec (%)": nb_echec / total_patients * 100,
        "Rechute (%)": nb_rechute / total_patients * 100,
        "Mortalité (%)": nb_mortalite / total_patients * 100,
        "Taux de plaintes (%)": nb_plaintes / total_patients * 100,
    }

    # ------------------------
    # AFFICHAGE KPI
    # ------------------------
    st.markdown("### 📌 Indicateurs clés")

    cols = st.columns(4)
    for i, (label, value) in enumerate(indicateurs.items()):
        with cols[i % 4]:
            st.metric(label, f"{value:.2f}")

    st.divider()

    # ------------------------
    # GRAPHIQUES
    # ------------------------
    st.markdown("### 📊 Visualisations")

    fig1 = px.bar(
        x=["Incidents", "IAS", "Réadmissions", "Plaintes"],
        y=[nb_incidents, nb_ias, nb_readmission, nb_plaintes],
        title="Incidents, IAS, Réadmissions et Plaintes",
        labels={"x": "Indicateur", "y": "Nombre"}
    )
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.pie(
        names=["Rémission", "Échec", "Rechute", "Mortalité"],
        values=[nb_remission, nb_echec, nb_rechute, nb_mortalite],
        title="Évolution des patients"
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ------------------------
    # TABLEAU DÉTAILLÉ
    # ------------------------
    st.markdown("### 🗂️ Patients filtrés")

    st.dataframe(
        df_filtered[[
            "patient_first_name",
            "patient_last_name",
            "patient_service",
            "registration_time",
            "evolution_patient",
            "readmission",
            "infection_soins"
        ]],
        use_container_width=True
    )

    # ------------------------
    # EXPORT EXCEL
    # ------------------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_filtered.to_excel(writer, index=False, sheet_name="Objectifs_KPI")

    st.download_button(
        "⬇️ Télécharger (Excel)",
        data=output.getvalue(),
        file_name="objectifs_kpi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
