# run_app.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import yaml
import streamlit_authenticator as stauth
from io import BytesIO
import plotly.express as px

# ------------------------
# PAGE CONFIG
# ------------------------
st.set_page_config(page_title="Indicateurs de Suivi", layout="wide")

# ------------------------
# SUPABASE CLIENT
# ------------------------
SUPABASE_URL = st.secrets["SUPABASE"]["URL"]
SUPABASE_KEY = st.secrets["SUPABASE"]["KEY"]
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
        prehashed=True
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
# SELECT PAGE
# ------------------------
if role == "admin":
    page = st.sidebar.selectbox("Menu", ["Dashboard", "User Management", "Statistics", "Objectifs"])
else:
    page = "Dashboard"

if page == "Objectifs":
    from objectifs import run_objectifs
    run_objectifs()
# ------------------------
# USER MANAGEMENT (ADMIN)
# ------------------------
if page == "User Management":
    st.subheader("👥 Gestion des utilisateurs")
    df_users = pd.DataFrame([{"username": u, "name": v["name"], "role": v.get("role", "user")}
                             for u, v in credentials["usernames"].items()])
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
                credentials["usernames"][new_username] = {"name": new_name, "password": hashed_pw, "role": new_role}
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
            fig_bar = px.bar(mean_df, x="Indicateur", y="Moyenne", title="Moyennes des indicateurs")
            st.plotly_chart(fig_bar, use_container_width=True)
            for col in numeric_cols:
                fig_hist = px.histogram(df_db, x=col, title=f"Distribution de {col}", nbins=20)
                st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------
