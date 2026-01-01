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
# SELECT PAGE
# ------------------------
if role == "admin":
    page = st.sidebar.selectbox("Menu", ["Dashboard", "User Management", "Statistics"], key="admin_menu")
else:
    page = "Dashboard"

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
        new_username = st.text_input("Nom d'utilisateur", key="new_username")
        new_name = st.text_input("Nom complet", key="new_name")
        new_password = st.text_input("Mot de passe", type="password", key="new_password")
        new_role = st.selectbox("Rôle", ["user", "admin"], key="new_role")
        add_user = st.form_submit_button("Ajouter", key="add_user_form_submit")
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
    del_username = st.selectbox("Sélectionner utilisateur à supprimer", df_users["username"], key="del_username")
    if st.button("Supprimer", key="delete_user_button"):
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
    # ENREGISTRER LE PATIENT
    # ------------------------
    if st.button("💾 Enregistrer", key="save_patient_dashboard"):
        record = {
            "patient_first_name": patient_first_name or None,
            "patient_last_name": patient_last_name or None,
            "patient_age": patient_age,
            "patient_sex": patient_sex or None,
            "patient_service": patient_service or None,
            "patient_motif": patient_motif or None,
            "patient_diagnosis": patient_diagnosis or None,
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
    # AFFICHER LES 10 DERNIERS PATIENTS AVEC FILTRES
    # ------------------------
    st.subheader("🗂️ Derniers patients enregistrés")

    # Récupérer tous les enregistrements
    all_records = supabase.table("indicateurs_cliniques") \
        .select("*") \
        .order("registration_time", desc=True) \
        .execute().data

    if all_records:
        df_all = pd.DataFrame(all_records)

        # --- FILTRES ---
        st.markdown("### 🔍 Filtrer les patients")
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_service = st.selectbox("Service / Unité", options=["Tous"] + df_all["patient_service"].dropna().unique().tolist(), key="filter_service")
        with col2:
            filter_sex = st.selectbox("Sexe", options=["Tous"] + df_all["patient_sex"].dropna().unique().tolist(), key="filter_sex")
        with col3:
            filter_evolution = st.selectbox("Évolution du patient", options=["Tous"] + df_all.get("evolution_patient", pd.Series([])).dropna().unique().tolist(), key="filter_evolution")

        df_filtered = df_all.copy()
        if filter_service != "Tous":
            df_filtered = df_filtered[df_filtered["patient_service"] == filter_service]
        if filter_sex != "Tous":
            df_filtered = df_filtered[df_filtered["patient_sex"] == filter_sex]
        if filter_evolution != "Tous" and "evolution_patient" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["evolution_patient"] == filter_evolution]

        # Afficher max 10 derniers
        st.dataframe(df_filtered.head(10), use_container_width=True)

        # --- TELECHARGEMENT DE TOUS LES PATIENTS ---
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
