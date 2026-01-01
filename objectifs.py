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
    st.set_page_config(page_title="Objectifs & KPI", layout="wide")

    st.subheader("🎯 Objectifs et Indicateurs Cliniques")

    # ------------------------
    # FILTRES
    # ------------------------
    records = supabase.table("indicateurs_cliniques").select("*").execute().data
    if not records:
        st.info("Aucune donnée disponible pour calculer les indicateurs.")
        st.stop()

    # Convert to DataFrame
    df = pd.DataFrame(records)

    # Convert registration_time to datetime
    df['registration_time'] = pd.to_datetime(df['registration_time'])

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Date début", df['registration_time'].min().date())
    with col2:
        end_date = st.date_input("Date fin", df['registration_time'].max().date())

    service_filter = st.text_input("Filtrer par service (laisser vide = tous)")

    # Filter by date and service
    df_filtered = df[(df['registration_time'].dt.date >= start_date) & (df['registration_time'].dt.date <= end_date)]
    if service_filter:
        df_filtered = df_filtered[df_filtered['patient_service'].str.contains(service_filter, case=False, na=False)]

    # ------------------------
    # CALCUL DES INDICATEURS
    # ------------------------
    total_patients = len(df_filtered)
    nb_incidents = df_filtered['nb_incidents'].sum()
    nb_ias = df_filtered[df_filtered['infection_soins'] == 'Oui'].shape[0]
    nb_readmission = df_filtered[df_filtered['readmission'] == 'Oui'].shape[0]
    nb_dossiers_complets = df_filtered[df_filtered['dossier_complet'] == 'Oui'].shape[0]
    nb_effets_graves = df_filtered[df_filtered['effets_graves'] == 'Oui'].shape[0]
    delai_moyen = df_filtered['delai_admission'].mean() if not df_filtered['delai_admission'].empty else 0
    nb_dossiers_complet_diag = df_filtered[df_filtered['diagnostic_etabli'] == 'Oui'].shape[0]
    nb_plaintes = df_filtered[df_filtered['plaintes_reclamations'] == 'Oui'].shape[0]

    # Évolution patients
    nb_remission = df_filtered[df_filtered['evolution_patient'] == 'Rémission'].shape[0]
    nb_echec = df_filtered[df_filtered['evolution_patient'] == 'Échec de traitement'].shape[0]
    nb_rechute = df_filtered[df_filtered['evolution_patient'] == 'Rechute'].shape[0]
    nb_mortalite = df_filtered[df_filtered['evolution_patient'] == 'Mortalité'].shape[0]

    # Calculs
    indicateurs = {
        'Taux d'incidents (%)': (nb_incidents / total_patients * 100) if total_patients else 0,
        'Taux IAS (%)': (nb_ias / total_patients * 100) if total_patients else 0,
        'Taux de réadmission (%)': (nb_readmission / total_patients * 100) if total_patients else 0,
        'Traçabilité (%)': (nb_dossiers_complets / total_patients * 100) if total_patients else 0,
        'Effets indésirables graves (/1000 patients)': (nb_effets_graves / total_patients * 1000) if total_patients else 0,
        'Délai moyen (jours)': delai_moyen,
        'Dossiers complets avec diagnostic (%)': (nb_dossiers_complet_diag / total_patients * 100) if total_patients else 0,
        'Rémission (%)': (nb_remission / total_patients * 100) if total_patients else 0,
        'Échec (%)': (nb_echec / total_patients * 100) if total_patients else 0,
        'Rechute (%)': (nb_rechute / total_patients * 100) if total_patients else 0,
        'Mortalité (%)': (nb_mortalite / total_patients * 100) if total_patients else 0,
        'Taux de plaintes (%)': (nb_plaintes / total_patients * 100) if total_patients else 0
    }

    # ------------------------
    # AFFICHAGE KPI
    # ------------------------
    kpi_cols = st.columns(len(indicateurs))
    for i, (k, v) in enumerate(indicateurs.items()):
        with kpi_cols[i % len(kpi_cols)]:
            st.metric(label=k, value=f"{v:.2f}")

    st.divider()

    # ------------------------
    # GRAPHIQUES
    # ------------------------
    st.subheader("📊 Visualisation des indicateurs")

    # Histogramme incidents vs IAS
    fig1 = px.bar(x=['Incidents', 'IAS', 'Réadmissions', 'Plaintes'], y=[nb_incidents, nb_ias, nb_readmission, nb_plaintes], labels={'x':'Indicateur','y':'Nombre'}, title='Incidents, IAS, Réadmissions, Plaintes')
    st.plotly_chart(fig1, use_container_width=True)

    # Évolution patients
    fig2 = px.pie(names=['Rémission','Échec','Rechute','Mortalité'], values=[nb_remission, nb_echec, nb_rechute, nb_mortalite], title='Évolution des patients')
    st.plotly_chart(fig2, use_container_width=True)

    # ------------------------
    # TABLEAU DES PATIENTS FILTRÉS
    # ------------------------
    st.subheader("🗂️ Tableau détaillé des patients filtrés")
    st.dataframe(df_filtered, use_container_width=True)

    # Export Excel
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_filtered.to_excel(writer, index=False, sheet_name="Patients Filtrés")

    st.download_button(
        label="⬇️ Télécharger les patients filtrés",
        data=output.getvalue(),
        file_name="patients_filtres.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



