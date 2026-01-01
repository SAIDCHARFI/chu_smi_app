# run_app.py
import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# ------------------------
# PAGE CONFIG
# ------------------------
st.set_page_config(page_title="Indicateurs de Suivi", layout="wide")
st.title("📊 Indicateurs de Suivi Clinique")

# ------------------------
# SUPABASE CLIENT
# ------------------------
SUPABASE_URL = "https://pvjdgddzuzarygaxyxuw.supabase.co"
SUPABASE_KEY = "sb_publishable_ilPGwOE_zkgfeqp-PosqPA_7mxrgfbF"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------
# FORM START
# ------------------------
st.subheader("👤 Informations patient")
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
if evolution_patient == "Rémission":
    remission_type = st.selectbox("Type de rémission", ["Complète", "Partielle"], key="rem_type")

echec_traitement = ""
cause_echec = ""
if evolution_patient == "Échec de traitement":
    echec_traitement = st.radio("Échec confirmé ?", ["Oui", "Non"], horizontal=True, key="echec")
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
    mortalite_cause = st.text_area("Préciser la cause du décès", key="mort_cause")

st.divider()

# ------------------------
# PERTINENCE DES SOINS
# ------------------------
st.subheader("📈 Pertinence des soins")

# Corrected logic: if Non, show redondants / non pertinents
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
        "username": "current_user",
        "action": f"Enregistrement patient {patient_first_name} {patient_last_name}",
        "timestamp": datetime.now().isoformat()
    }).execute()
    st.success(f"✅ Données enregistrées pour {patient_first_name} {patient_last_name}")
