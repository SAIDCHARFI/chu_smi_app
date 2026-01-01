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
        credentials, cookie_name, cookie_key, cookie_expiry_days, auto_hash=True
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
page = st.sidebar.selectbox(
    "Menu", ["Dashboard", "User Management", "Statistics"] if role == "admin" else ["Dashboard"]
)

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
                    yaml.dump({"usernames": credentials["usernames"], "cookie": users_config["cookie"]}, file)
                st.success(f"Utilisateur {new_username} ajouté !")

    st.markdown("### ❌ Supprimer un utilisateur")
    del_username = st.selectbox("Sélectionner utilisateur à supprimer", df_users["username"])
    if st.button("Supprimer"):
        if del_username in credentials["usernames"]:
            del credentials["usernames"][del_username]
            with open("users.yaml", "w") as file:
                yaml.dump({"usernames": credentials["usernames"], "cookie": users_config["cookie"]}, file)
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
            st.plotly_chart(px.bar(mean_df, x="Indicateur", y="Moyenne", title="Moyennes des indicateurs"), use_container_width=True)
            for col in numeric_cols:
                st.plotly_chart(px.histogram(df_db, x=col, title=f"Distribution de {col}", nbins=20), use_container_width=True)

# ------------------------
# DASHBOARD
# ------------------------
if page == "Dashboard":
    st.subheader("👤 Informations patient")
    with st.form("form_indicateurs"):
        # ------------------------ PATIENT INFO ------------------------
        patient_first_name = st.text_input("Prénom du patient", key="first_name")
        patient_last_name = st.text_input("Nom du patient", key="last_name")
        patient_age = st.number_input("Âge", min_value=0, max_value=120, step=1, key="age")
        patient_sex = st.radio("Sexe", ["Masculin", "Féminin"], horizontal=True, key="sex")
        patient_service = st.text_input("Service / Unité", key="service")
        patient_motif = st.text_area("Motif d’admission / Consultation", key="motif")
        patient_diagnosis = st.text_area("Diagnostic principal", key="diagnosis")
        registration_time = datetime.now()

        # ------------------------ QUALITÉ ET SÉCURITÉ DES SOINS ------------------------
        st.subheader("🛡️ Qualité et sécurité des soins")
        incident = st.radio("Incidents / erreurs médicales", ["Non", "Oui"], horizontal=True, key="incident")
        nb_incidents = st.number_input("Nombre d’incidents / erreurs", min_value=0, step=1, key="nb_incidents") if incident=="Oui" else 0
        readmission = st.radio("Réadmission", ["Non", "Oui"], horizontal=True, key="readmission")
        readmission_type = st.text_input("Cause de la réadmission", key="readmission_type") if readmission=="Oui" else ""
        infection_soins = st.radio("Infections liées aux soins", ["Non", "Oui"], horizontal=True, key="infection")
        infection_description = st.text_area("Préciser l’infection liée aux soins", key="infection_desc") if infection_soins=="Oui" else ""
        effets_graves = st.radio("Effets indésirables graves", ["Non", "Oui"], horizontal=True, key="effets")
        effets_graves_description = st.text_area("Décrire les effets indésirables graves", key="effets_desc") if effets_graves=="Oui" else ""

        # ------------------------ PERFORMANCE CLINIQUE ------------------------
        st.subheader("💊 Performance clinique")
        delai_admission = st.number_input("Délai d’admission / prise en charge (jours)", min_value=0, step=1, key="delai_admission")
        duree_sejour = st.number_input("Durée du séjour (jours)", min_value=0, step=1, key="duree_sejour")
        cause_long_sejour = st.text_area("Cause du séjour > 10 jours", key="cause_long_sejour") if duree_sejour>10 else ""
        diagnostic_etabli = st.radio("Patient sorti avec diagnostic établi ?", ["Oui", "Non"], horizontal=True, key="diagnostic_etabli")
        dossier_complet = st.radio("Dossier complet avec diagnostic ?", ["Oui", "Non"], horizontal=True, key="dossier_complet")
        cause_dossier_incomplet = st.text_area("Si Non, indiquer les éléments manquants", key="cause_dossier_incomplet") if dossier_complet=="Non" else ""
        evolution_patient = st.selectbox("Évolution du patient", ["Rémission", "Échec de traitement", "Rechute", "Mortalité"], key="evolution")
        remission_type = st.selectbox("Type de rémission", ["Complète","Partielle"], key="remission_type") if evolution_patient=="Rémission" else ""
        echec_traitement = st.radio("Échec confirmé ?", ["Oui","Non"], horizontal=True, key="echec") if evolution_patient=="Échec de traitement" else ""
        cause_echec = st.text_area("Cause de l’échec de traitement", key="cause_echec") if echec_traitement=="Oui" else ""
        rechute = st.radio("Rechute ?", ["Oui","Non"], horizontal=True, key="rechute") if evolution_patient=="Rechute" else ""
        cause_rechute = st.text_area("Préciser la cause de la rechute", key="cause_rechute") if rechute=="Oui" else ""
        mortalite_cause = st.text_area("Préciser la cause du décès", key="mortalite_cause") if evolution_patient=="Mortalité" else ""

        # ------------------------ PERTINENCE DES SOINS ------------------------
        st.subheader("📈 Pertinence des soins")
        pertinence_bio = st.radio("Pertinence des examens biologiques ?", ["Oui","Non"], horizontal=True, key="pertinence_bio")
        examens_bio_redondants = st.checkbox("Examens redondants", key="examens_redondants") if pertinence_bio=="Oui" else False
        examens_bio_non_pertinents = st.checkbox("Non pertinents", key="examens_non_pertinents") if pertinence_bio=="Oui" else False
        pertinence_imagerie = st.radio("Pertinence des examens d’imagerie ?", ["Oui","Non"], horizontal=True, key="pertinence_imagerie")

        # ------------------------ SATISFACTION PATIENT ------------------------
        st.subheader("😊 Satisfaction des Patients")
        satisfaction_patient = st.slider("Satisfaction patient", 1,5,3, key="satisfaction_patient")
        plaintes_resolues = st.radio("Plaintes ou réclamations reçues résolues ?", ["Oui","Non"], horizontal=True, key="plaintes_resolues")

        # ------------------------ INNOVATION / HUMANISATION ------------------------
        st.subheader("🏥 Innovation et Humanisation")
        acces_telemedecine = st.radio("Patient ayant accès à la télémedecine ou suivi à distance ?", ["Oui","Non"], horizontal=True, key="telemedecine")

        # ------------------------ SUBMIT ------------------------
        submit = st.form_submit_button("💾 Enregistrer")
        if submit:
            record = {
                "patient_first_name": patient_first_name,
                "patient_last_name": patient_last_name,
                "patient_age": patient_age,
                "patient_sex": patient_sex,
                "patient_service": patient_service,
                "patient_motif": patient_motif,
                "patient_diagnosis": patient_diagnosis,
                "registration_time": registration_time.isoformat(),
                "incident": incident,
                "nb_incidents": nb_incidents,
                "readmission": readmission,
                "readmission_type": readmission_type,
                "infection_soins": infection_soins,
                "infection_description": infection_description,
                "effets_graves": effets_graves,
                "effets_graves_description": effets_graves_description,
                "delai_admission": delai_admission,
                "duree_sejour": duree_sejour,
                "cause_long_sejour": cause_long_sejour,
                "diagnostic_etabli": diagnostic_etabli,
                "dossier_complet": dossier_complet,
                "cause_dossier_incomplet": cause_dossier_incomplet,
                "evolution_patient": evolution_patient,
                "remission_type": remission_type,
                "echec_traitement": echec_traitement,
                "cause_echec": cause_echec,
                "rechute": rechute,
                "cause_rechute": cause_rechute,
                "mortalite_cause": mortalite_cause,
                "pertinence_bio": pertinence_bio,
                "examens_bio_redondants": examens_bio_redondants,
                "examens_bio_non_pertinents": examens_bio_non_pertinents,
                "pertinence_imagerie": pertinence_imagerie,
                "satisfaction_patient": satisfaction_patient,
                "plaintes_resolues": plaintes_resolues,
                "acces_telemedecine": acces_telemedecine
            }
            supabase.table("indicateurs_cliniques").insert(record).execute()
            supabase.table("activity_logs").insert({
                "username": username,
                "action": f"Submitted clinical indicators for {patient_first_name} {patient_last_name}",
                "timestamp": datetime.now().isoformat()
            }).execute()
            st.success(f"✅ Données enregistrées pour {patient_first_name} {patient_last_name}")

            # Display saved data
            records = supabase.table("indicateurs_cliniques").select("*").order("registration_time", desc=True).execute().data
            df_db = pd.DataFrame(records)
            if not df_db.empty:
                st.dataframe(df_db, use_container_width=True)