# DASHBOARD
# ------------------------
if page == "Dashboard":
    st.subheader("📊 Indicateurs de Suivi Clinique")

    # ------------------------
    # INFORMATIONS PATIENT
    # ------------------------
    col1, col2, col3 = st.columns(3)
    with col1:
        patient_first_name = st.text_input("Prénom du patient", key="first_name")
    with col2:
        patient_last_name = st.text_input("Nom du patient", key="last_name")
    with col3:
        patient_age = st.number_input("Âge", min_value=0, max_value=120, step=1, key="age")

    col1, col2 = st.columns(2)
    with col1:
        patient_sex = st.radio("Sexe", ["Masculin", "Féminin"], horizontal=True, key="sex")
    with col2:
        patient_service = st.text_input("Service / Unité", key="service")

    patient_motif = st.text_area("Motif d’admission / Consultation", key="motif")
    patient_diagnosis = st.text_area("Diagnostic principal", key="diagnostic")

    st.caption(f"Date de saisie : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.divider()

    # ------------------------
    # QUALITÉ ET SÉCURITÉ DES SOINS
    # ------------------------
    st.subheader("🛡️ Qualité et sécurité des soins")
    incident = st.radio("Incidents / erreurs médicales", ["Non", "Oui"], horizontal=True, key="incident")
    nb_incidents = None
    incident_description = ""
    if incident == "Oui":
        nb_incidents = st.number_input("Nombre d’incidents / erreurs", min_value=1, step=1, key="nb_incidents")
        incident_description = st.text_area("Décrire l'incident", key="incident_desc")

    readmission = st.radio("Réadmission", ["Non", "Oui"], horizontal=True, key="readmission")
    readmission_type = ""
    if readmission == "Oui":
        readmission_type = st.radio("Cause de la réadmission", ["PEC incomplète", "Complication"], key="readm_type")

    infection_soins = st.radio("Infections liées aux soins", ["Non", "Oui"], horizontal=True, key="infection")
    infection_description = ""
    if infection_soins == "Oui":
        infection_description = st.text_area("Préciser l’infection liée aux soins", key="infection_desc")

    effets_graves = st.radio("Effets indésirables graves", ["Non", "Oui"], horizontal=True, key="effets")
    effets_graves_description = ""
    if effets_graves == "Oui":
        effets_graves_description = st.text_area("Décrire les effets indésirables graves", key="effets_desc")

    st.divider()

    # ------------------------
    # PERFORMANCE CLINIQUE
    # ------------------------
    st.subheader("💊 Performance clinique")
    delai_admission = st.number_input("Délai d’admission / prise en charge (jours)", min_value=0, step=1, key="delai_adm")
    duree_sejour = st.number_input("Durée du séjour (jours)", min_value=0, step=1, key="duree_sej")
    cause_long_sejour = ""
    if duree_sejour > 10:
        cause_long_sejour = st.text_area("Cause du séjour > 10 jours", key="cause_long_sej")

    diagnostic_etabli = st.radio("Patient sorti avec diagnostic établi ?", ["Oui", "Non"], horizontal=True, key="diag_etabli")
    dossier_complet = st.radio("Dossier complet avec diagnostic ?", ["Oui", "Non"], horizontal=True, key="dossier")
    cause_dossier_incomplet = ""
    if dossier_complet == "Non":
        cause_dossier_incomplet = st.text_area("Si Non, indiquer les éléments manquants", key="dossier_cause")

    evolution_patient = st.selectbox(
        "Évolution du patient",
        ["Rémission", "Échec de traitement", "Rechute", "Mortalité"],
        key="evolution"
    )
    remission_type = ""
    echec_traitement = ""
    cause_echec = ""
    rechute = ""
    cause_rechute = ""
    mortalite_cause = ""

    if evolution_patient == "Rémission":
        remission_type = st.selectbox("Type de rémission", ["Complète", "Partielle"], key="rem_type")
    elif evolution_patient == "Échec de traitement":
        echec_traitement = st.radio("Échec confirmé ?", ["Oui", "Non"], horizontal=True, key="echec")
        if echec_traitement == "Oui":
            cause_echec = st.text_area("Cause de l’échec de traitement", key="cause_echec")
    elif evolution_patient == "Rechute":
        rechute = st.radio("Rechute ?", ["Oui", "Non"], horizontal=True, key="rechute")
        if rechute == "Oui":
            cause_rechute = st.text_area("Préciser la cause de la rechute", key="cause_rechute")
    elif evolution_patient == "Mortalité":
        mortalite_cause = st.text_area("Préciser la cause du décès", key="mort_cause")

    st.divider()

    # ------------------------
    # PERTINENCE DES SOINS
    # ------------------------
    st.subheader("📈 Pertinence des soins")
    pertinence_bio = st.radio("Pertinence des examens biologiques ?", ["Non", "Oui"], horizontal=True, key="pert_bio")
    examens_bio_redondants = examens_bio_non_pertinents = False
    if pertinence_bio == "Non":
        examens_bio_redondants = st.checkbox("Examens redondants", key="bio_redond")
        examens_bio_non_pertinents = st.checkbox("Non pertinents", key="bio_nonpert")
    pertinence_imagerie = st.radio("Pertinence des examens d’imagerie ?", ["Oui", "Non"], horizontal=True, key="pert_imag")

    st.divider()

    # ------------------------
    # SATISFACTION DES PATIENTS
    # ------------------------
    st.subheader("😊 Satisfaction des Patients")
    satisfaction_patient = st.slider("Satisfaction patient", 1, 5, 3, key="satisf")
    plaintes_reclamations = st.radio("Plaintes ou réclamations reçues résolues ?", ["Oui", "Non"], horizontal=True, key="plaintes")

    st.divider()

    # ------------------------
    # INNOVATION ET HUMANISATION
    # ------------------------
    st.subheader("🏥 Innovation et Humanisation")
    telemedecine = st.radio("Patient ayant accès à la télémedecine ou suivi à distance ?", ["Oui", "Non"], horizontal=True, key="telemed")

    st.divider()

    # ------------------------
    # ENREGISTRER
    # ------------------------
    if st.button("💾 Enregistrer"):
        record = {
            "patient_first_name": patient_first_name or None,
            "patient_last_name": patient_last_name or None,
            "patient_age": patient_age,
            "patient_sex": patient_sex or None,
            "patient_service": patient_service or None,
            "patient_motif": patient_motif or None,
            "patient_diagnosis": patient_diagnosis or None,
            "incident": incident,
            "nb_incidents": int(nb_incidents) if nb_incidents is not None else None,
            "incident_description": incident_description or None,
            "readmission": readmission,
            "readmission_type": readmission_type or None,
            "infection_soins": infection_soins,
            "infection_description": infection_description or None,
            "effets_graves": effets_graves,
            "effets_graves_description": effets_graves_description or None,
            "delai_admission": delai_admission,
            "duree_sejour": duree_sejour,
            "cause_long_sejour": cause_long_sejour or None,
            "diagnostic_etabli": diagnostic_etabli,
            "dossier_complet": dossier_complet,
            "cause_dossier_incomplet": cause_dossier_incomplet or None,
            "evolution_patient": evolution_patient,
            "remission_type": remission_type or None,
            "echec_traitement": echec_traitement or None,
            "cause_echec": cause_echec or None,
            "rechute": rechute or None,
            "cause_rechute": cause_rechute or None,
            "mortalite_cause": mortalite_cause or None,
            "pertinence_bio": pertinence_bio,
            "examens_bio_redondants": examens_bio_redondants,
            "examens_bio_non_pertinents": examens_bio_non_pertinents,
            "pertinence_imagerie": pertinence_imagerie,
            "satisfaction_patient": satisfaction_patient,
            "plaintes_reclamations": plaintes_reclamations,
            "telemedecine": telemedecine,
            "registration_time": datetime.now().isoformat()
        }
        supabase.table("indicateurs_cliniques").insert(record).execute()
        supabase.table("activity_logs").insert({
            "username": username,
            "action": f"Enregistrement patient {patient_first_name} {patient_last_name}",
            "timestamp": datetime.now().isoformat()
        }).execute()
        st.success(f"✅ Données enregistrées pour {patient_first_name} {patient_last_name}")

# ------------------------
# AFFICHER LES 10 DERNIERS PATIENTS AVEC FILTRES NOM/PRÉNOM
# ------------------------
st.subheader("🗂️ Derniers patients enregistrés")
all_records = supabase.table("indicateurs_cliniques").select("*").order("registration_time", desc=True).execute().data

if all_records:
    df_all = pd.DataFrame(all_records)
    col1, col2 = st.columns(2)
    with col1:
        filter_first_name = st.text_input("Filtrer par prénom", key="filter_first_name")
    with col2:
        filter_last_name = st.text_input("Filtrer par nom", key="filter_last_name")

    df_filtered = df_all.copy()
    if filter_first_name:
        df_filtered = df_filtered[df_filtered["patient_first_name"].str.contains(filter_first_name, case=False, na=False)]
    if filter_last_name:
        df_filtered = df_filtered[df_filtered["patient_last_name"].str.contains(filter_last_name, case=False, na=False)]

    st.dataframe(
        df_filtered.head(10)[[
            "patient_first_name", "patient_last_name", "patient_age",
            "patient_sex", "patient_service", "registration_time"
        ]],
        use_container_width=True
    )

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_all.to_excel(writer, index=False, sheet_name="Tous les Patients")

    st.download_button(
        label="⬇️ Télécharger tous les patients",
        data=output.getvalue(),
        file_name="tous_les_patients.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_all_patients"
    )
else:
    st.info("Aucun patient enregistré pour le moment")
