# run_app.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import yaml
import streamlit_authenticator as stauth
from datetime import datetime
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
        new_username = st.text_input("Nom d'utilisateur", key="new_username")
        new_name = st.text_input("Nom complet", key="new_name")
        new_password = st.text_input("Mot de passe", type="password", key="new_password")
        new_role = st.selectbox("Rôle", ["user", "admin"], key="new_role")
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
    del_username = st.selectbox("Sélectionner utilisateur à supprimer", df_users["username"], key="del_username")
    if st.button("Supprimer", key="del_user"):
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
            import plotly.express as px
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

        col1, col2, col3 = st.columns(3)
        with col1:
            patient_first_name = st.text_input("Prénom du patient", key="patient_first_name")
        with col2:
            patient_last_name = st.text_input("Nom du patient", key="patient_last_name")
        with col3:
            patient_age = st.number_input("Âge", min_value=0, max_value=120, step=1, key="patient_age")

        col1, col2 = st.columns(2)
        with col1:
            patient_sex = st.radio("Sexe", ["Masculin", "Féminin"], horizontal=True, key="patient_sex")
        with col2:
            patient_service = st.text_input("Service / Unité", key="patient_service")

        patient_motif = st.text_area("Motif d’admission / Consultation", key="patient_motif")
        patient_diagnosis = st.text_area("Diagnostic principal", key="patient_diagnosis")
        registration_time = datetime.now()

        st.divider()
        st.subheader("🛡️ Qualité et sécurité des soins")

        # --- Incidents ---
        incident = st.radio("Incidents / erreurs médicales", ["Non", "Oui"], horizontal=True, key="incident")
        nb_incidents_placeholder = st.empty()
        nb_incidents = 0
        if incident == "Oui":
            nb_incidents = nb_incidents_placeholder.number_input("Nombre d’incidents / erreurs", min_value=1, step=1, key="nb_incidents")

        # --- Réadmission ---
        readmission = st.radio("Réadmission", ["Non", "Oui"], horizontal=True, key="readmission")
        readmission_placeholder = st.empty()
        readmission_type = ""
        if readmission == "Oui":
            readmission_type = readmission_placeholder.radio("Cause de la réadmission", ["PEC incomplète", "Complication"], key="readmission_type")

        # --- Infections liées aux soins ---
        infection_soins = st.radio("Infections liées aux soins", ["Non", "Oui"], horizontal=True, key="infection_soins")
        infection_placeholder = st.empty()
        infection_description = ""
        if infection_soins == "Oui":
            infection_description = infection_placeholder.text_area("Préciser l’infection liée aux soins", key="infection_description")

        # --- Effets indésirables graves ---
        effets_graves = st.radio("Effets indésirables graves", ["Non", "Oui"], horizontal=True, key="effets_graves")
        effets_placeholder = st.empty()
        effets_graves_description = ""
        if effets_graves == "Oui":
            effets_graves_description = effets_placeholder.text_area("Décrire les effets indésirables graves", key="effets_graves_description")

        st.divider()
        st.subheader("💊 Performance clinique")

        delai_admission = st.number_input("Délai d’admission / prise en charge (jours)", min_value=0, step=1, key="delai_admission")
        duree_sejour = st.number_input("Durée du séjour (jours)", min_value=0, step=1, key="duree_sejour")
        cause_long_sejour_placeholder = st.empty()
        cause_long_sejour = ""
        if duree_sejour > 10:
            cause_long_sejour = cause_long_sejour_placeholder.text_area("Cause du séjour > 10 jours", key="cause_long_sejour")

        diagnostic_etabli = st.radio("Patient sorti avec diagnostic établi ?", ["Oui", "Non"], horizontal=True, key="diagnostic_etabli")

        dossier_complet = st.radio("Dossier complet avec diagnostic ?", ["Oui", "Non"], horizontal=True, key="dossier_complet")
        cause_dossier_incomplet_placeholder = st.empty()
        cause_dossier_incomplet = ""
        if dossier_complet == "Non":
            cause_dossier_incomplet = cause_dossier_incomplet_placeholder.text_area("Si Non, indiquer les éléments manquants", key="cause_dossier_incomplet")

        evolution_patient = st.selectbox(
            "Évolution du patient",
            ["Rémission", "Échec de traitement", "Rechute", "Mortalité"],
            key="evolution_patient"
        )

        remission_type_placeholder = st.empty()
        remission_type = ""
        echec_traitement_placeholder = st.empty()
        echec_traitement = ""
        cause_echec_placeholder = st.empty()
        cause_echec = ""
        rechute_placeholder = st.empty()
        rechute = ""
        cause_rechute_placeholder = st.empty()
        cause_rechute = ""
        mortalite_cause_placeholder = st.empty()
        mortalite_cause = ""

        if evolution_patient == "Rémission":
            remission_type = remission_type_placeholder.selectbox("Type de rémission", ["Complète", "Partielle"], key="remission_type")
        if evolution_patient == "Échec de traitement":
            echec_traitement = echec_traitement_placeholder.radio("Échec confirmé ?", ["Oui", "Non"], horizontal=True, key="echec_traitement")
            if echec_traitement == "Oui":
                cause_echec = cause_echec_placeholder.text_area("Cause de l’échec de traitement", key="cause_echec")
        if evolution_patient == "Rechute":
            rechute = rechute_placeholder.radio("Rechute ?", ["Oui", "Non"], horizontal=True, key="rechute")
            if rechute == "Oui":
                cause_rechute = cause_rechute_placeholder.text_area("Préciser la cause de la rechute", key="cause_rechute")
        if evolution_patient == "Mortalité":
            mortalite_cause = mortalite_cause_placeholder.text_area("Préciser la cause du décès", key="mortalite_cause")

        st.divider()
        st.subheader("📈 Pertinence des soins")

        pertinence_bio = st.radio("Pertinence des examens biologiques ?", ["Oui", "Non"], horizontal=True, key="pertinence_bio")
        examens_bio_redondants_placeholder = st.empty()
        examens_bio_non_pertinents_placeholder = st.empty()
        examens_bio_redondants = False
        examens_bio_non_pertinents = False
        if pertinence_bio == "Oui":
            examens_bio_redondants = examens_bio_redondants_placeholder.checkbox("Examens redondants", key="examens_bio_redondants")
            examens_bio_non_pertinents = examens_bio_non_pertinents_placeholder.checkbox("Non pertinents", key="examens_bio_non_pertinents")

        pertinence_imagerie = st.radio("Pertinence des examens d’imagerie ?", ["Oui", "Non"], horizontal=True, key="pertinence_imagerie")

        st.divider()
        st.subheader("😊 Satisfaction des Patients")
        satisfaction = st.slider("Satisfaction patient", 1, 5, 3, key="satisfaction")
        plaintes_resolues = st.radio("Plaintes ou réclamations reçues résolues ?", ["Oui", "Non"], horizontal=True, key="plaintes_resolues")

        st.divider()
        st.subheader("🏥 Innovation et Humanisation")
        telemedecine = st.radio("Patient ayant accès à la télémedecine ou suivi à distance ?", ["Oui", "Non"], horizontal=True, key="telemedecine")

        submit = st.form_submit_button("💾 Enregistrer")
        if submit:
            record = {
                "patient_first_name": patient_first_name,
                "patient_last_name": patient_last_name,
                "patient_age": int(patient_age),
                "patient_sex": patient_sex,
                "patient_service": patient_service,
                "patient_motif": patient_motif,
                "patient_diagnosis": patient_diagnosis,
                "registration_time": registration_time.isoformat(),
                "incident": incident,
                "nb_incidents": int(nb_incidents),
                "readmission": readmission,
                "cause_readmission": readmission_type,
                "infection_soins": infection_soins,
                "description_infection": infection_description,
                "effets_graves": effets_graves,
                "description_effets_graves": effets_graves_description,
                "delai_admission": int(delai_admission),
                "duree_sejour": int(duree_sejour),
                "cause_long_sejour": cause_long_sejour,
                "diagnostic_etabli": diagnostic_etabli,
                "dossier_complet": dossier_complet,
                "cause_dossier_incomplet": cause_dossier_incomplet,
                "evolution_patient": evolution_patient,
                "type_remission": remission_type,
                "echec_traitement": echec_traitement,
                "cause_echec": cause_echec,
                "rechute": rechute,
                "cause_rechute": cause_rechute,
                "mortalite_cause": mortalite_cause,
                "pertinence_bio": pertinence_bio,
                "examens_bio_redondants": examens_bio_redondants,
                "examens_bio_non_pertinents": examens_bio_non_pertinents,
                "pertinence_imagerie": pertinence_imagerie,
                "satisfaction": satisfaction,
                "plaintes_resolues": plaintes_resolues,
                "telemedecine": telemedecine
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
