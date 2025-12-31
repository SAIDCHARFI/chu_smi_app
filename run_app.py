# run_app.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import yaml
import streamlit_authenticator as stauth
from datetime import datetime
import plotly.express as px
from io import BytesIO

# ------------------------
# PAGE CONFIG
# ------------------------
st.set_page_config(page_title="Indicateurs de Suivi", layout="wide")

# ------------------------
# SUPABASE CLIENT INIT
# ------------------------
SUPABASE_URL = "https://pvjdgddzuzarygaxyxuw.supabase.co"
SUPABASE_KEY = "sb_publishable_ilPGwOE_zkgfeqp-PosqPA_7mxrgfbF"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------
# LOAD USERS FROM YAML
# ------------------------
with open("users.yaml") as file:
    users_config = yaml.safe_load(file)

credentials = {"usernames": users_config["usernames"]}
cookie_name = users_config["cookie"]["name"]
cookie_key = users_config["cookie"]["key"]
cookie_expiry_days = users_config["cookie"]["expiry_days"]

# ------------------------
# AUTHENTICATOR INIT
# ------------------------
if "authenticator" not in st.session_state:
    st.session_state["authenticator"] = stauth.Authenticate(
        credentials,
        cookie_name,
        cookie_key,
        cookie_expiry_days,
        auto_hash=True
    )
authenticator = st.session_state["authenticator"]

# ------------------------
# LOGIN
# ------------------------
authenticator.login("main")
if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    user_name = st.session_state["name"]
    role = credentials["usernames"][username].get("role", "user")
    st.sidebar.success(f"Connecté en tant que {user_name} ({role})")
    authenticator.logout("Logout", "sidebar")
elif st.session_state.get("authentication_status") is False:
    st.error("❌ Nom d'utilisateur ou mot de passe incorrect")
    st.stop()
else:
    st.warning("Veuillez entrer vos identifiants")
    st.stop()

# ------------------------
# ADMIN PAGES
# ------------------------
if role == "admin":
    page = st.sidebar.selectbox("Menu", ["Dashboard", "User Management", "Statistics"])
else:
    page = "Dashboard"

# ------------------------
# USER MANAGEMENT (ADMIN)
# ------------------------
if page == "User Management":
    st.subheader("👥 Gestion des utilisateurs")
    df_users = pd.DataFrame([
        {"username": u, "name": v["name"], "role": v.get("role", "user")}
        for u, v in credentials["usernames"].items()
    ])
    st.dataframe(df_users, use_container_width=True)

    st.markdown("### ➕ Ajouter un utilisateur")
    with st.form("add_user_form"):
        new_username = st.text_input("Nom d'utilisateur")
        new_name = st.text_input("Nom complet")
        new_password = st.text_input("Mot de passe", type="password")
        new_role = st.selectbox("Rôle", ["user", "admin"])
        add_user = st.form_submit_button("Ajouter")
        if add_user:
            if new_username in credentials["usernames"]:
                st.warning("⚠️ Utilisateur déjà existant")
            else:
                hashed_pw = stauth.Hasher([new_password]).generate()[0]
                credentials["usernames"][new_username] = {
                    "name": new_name,
                    "password": hashed_pw,
                    "role": new_role
                }
                with open("users.yaml", "w") as file:
                    yaml.dump({"usernames": credentials["usernames"],
                               "cookie": users_config["cookie"]}, file)
                st.success(f"Utilisateur {new_username} ajouté !")

    st.markdown("### ❌ Supprimer un utilisateur")
    del_username = st.selectbox("Sélectionner utilisateur à supprimer", df_users["username"])
    if st.button("Supprimer"):
        if del_username in credentials["usernames"]:
            del credentials["usernames"][del_username]
            with open("users.yaml", "w") as file:
                yaml.dump({"usernames": credentials["usernames"],
                           "cookie": users_config["cookie"]}, file)
            st.success(f"Utilisateur {del_username} supprimé !")

    st.markdown("### 📝 Journaux d'activité")
    logs = supabase.table("activity_logs").select("*").order("timestamp", desc=True).execute().data
    df_logs = pd.DataFrame(logs)
    st.dataframe(df_logs, use_container_width=True)

# ------------------------
# STATISTICS (ADMIN)
# ------------------------
if page == "Statistics":
    st.subheader("📊 Statistiques des indicateurs")
    records = supabase.table("indicateurs_cliniques").select("*").execute().data
    df_db = pd.DataFrame(records)
    if df_db.empty:
        st.info("Aucune donnée enregistrée pour afficher des statistiques")
    else:
        numeric_cols = df_db.select_dtypes(include=["int64", "float64"]).columns.tolist()
        if numeric_cols:
            mean_df = df_db[numeric_cols].mean().reset_index()
            mean_df.columns = ["Indicateur", "Moyenne"]
            fig_bar = px.bar(mean_df, x="Indicateur", y="Moyenne", title="Moyennes des indicateurs")
            st.plotly_chart(fig_bar, use_container_width=True)
            for col in numeric_cols:
                fig_hist = px.histogram(df_db, x=col, title=f"Distribution de {col}", nbins=20)
                st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------
