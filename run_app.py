# run_app.py
import streamlit as st
from datetime import datetime

# ------------------------
# PAGE CONFIG
# ------------------------
st.set_page_config(page_title="Indicateurs de Suivi", layout="wide")
st.title("📊 Indicateurs de Suivi Clinique")

# ------------------------
# INFORMATIONS PATIENT
# ------------------------
st.subheader("👤 Informations patient")

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

st.caption(f"Date de saisie : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.divider()

# ==================================================
# QUALITÉ ET SÉCURITÉ DES SOINS
# ==================================================
st.subheader("🛡️ Qualité et sécurité des soins")

# Incidents / erreurs médicales
incident = st.radio("Incidents / erreurs médicales", ["Non", "Oui"], horizontal=True, key="incident")
nb_incidents = None
if incident == "Oui":
    nb_incidents = st.number_input("Nombre d’incidents / erreurs", min_value=1, step=1, key="nb_incidents")

# Réadmission
readmission = st.radio("Réadmission", ["Non", "Oui"], horizontal=True, key="readmission")
readmission_type = None
if readmission == "Oui":
    readmission_type = st.radio(
        "Cause de la réadmission",
        ["PEC incomplète", "Complication"],
        key="readmission_type"
    )

# Infections liées aux soins
infection_soins = st.radio("Infections liées aux soins", ["Non", "Oui"], horizontal=True, key="infection_soins")
infection_description = ""
if infection_soins == "Oui":
    infection_description = st.text_area(
        "Préciser l’infection liée aux soins",
        key="infection_description"
    )

# Effets indésirables graves
effets_graves = st.radio("Effets indésirables graves", ["Non", "Oui"], horizontal=True, key="effets_graves")
effets_graves_description = ""
if effets_graves == "Oui":
    effets_graves_description = st.text_area(
        "Décrire les effets indésirables graves",
        key="effets_graves_description"
    )

st.divider()

# ==================================================
# PERFORMANCE CLINIQUE
# ==================================================
st.subheader("💊 Performance clinique")

delai_admission = st.number_input(
    "Délai d’admission / prise en charge (jours)",
    min_value=0,
    step=1,
    key="delai_admission"
)
duree_sejour = st.number_input(
    "Durée du séjour (jours)",
    min_value=0,
    step=1,
    key="duree_sejour"
)
cause_long_sejour = ""
if duree_sejour > 10:
    cause_long_sejour = st.text_area(
        "Cause du séjour > 10 jours",
        key="cause_long_sejour"
    )

diagnostic_etabli = st.radio(
    "Patient sorti avec diagnostic établi ?",
    ["Oui", "Non"],
    horizontal=True,
    key="diagnostic_etabli"
)

dossier_complet = st.radio(
    "Dossier complet avec diagnostic ?",
    ["Oui", "Non"],
    horizontal=True,
    key="dossier_complet"
)
cause_dossier_incomplet = ""
if dossier_complet == "Non":
    cause_dossier_incomplet = st.text_area(
        "Si Non, indiquer les éléments manquants",
        key="cause_dossier_incomplet"
    )

evolution_patient = st.selectbox(
    "Évolution du patient",
    ["Rémission", "Échec de traitement", "Rechute", "Mortalité"],
    key="evolution_patient"
)

# Sous-options selon évolution
remission_type = ""
if evolution_patient == "Rémission":
    remission_type = st.selectbox(
        "Type de rémission",
        ["Complète", "Partielle"],
        key="remission_type"
    )

echec_traitement = ""
cause_echec = ""
if evolution_patient == "Échec de traitement":
    echec_traitement = st.radio("Échec confirmé ?", ["Oui", "Non"], horizontal=True, key="echec_traitement")
    if echec_traitement == "Oui":
        cause_echec = st.text_area("Cause de l’échec de traitement", key="cause_echec")

rechute = ""
cause_rechute = ""
if evolution_patient == "Rechute":
    rechute = st.radio("Rechute ?", ["Oui", "Non"], horizontal=True, key="rechute")
    if rechute == "Oui":
        cause_rechute = st.text_area("Préciser la cause de la rechute", key="cause_rechute")

mortalite_cause = ""
if evolution_patient == "Mortalité":
    mortalite_cause = st.text_area("Préciser la cause du décès", key="mortalite_cause")

st.divider()

# ==================================================
# PERTINENCE DES SOINS
# ==================================================
st.subheader("📈 Pertinence des soins")

pertinence_bio = st.radio(
    "Pertinence des examens biologiques ?",
    ["Oui", "Non"],
    horizontal=True,
    key="pertinence_bio"
)
examens_bio_redondants = examens_bio_non_pertinents = False
if pertinence_bio == "Oui":
    examens_bio_redondants = st.checkbox("Examens redondants", key="examens_bio_redondants")
    examens_bio_non_pertinents = st.checkbox("Non pertinents", key="examens_bio_non_pertinents")

pertinence_imagerie = st.radio(
    "Pertinence des examens d’imagerie ?",
    ["Oui", "Non"],
    horizontal=True,
    key="pertinence_imagerie"
)

st.divider()

# ==================================================
# SATISFACTION DES PATIENTS
# ==================================================
st.subheader("😊 Satisfaction des Patients")

satisfaction_patient = st.slider("Satisfaction patient", 1, 5, 3, key="satisfaction_patient")
plaintes_reclamations = st.radio(
    "Plaintes ou réclamations reçues ? Résolu ?",
    ["Non", "Oui"],
    horizontal=True,
    key="plaintes_reclamations"
)

st.divider()

# ==================================================
# INNOVATION ET HUMANISATION
# ==================================================
st.subheader("🏥 Innovation et Humanisation")

telemedecine_acces = st.radio(
    "Patient ayant accès à la télémédecine ou suivi à distance ?",
    ["Non", "Oui"],
    horizontal=True,
    key="telemedecine_acces"
)

st.divider()

# ------------------------
# SUBMIT (UI ONLY)
# ------------------------
if st.button("💾 Enregistrer (interface uniquement)"):
    st.success("✅ Formulaire validé (aucune donnée enregistrée)")
    st.info("📌 La base de données sera ajoutée ultérieurement")

    st.subheader("👁️ Aperçu des données saisies")
    st.json({
        "Prénom": patient_first_name,
        "Nom": patient_last_name,
        "Âge": patient_age,
        "Sexe": patient_sex,
        "Service": patient_service,
        "Motif": patient_motif,
        "Diagnostic principal": patient_diagnosis,
        "Incident médical": incident,
        "Nombre incidents": nb_incidents,
        "Réadmission": readmission,
        "Cause réadmission": readmission_type,
        "Infection liée aux soins": infection_soins,
        "Description infection": infection_description,
        "Effets indésirables graves": effets_graves,
        "Description effets graves": effets_graves_description,
        "Délai admission": delai_admission,
        "Durée séjour": duree_sejour,
        "Cause séjour long": cause_long_sejour,
        "Diagnostic établi": diagnostic_etabli,
        "Dossier complet": dossier_complet,
        "Cause dossier incomplet": cause_dossier_incomplet,
        "Évolution": evolution_patient,
        "Type rémission": remission_type,
        "Échec traitement": echec_traitement,
        "Cause échec": cause_echec,
        "Rechute": rechute,
        "Cause rechute": cause_rechute,
        "Mortalité cause": mortalite_cause,
        "Pertinence bio": pertinence_bio,
        "Examens bio redondants": examens_bio_redondants,
        "Examens bio non pertinents": examens_bio_non_pertinents,
        "Pertinence imagerie": pertinence_imagerie,
        "Satisfaction patient": satisfaction_patient,
        "Plaintes ou réclamations": plaintes_reclamations,
        "Accès télémédecine": telemedecine_acces
    })
