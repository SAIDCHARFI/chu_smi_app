# run_app.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import yaml
import streamlit_authenticator as stauth
from datetime import datetime
import plotly.express as px
from io import BytesIO
import psycopg2
st.write("psycopg2 imported successfully")
# ------------------------
# PAGE CONFIG
# ------------------------
st.set_page_config(page_title="Indicateurs de Suivi", layout="wide")

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
# DATABASE SETUP (PostgreSQL)
# ------------------------
@st.cache_resource
def get_engine():
    return create_engine(
        st.secrets["DATABASE_URL"],
        pool_pre_ping=True,
        future=True
    )

engine = get_engine()

# ------------------------
# CREATE TABLES
# ------------------------
try:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS indicateurs_cliniques (
                id SERIAL PRIMARY KEY,
                patient_first_name TEXT,
                patient_last_name TEXT,
                registration_time TIMESTAMPTZ,
                delai_diagnostic INTEGER,
                pertinence_exam_bio INTEGER,
                pertinence_exam_imagerie INTEGER,
                utilisation_corticoides INTEGER,
                delai_introduction_ims_biotherapies INTEGER,
                effets_indesirables_medicamenteux INTEGER,
                adhesion_recommandations INTEGER,
                remission INTEGER,
                rechute INTEGER,
                duree_sejour INTEGER,
                mortalite INTEGER,
                infections_associees_soins INTEGER,
                infections_opportunistes INTEGER,
                rehosp_complication INTEGER,
                rehosp_pec_incomplete INTEGER,
                rehosp_autres INTEGER,
                duree_moyenne_sejour REAL,
                delai_realisation_examens INTEGER,
                taux_hospitalisation_prolongee REAL,
                qualite_tracabilite_dossiers INTEGER,
                satisfaction_patient INTEGER,
                observance_therapeutique INTEGER,
                education_therapeutique INTEGER
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                username TEXT,
                action TEXT,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            )
        """))
except SQLAlchemyError as e:
    st.error(f"❌ Database initialization error: {e}")
    st.stop()

# ------------------------
# ADMIN MENU
# ------------------------
if role == "admin":
    page = st.sidebar.selectbox("Menu", ["Dashboard", "User Management", "Statistics"])
else:
    page = "Dashboard"

# ------------------------
# DASHBOARD
# ------------------------
if page == "Dashboard":
    st.subheader("👤 Informations patient")

    with st.form("form_indicateurs"):
        patient_first_name = st.text_input("Prénom du patient")
        patient_last_name = st.text_input("Nom du patient")
        registration_time = datetime.utcnow()

        delai_diagnostic = st.number_input("Délai diagnostic (jours)", min_value=0)
        bio = st.checkbox("Examens biologiques pertinents")
        imagerie = st.checkbox("Examens d’imagerie pertinents")

        corticoides = st.checkbox("Utilisation des corticoïdes")
        effets = st.checkbox("Effets indésirables médicamenteux")
        adhesion = st.checkbox("Adhésion aux recommandations")
        delai_ims = st.number_input("Délai introduction IMS / biothérapies (jours)", min_value=0)

        remission = st.checkbox("Rémission")
        rechute = st.checkbox("Rechute")
        duree_sejour = st.number_input("Durée du séjour (jours)", min_value=0)
        mortalite = st.checkbox("Décès")

        submit = st.form_submit_button("💾 Enregistrer")

        if submit:
            df = pd.DataFrame([{
                "patient_first_name": patient_first_name,
                "patient_last_name": patient_last_name,
                "registration_time": registration_time,
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
                "mortalite": int(mortalite)
            }])

            df.to_sql("indicateurs_cliniques", engine, if_exists="append", index=False)

            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO activity_logs (username, action) VALUES (:u, :a)"),
                    {"u": username, "a": f"Submitted data for {patient_first_name} {patient_last_name}"}
                )

            st.success("✅ Données enregistrées")

# ------------------------
# DATA VIEW
# ------------------------
st.divider()
df_db = pd.read_sql("SELECT * FROM indicateurs_cliniques ORDER BY registration_time DESC", engine)
st.dataframe(df_db, use_container_width=True)

# ------------------------
# EXPORT
# ------------------------
st.subheader("💾 Exporter les données")
export_format = st.radio("Format d'export", ["CSV", "Excel"], horizontal=True)

if st.button("Exporter"):
    if export_format == "CSV":
        st.download_button(
            "Télécharger CSV",
            df_db.to_csv(index=False),
            "indicateurs_cliniques.csv",
            "text/csv"
        )
    else:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_db.to_excel(writer, index=False)
        st.download_button(
            "Télécharger Excel",
            output.getvalue(),
            "indicateurs_cliniques.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
