# run_app.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import yaml
import streamlit_authenticator as stauth
from datetime import datetime
import plotly.express as px

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
# DATABASE SETUP
# ------------------------
#DB_URL = "sqlite:///clinical_indicators.db"
# ------------------------
# DATABASE SETUP
# ------------------------
@st.cache_resource
def get_engine():
    return create_engine(
        st.secrets["DATABASE_URL"],
        pool_pre_ping=True
    )

engine = get_engine()

# Clinical indicators table
try:
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS indicateurs_cliniques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_first_name TEXT,
                patient_last_name TEXT,
                registration_time DATETIME,
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
        conn.commit()
except SQLAlchemyError as e:
    st.error(f"❌ Erreur lors de la création de la table : {e}")
    st.stop()

# Activity logs table
try:
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                username TEXT,
                action TEXT,
                timestamp TIMESTAMPTZ DEFAULT NOW()
                )
        """))
        conn.commit()
except SQLAlchemyError as e:
    st.error(f"❌ Erreur lors de la création des logs : {e}")
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
    df_logs = pd.read_sql("SELECT * FROM activity_logs ORDER BY timestamp DESC", engine)
    st.dataframe(df_logs, use_container_width=True)

# ------------------------
# STATISTICS (ADMIN)
# ------------------------
if page == "Statistics":
    st.subheader("📊 Statistiques des indicateurs")
    df_db = pd.read_sql("SELECT * FROM indicateurs_cliniques", engine)
    if df_db.empty:
        st.info("Aucune donnée enregistrée pour afficher des statistiques")
    else:
        numeric_cols = df_db.select_dtypes(include=["int64", "float64"]).columns.tolist()
        if numeric_cols:
            # Mean per indicator
            mean_df = df_db[numeric_cols].mean().reset_index()
            mean_df.columns = ["Indicateur", "Moyenne"]
            fig_bar = px.bar(mean_df, x="Indicateur", y="Moyenne", title="Moyennes des indicateurs")
            st.plotly_chart(fig_bar, use_container_width=True)

            # Distribution histograms
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
            }])
            try:
                df.to_sql("indicateurs_cliniques", engine, if_exists="append", index=False)
                with engine.connect() as conn:
                    conn.execute(
                        text("INSERT INTO activity_logs (username, action) VALUES (:user, :action)"),
                        {"user": username, "action": f"Submitted clinical indicators for {patient_first_name} {patient_last_name}"}
                    )
                    conn.commit()
                st.success(f"✅ Données enregistrées pour {patient_first_name} {patient_last_name}")
            except SQLAlchemyError as e:
                st.error(f"❌ Erreur DB : {e}")

    # Display saved data
    st.divider()
    st.subheader("📋 Données enregistrées")
    df_db = pd.read_sql("SELECT * FROM indicateurs_cliniques ORDER BY registration_time DESC", engine)
    if not df_db.empty:
        filter_column = st.selectbox("Filtrer par colonne", df_db.columns)
        if filter_column:
            unique_values = df_db[filter_column].unique()
            selected_values = st.multiselect(f"Sélectionner {filter_column}", unique_values, default=unique_values)
            df_db = df_db[df_db[filter_column].isin(selected_values)]
        st.dataframe(df_db, use_container_width=True)

    # Export options
    from io import BytesIO

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
