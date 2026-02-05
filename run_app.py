# run_app.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
from io import BytesIO
import plotly.express as px
import os
import json

st.set_page_config(page_title="Indicateurs de Suivi", layout="wide")

# ------------------------
# CSS pour cacher menu/header/footer
# ------------------------
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden; height: 0px;}
a[href*="streamlit.io"] {display:none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ------------------------
# SUPABASE CONFIG
# ------------------------
SUPABASE_URL = st.secrets["SUPABASE"]["URL"]
SUPABASE_KEY = st.secrets["SUPABASE"]["KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
SUPABASE_ONLINE = True
LOCAL_FILE = "local_records.json"

# ------------------------
# Fonction pour sauvegarder localement
# ------------------------
def save_locally(record):
    local_data = []
    if os.path.exists(LOCAL_FILE):
        with open(LOCAL_FILE, "r") as f:
            try:
                local_data = json.load(f)
            except json.JSONDecodeError:
                local_data = []
    local_data.append(record)
    with open(LOCAL_FILE, "w") as f:
        json.dump(local_data, f, indent=4)
    st.info("💾 Données enregistrées localement")

# ------------------------
# CHECK CONNECTION
# ------------------------
try:
    supabase.table("users").select("id").limit(1).execute()
except Exception:
    SUPABASE_ONLINE = False
    st.warning("⚠️ Mode hors ligne — certaines fonctionnalités sont désactivées")

# ------------------------
# AUTHENTICATION
# ------------------------
if "user" not in st.session_state:
    st.title("Connexion")
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.experimental_rerun()
        except Exception:
            st.error("❌ Email ou mot de passe incorrect")
    st.stop()

user = st.session_state.user
try:
    res = supabase.table("users").select("*").eq("auth_user_id", user.id).single().execute()
    profile = res.data
    if not profile:
        st.error(
            "❌ Aucun profil trouvé pour cet utilisateur.\n"
            "Veuillez créer une entrée dans la table 'users' avec ce 'auth_user_id'."
        )
        st.stop()
except Exception as e:
    st.error(
        "❌ Impossible de récupérer le profil utilisateur.\n"
        "Vérifiez que la table 'users' contient bien un enregistrement pour ce 'auth_user_id'."
    )
    st.exception(e)
    st.stop()
if not profile["active"]:
    st.error("⛔ Compte désactivé")
    st.stop()

username = profile["username"]
name = profile["name"]
role = profile["role"]

st.sidebar.success(f"{name} ({role})")
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state.clear()
    st.experimental_rerun()

# ------------------------
# PAGE SELECTION
# ------------------------
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

page_options = ["Dashboard"]
if role in ["admin", "super_admin"]:
    page_options += ["User Management", "Statistics", "Objectifs"]

st.session_state.page = st.sidebar.selectbox(
    "Menu",
    page_options,
    index=page_options.index(st.session_state.page)
)
page = st.session_state.page

# ------------------------
# OBJECTIFS PAGE
# ------------------------
if page == "Objectifs":
    from objectifs import run_objectifs
    run_objectifs()

# ------------------------
# USER MANAGEMENT
# ------------------------
if page == "User Management":
    st.subheader("👥 Gestion des utilisateurs")
    if SUPABASE_ONLINE:
        users_db = supabase.table("users").select("*").execute().data
    else:
        users_db = []
        st.warning("⚠️ Supabase indisponible (mode dégradé)")

    if not users_db:
        st.info("Aucun utilisateur disponible.")
    else:
        users_visible = [u for u in users_db if u.get("role") != "super_admin"]
        df_users = pd.DataFrame(users_visible)
        if "id" in df_users.columns:
            df_users.drop(columns="id", inplace=True)
        st.dataframe(df_users, use_container_width=True)

    # Ajouter / Réactiver utilisateur
    st.markdown("### ➕ Ajouter ou réactiver un utilisateur")
    with st.form("add_user_form"):
        new_username = st.text_input("Nom d'utilisateur")
        new_name = st.text_input("Nom complet")
        new_email = st.text_input("Email professionnel")
        if role == "super_admin":
            new_role = st.selectbox("Rôle", ["user", "admin", "super_admin"])
        else:
            new_role = st.selectbox("Rôle", ["user", "admin"])
        add_user = st.form_submit_button("Ajouter / Réactiver")

    if add_user:
        if not new_username or not new_email:
            st.warning("Nom d'utilisateur et email requis")
        else:
            exists = next((u for u in users_db if u["username"] == new_username), None)
            if exists:
                if exists["active"]:
                    st.warning("⚠️ Utilisateur déjà actif")
                else:
                    supabase.table("users").update({
                        "active": True,
                        "name": new_name,
                        "role": new_role
                    }).eq("username", new_username).execute()
                    st.success(f"Utilisateur {new_username} réactivé !")
            else:
                try:
                    auth_user = supabase.auth.admin.create_user({
                                "email": new_email,
                                "password": "MotDePasseTemp123!",  # obligatoire pour se connecter
                                "email_confirm": True
                            })                    
                    supabase.table("users").insert({
                        "auth_user_id": auth_user.user.id,
                        "email": new_email,
                        "username": new_username,
                        "name": new_name,
                        "role": new_role,
                        "active": True
                    }).execute()
                    st.success(f"Utilisateur {new_username} ajouté et invité !")
                except Exception as e:
                    st.error("❌ Impossible de créer l'utilisateur")
                    st.exception(e)

    # Désactiver utilisateur
    st.markdown("### ❌ Désactiver un utilisateur")
    active_usernames = [u["username"] for u in users_db if u["active"] and u.get("role") != "super_admin"]
    if active_usernames:
        del_username = st.selectbox("Sélectionner utilisateur à désactiver", active_usernames)
        if st.button("Désactiver"):
            if del_username == username:
                st.error("❌ Impossible de désactiver votre propre compte")
            else:
                role_to_delete = next(u["role"] for u in users_db if u["username"] == del_username)
                if role_to_delete == "admin":
                    st.error("❌ Impossible de désactiver un administrateur")
                else:
                    supabase.table("users").update({"active": False}).eq("username", del_username).execute()
                    st.success(f"Utilisateur {del_username} désactivé")

    # Reset password email
    st.markdown("### 🔑 Réinitialiser le mot de passe")
    reset_email = st.text_input("Email utilisateur")
    if st.button("Envoyer email de réinitialisation"):
        supabase.auth.reset_password_email(reset_email)
        st.success("📧 Email de réinitialisation envoyé")

    # Journaux d'activité
    st.markdown("### 📝 Journaux d'activité")
    if SUPABASE_ONLINE:
        logs = supabase.table("activity_logs").select("*").order("timestamp", desc=True).execute()
        df_logs = pd.DataFrame(logs.data)
    else:
        df_logs = pd.DataFrame()
        st.info("📝 Journaux indisponibles hors ligne")

    if df_logs.empty:
        st.info("Aucun journal disponible")
    st.dataframe(df_logs, use_container_width=True)

# ------------------------
# STATISTICS PAGE
# ------------------------
if page == "Statistics":
    st.subheader("📊 Statistiques Cliniques")
    if not SUPABASE_ONLINE:
        st.warning("📊 Statistiques indisponibles hors ligne")
        st.stop()

    records = supabase.table("indicateurs_cliniques").select("*").execute()
    df = pd.DataFrame(records.data)

    if df.empty:
        st.info("Aucune donnée clinique disponible pour le moment.")
        st.stop()

    df["registration_time"] = pd.to_datetime(df["registration_time"])

    # Filters
    st.markdown("### Filtrer les données")
    col1, col2, col3 = st.columns(3)
    with col1:
        date_min = df["registration_time"].min().date()
        date_max = df["registration_time"].max().date()
        date_range = st.date_input("Période", [date_min, date_max])
    with col2:
        patients = ["Tous"] + df["patient_first_name"].dropna().unique().tolist()
        selected_patient = st.selectbox("Patient", patients)
    with col3:
        metrics_options = ["Tous", "Incidents", "Erreurs", "Réadmissions"]
        selected_metric = st.selectbox("Métrique", metrics_options)

    start_date, end_date = date_range
    mask = (df["registration_time"].dt.date >= start_date) & (df["registration_time"].dt.date <= end_date)
    if selected_patient != "Tous":
        mask &= df["patient_first_name"] == selected_patient
    df_filtered = df[mask]

    if df_filtered.empty:
        st.warning("Aucune donnée pour ce filtre.")
        st.stop()

    # Metrics overview
    st.markdown("### ✅ Vue d'ensemble")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Nombre de patients", len(df_filtered))
    with col2: st.metric("Incidents signalés", df_filtered["incident"].sum())
    with col3: st.metric("Erreurs médicales", df_filtered["erreur_medicale"].sum())
    with col4: st.metric("Réadmissions", df_filtered["readmission"].sum())

    st.divider()

    # Pie chart: evolution
    st.markdown("### Évolution des patients")
    evolution_counts = df_filtered["evolution_patient"].value_counts().reset_index()
    evolution_counts.columns = ["Évolution", "Nombre"]
    fig_evolution = px.pie(evolution_counts, names="Évolution", values="Nombre", title="Répartition par évolution des patients")
    st.plotly_chart(fig_evolution, use_container_width=True)

    # Bar chart: incidents vs errors
    st.markdown("### Incidents vs Erreurs médicales")
    incidents_df = df_filtered.groupby(["incident", "erreur_medicale"]).size().reset_index(name="Nombre")
    fig_incidents = px.bar(
        incidents_df,
        x="incident",
        y="Nombre",
        color="erreur_medicale",
        labels={"incident": "Incident", "erreur_medicale": "Erreur médicale"},
        title="Nombre d'incidents par erreurs médicales"
    )
    st.plotly_chart(fig_incidents, use_container_width=True)

    # Histogram: duration of stay
    st.markdown("### Durée de séjour")
    fig_sejour = px.histogram(df_filtered, x="duree_sejour", nbins=20, title="Distribution des durées de séjour (jours)", labels={"duree_sejour": "Durée (jours)"})
    st.plotly_chart(fig_sejour, use_container_width=True)

    # Histogram: satisfaction patient
    st.markdown("### Satisfaction des patients")
    fig_satisfaction = px.histogram(df_filtered, x="satisfaction_patient", nbins=5, title="Distribution de la satisfaction patient", labels={"satisfaction_patient": "Satisfaction"})
    st.plotly_chart(fig_satisfaction, use_container_width=True)

    # Raw data
    st.markdown("### Données brutes")
    st.dataframe(df_filtered, use_container_width=True)# ------------------------
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

    col1, col2, col3 = st.columns(3)
    with col1:
        patient_sex = st.radio(
            "Sexe",
            ["Masculin", "Féminin"],
            horizontal=True,
            key="sex"
        )

    with col2:
        patient_unite = st.selectbox(
            "Unité",
            ["Hospitalisation", "HDJ"],
            key="unite"
        )

    with col3:
        date_hospitalisation = st.date_input(
            "Date d’hospitalisation",
            value=datetime.now().date(),
            key="date_hosp"
        )

    if patient_unite == "HDJ":
        from HDJ import run_HDJ
        run_HDJ()
        st.stop()

    patient_motif = st.text_area("Motif d’admission / Consultation", key="motif")
    patient_diagnosis = st.text_area("Diagnostic principal", key="diagnostic")

    st.caption(f"Date de saisie : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.divider()

    # ------------------------
    # QUALITÉ ET SÉCURITÉ DES SOINS
    # ------------------------
    st.subheader("🛡️ Qualité et sécurité des soins")

    incident = st.radio("Incident", ["Non", "Oui"], horizontal=True, key="incident")
    nb_incidents = None
    incident_description = ""
    if incident == "Oui":
        nb_incidents = st.number_input("Nombre d’incidents", min_value=1, step=1, key="nb_incidents")
        incident_description = st.text_area("Décrire l'incident", key="incident_desc")

    erreur_medicale = st.radio("Erreur médicale", ["Non", "Oui"], horizontal=True, key="erreur_medicale")
    nb_erreurs = None
    erreur_description = ""
    if erreur_medicale == "Oui":
        st.warning(
        "Une erreur médicale est l’échec d’une action planifiée à être menée comme prévu "
        "(erreur d’exécution), ou l’utilisation d’un mauvais plan pour atteindre un objectif "
        "(erreur de planification), pouvant entraîner ou non un préjudice pour le patient."
        )
        nb_erreurs = st.number_input("Nombre d’erreurs médicales", min_value=1, step=1, key="nb_erreurs")
        erreur_description = st.text_area("Décrire l’erreur médicale", key="erreur_desc")

    # ------------------------
    # Nouveaux indicateurs
    # ------------------------
    readmission = st.radio("Réadmission", ["Non", "Oui"], horizontal=True, key="readmission")
    readmission_type = None
    if readmission == "Oui":
        readmission_type = st.radio("Cause de la réadmission", ["PEC incomplète", "Complication"], key="readmission_type")

    infection_soins = st.radio("Infections liées aux soins", ["Non", "Oui"], horizontal=True, key="infection")
    infection_description = ""
    if infection_soins == "Oui":
        infection_description = st.text_area("Préciser l’infection liée aux soins", key="infection_desc")

    effets_graves = st.radio("Effets indésirables graves", ["Non", "Oui"], horizontal=True, key="effets")
    effets_graves_description = ""
    if effets_graves == "Oui":
        st.warning(
        "Un effet indésirable grave est un effet indésirable qui, quelle que soit la dose administrée, "
        "entraîne la mort, met la vie en danger, nécessite une hospitalisation ou la prolonge, "
        "provoque une incapacité ou un handicap significatif ou durable, "
        "ou entraîne une anomalie congénitale ou une malformation."
        )
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

    remission_type = echec_traitement = cause_echec = rechute = cause_rechute = mortalite_cause = ""
    types_echec = []
    causes_echec = []

    # ------------------------
    # RÉMISSION
    # ------------------------
    remission_type = ""
    echec_traitement = ""
    cause_echec = ""
    rechute = ""
    cause_rechute = ""
    mortalite_cause = ""
    types_echec = []
    causes_echec = []
    types_rechute = []
    delai_survenue = []
    cause_principale_rechute = []
    autres_rechute = ""

    if evolution_patient == "Rémission":
        remission_type = st.selectbox("Type de rémission", ["Complète", "Partielle"], key="rem_type")

    # ------------------------
    # ÉCHEC DE TRAITEMENT
    # ------------------------
    elif evolution_patient == "Échec de traitement":
        st.warning(
            "Échec thérapeutique : absence d’amélioration clinique et/ou biologique attendue, "
            "ou aggravation de la pathologie, après un traitement conforme aux recommandations, "
            "administré à dose adéquate, sur une durée suffisante, avec une observance jugée correcte.\n\n"
            "Attention : Un échec doit toujours faire analyser :\n"
            "• Observance insuffisante\n"
            "• Posologie inadaptée\n"
            "• Résistance au traitement\n"
            "• Mauvais diagnostic initial\n"
            "• Comorbidités ou interactions médicamenteuses"
        )

        echec_traitement = st.radio("Échec confirmé ?", ["Oui", "Non"], horizontal=True, key="echec")

        if echec_traitement == "Oui":
            st.markdown("**Types d’échec retenus**")
            if st.checkbox("Échec clinique"):
                types_echec.append("Clinique")
            if st.checkbox("Échec biologique"):
                types_echec.append("Biologique")
            if st.checkbox("Échec radiologique"):
                types_echec.append("Radiologique")
            if st.checkbox("Échec thérapeutique (changement ou intensification du traitement)"):
                types_echec.append("Thérapeutique")
            if st.checkbox("Échec composite (≥ 2 critères)"):
                types_echec.append("Composite")

            st.markdown("**Causes de l’échec**")
            if st.checkbox("Mauvais diagnostic initial"):
                causes_echec.append("Mauvais diagnostic initial")
            if st.checkbox("Retard thérapeutique"):
                causes_echec.append("Retard thérapeutique")
            if st.checkbox("Résistance / inefficacité pharmacologique"):
                causes_echec.append("Résistance / inefficacité pharmacologique")
            if st.checkbox("Comorbidité intercurrente"):
                causes_echec.append("Comorbidité intercurrente")
            if st.checkbox("Non-observance"):
                causes_echec.append("Non-observance")
            if st.checkbox("Effet indésirable limitant"):
                causes_echec.append("Effet indésirable limitant")

    # ------------------------
    # RECHUTE
    # ------------------------
    elif evolution_patient == "Rechute":
        st.warning(
            "Rechute :\n"
            "Définition : réapparition de signes cliniques, biologiques et/ou radiologiques de la maladie après une réponse initiale complète ou partielle documentée, nécessitant une réintroduction, une intensification ou une modification du traitement.\n"
            "Attention : La rechute se distingue de l’échec thérapeutique par l’existence obligatoire d’une phase d’amélioration préalable.\n"
            "Conditions préalables (OBLIGATOIRES)\n"
            "✔ Réponse thérapeutique initiale documentée\n"
            "✔ Stabilisation clinique et/ou biologique\n"
            "✔ Traitement de fond instauré ou suivi organisé"
        )

        rechute = st.radio("Rechute ?", ["Oui", "Non"], horizontal=True, key="rechute")
        types_rechute = []
        delai_survenue = []
        cause_principale_rechute = []
        autres_rechute = ""

        if rechute == "Oui":
            st.markdown("**Types de rechute retenus**")
            if st.checkbox("Rechute clinique"):
                types_rechute.append("Clinique")
            if st.checkbox("Rechute biologique"):
                types_rechute.append("Biologique")
            if st.checkbox("Rechute radiologique"):
                types_rechute.append("Radiologique")
            if st.checkbox("Rechute thérapeutique (réintroduction / escalade)"):
                types_rechute.append("Thérapeutique")
            if st.checkbox("Rechute composite (≥ 2 critères)"):
                types_rechute.append("Composite")

            st.markdown("**Délai de survenue**")
            if st.checkbox("< 3 mois"):
                delai_survenue.append("<3 mois")
            if st.checkbox("3–6 mois"):
                delai_survenue.append("3–6 mois")
            if st.checkbox("6–12 mois"):
                delai_survenue.append("6–12 mois")
            if st.checkbox("> 12 mois"):
                delai_survenue.append(">12 mois")

            st.markdown("**Cause principale**")
            if st.checkbox("Non-observance secondaire"):
                cause_principale_rechute.append("Non-observance secondaire")
            if st.checkbox("Sevrage ou dégression trop rapide"):
                cause_principale_rechute.append("Sevrage ou dégression trop rapide")
            if st.checkbox("Maladie active sous-jacente"):
                cause_principale_rechute.append("Maladie active sous-jacente")
            if st.checkbox("Traitement de fond insuffisant"):
                cause_principale_rechute.append("Traitement de fond insuffisant")
            if st.checkbox("Facteur déclenchant intercurrent (infection, stress…)"):
                cause_principale_rechute.append("Facteur déclenchant intercurrent")
            autres_rechute = st.text_area("Autres causes", key="autres_rechute")

    # ------------------------
    # MORTALITÉ
    # ------------------------
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
    # ------------------------
# SATISFACTION DES PATIENTS
# ------------------------
    st.subheader("😊 Satisfaction des Patients")
    satisfaction_patient = st.slider("Satisfaction patient", 1, 5, 3, key="satisf")

    plaintes_reclamations = st.radio(
        "Plaintes ou réclamations reçues résolues ?", ["Oui", "Non"], horizontal=True, key="plaintes"
    )

    plaintes_description = ""
    if plaintes_reclamations == "Oui":
        plaintes_description = st.text_area(
            "Préciser la/les plainte(s) ou réclamation(s)", key="plaintes_desc"
        )

# ------------------------
# OBSERVANCE THÉRAPEUTIQUE
# ------------------------
    st.subheader("💊 Observance thérapeutique")

    st.markdown("**Compréhension du traitement**")
    obs_comp_80 = st.checkbox("Le patient peut citer au moins 80 % de son traitement", key="obs_comp_80")
    obs_indication = st.checkbox("Il comprend l’indication et la durée", key="obs_indication")
    obs_effets = st.checkbox("Il connaît les principaux effets indésirables", key="obs_effets")

    st.markdown("---\n**Acceptation / adhésion**")
    obs_accord = st.checkbox("Le patient est d’accord avec le traitement", key="obs_accord")
    obs_refus = st.checkbox("Pas de refus exprimé", key="obs_refus")
    obs_crainte = st.checkbox("Pas de crainte majeure non levée", key="obs_crainte")

    st.markdown("---\n**Faisabilité**")
    obs_dispo = st.checkbox("Traitement disponible / accessible", key="obs_dispo")
    obs_cout = st.checkbox("Coût compatible", key="obs_cout")
    obs_schema = st.checkbox("Schéma thérapeutique compréhensible", key="obs_schema")
    obs_barriere = st.checkbox("Pas de barrière cognitive majeure", key="obs_barriere")


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
        # Convert lists to comma-separated strings
        types_echec_str = ", ".join(types_echec) if types_echec else None
        causes_echec_str = ", ".join(causes_echec) if causes_echec else None
        types_rechute_str = ", ".join(types_rechute) if types_rechute else None
        delai_survenue_str = ", ".join(delai_survenue) if delai_survenue else None
        cause_principale_rechute_str = ", ".join(cause_principale_rechute) if cause_principale_rechute else None

        # Ensure booleans are real bool types
        examens_bio_redondants = bool(examens_bio_redondants)
        examens_bio_non_pertinents = bool(examens_bio_non_pertinents)
        obs_comp_80 = bool(obs_comp_80)
        obs_indication = bool(obs_indication)
        obs_effets = bool(obs_effets)
        obs_accord = bool(obs_accord)
        obs_refus = bool(obs_refus)
        obs_crainte = bool(obs_crainte)
        obs_dispo = bool(obs_dispo)
        obs_cout = bool(obs_cout)
        obs_schema = bool(obs_schema)
        obs_barriere = bool(obs_barriere)

        record = {
            "patient_first_name": patient_first_name.lower() or None,
            "patient_last_name": patient_last_name.upper() or None,
            "patient_age": int(patient_age) if patient_age else None,
            "patient_sex": patient_sex or None,
            "patient_unite": patient_unite or None,
            "date_hospitalisation": date_hospitalisation.isoformat() if date_hospitalisation else None,
            "patient_motif": patient_motif or None,
            "patient_diagnosis": patient_diagnosis or None,
            "incident": incident == "Oui",
            "nb_incidents": int(nb_incidents) if nb_incidents else None,
            "incident_description": incident_description or None,
            "erreur_medicale": erreur_medicale == "Oui",
            "nb_erreurs": int(nb_erreurs) if nb_erreurs else None,
            "erreur_description": erreur_description or None,
            "readmission": readmission == "Oui",
            "readmission_type": readmission_type or None,
            "infection_soins": infection_soins == "Oui",
            "infection_description": infection_description or None,
            "effets_graves": effets_graves == "Oui",
            "effets_graves_description": effets_graves_description or None,
            "delai_admission": int(delai_admission) if delai_admission else None,
            "duree_sejour": int(duree_sejour) if duree_sejour else None,
            "cause_long_sejour": cause_long_sejour or None,
            "diagnostic_etabli": diagnostic_etabli == "Oui",
            "dossier_complet": dossier_complet == "Oui",
            "cause_dossier_incomplet": cause_dossier_incomplet or None,
            "evolution_patient": evolution_patient or None,
            "types_echec": types_echec_str,
            "causes_echec": causes_echec_str,
            "rechute": rechute == "Oui" if rechute else None,
            "types_rechute": types_rechute_str,
            "delai_survenue": delai_survenue_str,
            "cause_principale_rechute": cause_principale_rechute_str,
            "autres_rechute": autres_rechute or None,
            "cause_rechute": cause_rechute or None,
            "mortalite_cause": mortalite_cause or None,
            "pertinence_bio": pertinence_bio == "Oui",
            "examens_bio_redondants": examens_bio_redondants,
            "examens_bio_non_pertinents": examens_bio_non_pertinents,
            "pertinence_imagerie": pertinence_imagerie == "Oui",
            "satisfaction_patient": int(satisfaction_patient),
            "plaintes_reclamations": plaintes_reclamations == "Oui",
            "plaintes_description": plaintes_description or None,
            "obs_comp_80": obs_comp_80,
            "obs_indication": obs_indication,
            "obs_effets": obs_effets,
            "obs_accord": obs_accord,
            "obs_refus": obs_refus,
            "obs_crainte": obs_crainte,
            "obs_dispo": obs_dispo,
            "obs_cout": obs_cout,
            "obs_schema": obs_schema,
            "obs_barriere": obs_barriere,
            "telemedecine": telemedecine == "Oui",
            "registration_time": datetime.now().isoformat()
        }

        # ------------------------
        # Try sending to Supabase if online
        # ------------------------
        
        try:
                # Insert main record
                supabase.table("indicateurs_cliniques").insert(record).execute()
                supabase.table("activity_logs").insert({
                    "username": username,
                    "action": f"Enregistrement patient {patient_first_name} {patient_last_name}",
                    "timestamp": datetime.now().isoformat()
                }).execute()

                st.success(f"✅ Données envoyées pour {patient_first_name} {patient_last_name}")

                # Sync any cached records
                if os.path.exists(LOCAL_FILE):
                    with open(LOCAL_FILE, "r") as f:
                        cached_records = json.load(f)
                    for r in cached_records:
                        supabase.table("indicateurs_cliniques").insert(r).execute()
                    os.remove(LOCAL_FILE)
                    st.info("📤 Données locales synchronisées automatiquement")

        except Exception as e:
                st.warning("⚠️ Connexion perdue, données stockées localement")
                save_locally(record)
        