# DASHBOARD
# ------------------------
if page == "Dashboard":
    st.subheader("👤 Informations patient")
    with st.form("form_indicateurs"):
        # Patient info
        patient_first_name = st.text_input("Prénom du patient")
        patient_last_name = st.text_input("Nom du patient")
        registration_time = datetime.now()

        # Clinical indicators
        st.subheader("⏱ Indicateurs cliniques")
        delai_diagnostic = st.number_input("Délai diagnostic (jours)", min_value=0, step=1)
        bio = st.checkbox("Examens biologiques pertinents")
        imagerie = st.checkbox("Examens d’imagerie pertinents")

        # Therapeutic indicators
        st.subheader("💊 Indicateurs thérapeutiques")
        corticoides = st.checkbox("Utilisation des corticoïdes")
        effets = st.checkbox("Effets indésirables médicamenteux")
        adhesion = st.checkbox("Adhésion aux recommandations")
        delai_ims = st.number_input("Délai introduction IMS / biothérapies (jours)", min_value=0, step=1)

        # Evolution indicators
        st.subheader("📈 Indicateurs d’évolution")
        remission = st.checkbox("Rémission")
        rechute = st.checkbox("Rechute")
        duree_sejour = st.number_input("Durée du séjour (jours)", min_value=0, step=1)
        mortalite = st.checkbox("Décès")

        # Safety indicators
        st.subheader("🏥 Indicateurs de sécurité des soins")
        inf_soins = st.checkbox("Infections associées aux soins")
        inf_opp = st.checkbox("Infections opportunistes")
        st.caption("### 🔁 Réhospitalisations")
        rehosp_comp = st.checkbox("Complication")
        rehosp_incompl = st.checkbox("PEC incomplète")
        rehosp_autres = st.checkbox("Autres causes")

        # Organizational indicators
        st.subheader("🏥 Indicateurs organisationnels")
        duree_moy_sejour = st.number_input("Durée moyenne du séjour (jours)", min_value=0, step=1)
        delai_examens = st.number_input("Délai réalisation des examens (jours)", min_value=0, step=1)
        taux_hospit = st.number_input("Taux d’hospitalisation prolongée", min_value=0, step=1)

        # Quality
        st.subheader("⭐ Qualité")
        qualite = st.slider("Qualité de la traçabilité", 1, 5, 3)
        satisfaction = st.slider("Satisfaction patient", 1, 5, 3)
        observance = st.slider("Observance thérapeutique", 1, 5, 3)
        education = st.checkbox("Éducation thérapeutique réalisée")

        submit = st.form_submit_button("💾 Enregistrer")
        if submit:
            record = {
                "patient_first_name": patient_first_name,
                "patient_last_name": patient_last_name,
                "registration_time": registration_time.isoformat(),
                "delai_diagnostic": int(delai_diagnostic),
                "pertinence_exam_bio": int(bio),
                "pertinence_exam_imagerie": int(imagerie),
                "utilisation_corticoides": int(corticoides),
                "delai_introduction_ims_biotherapies": int(delai_ims),
                "effets_indesirables_medicamenteux": int(effets),
                "adhesion_recommandations": int(adhesion),
                "remission": int(remission),
                "rechute": int(rechute),
                "duree_sejour": int(duree_sejour),
                "mortalite": int(mortalite),
                "infections_associees_soins": int(inf_soins),
                "infections_opportunistes": int(inf_opp),
                "rehosp_complication": int(rehosp_comp),
                "rehosp_pec_incomplete": int(rehosp_incompl),
                "rehosp_autres": int(rehosp_autres),
                "duree_moyenne_sejour": float(duree_moy_sejour),
                "delai_realisation_examens": int(delai_examens),
                "taux_hospitalisation_prolongee": float(taux_hospit),
                "qualite_tracabilite_dossiers": int(qualite),
                "satisfaction_patient": int(satisfaction),
                "observance_therapeutique": int(observance),
                "education_therapeutique": int(education)
            }
            # Insert record
            supabase.table("indicateurs_cliniques").insert(record).execute()
            # Log activity
            supabase.table("activity_logs").insert({
                "username": username,
                "action": f"Submitted clinical indicators for {patient_first_name} {patient_last_name}",
                "timestamp": datetime.now().isoformat()
            }).execute()
            st.success(f"✅ Données enregistrées pour {patient_first_name} {patient_last_name}")

    # Display saved data
    st.divider()
    st.subheader("📋 Données enregistrées")
    records = supabase.table("indicateurs_cliniques").select("*").order("registration_time", desc=True).execute().data
    df_db = pd.DataFrame(records)
    if not df_db.empty:
        filter_column = st.selectbox("Filtrer par colonne", df_db.columns)
        if filter_column:
            unique_values = df_db[filter_column].unique()
            selected_values = st.multiselect(f"Sélectionner {filter_column}", unique_values, default=unique_values)
            df_db = df_db[df_db[filter_column].isin(selected_values)]
        st.dataframe(df_db, use_container_width=True)

    # Export options
    st.subheader("💾 Exporter les données")
    export_format = st.radio("Format d'export", ["CSV", "Excel"], horizontal=True)

    if st.button("Exporter"):
        if export_format == "CSV":
            csv_data = df_db.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Télécharger CSV",
                csv_data,
                "indicateurs_cliniques.csv",
                "text/csv"
            )
        else:
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_db.to_excel(writer, index=False, sheet_name="Indicateurs")
            st.download_button(
                label="Télécharger Excel",
                data=output.getvalue(),
                file_name="indicateurs_cliniques.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
