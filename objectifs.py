import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from io import BytesIO
from datetime import timedelta

# ------------------------
# SUPABASE CLIENT
# ------------------------
SUPABASE_URL = st.secrets["SUPABASE"]["URL"]
SUPABASE_KEY = st.secrets["SUPABASE"]["KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ------------------------
# UTILS
# ------------------------
def safe_pct(num, den):
    return (num / den * 100) if den else 0


def trend(current, previous):
    if previous == 0:
        return "➡️ Stable"
    diff = current - previous
    if diff > 0:
        return "🔺 En hausse"
    elif diff < 0:
        return "🔻 En baisse"
    return "➡️ Stable"


def status_threshold(value, target, mode="lt"):
    if mode == "lt":  # value < target
        return "🟢 Conforme" if value < target else "🔴 Non conforme"
    else:  # value > target
        return "🟢 Conforme" if value > target else "🔴 Non conforme"


# ------------------------
# MAIN FUNCTION
# ------------------------
def run_objectifs():
    st.subheader("🎯 Objectifs & Indicateurs Cliniques")

    # ------------------------
    # LOAD DATA
    # ------------------------
    records = supabase.table("indicateurs_cliniques").select("*").execute().data
    if not records:
        st.info("Aucune donnée disponible.")
        return

    df = pd.DataFrame(records)
    df["registration_time"] = pd.to_datetime(df["registration_time"], errors="coerce")

    # ------------------------
    # FILTERS
    # ------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        start_date = st.date_input(
            "Date début", df["registration_time"].min().date()
        )
    with col2:
        end_date = st.date_input(
            "Date fin", df["registration_time"].max().date()
        )
    with col3:
        service = st.text_input("Service (optionnel)")

    df_period = df[
        (df["registration_time"].dt.date >= start_date)
        & (df["registration_time"].dt.date <= end_date)
    ]

    if service:
        df_period = df_period[
            df_period["patient_service"].str.contains(service, case=False, na=False)
        ]

    # période précédente (pour tendance)
    delta = (end_date - start_date).days or 1
    prev_start = start_date - timedelta(days=delta)
    prev_end = start_date

    df_prev = df[
        (df["registration_time"].dt.date >= prev_start)
        & (df["registration_time"].dt.date < prev_end)
    ]

    # ------------------------
    # COUNTS
    # ------------------------
    total = len(df_period)

    nb_incidents = df_period["nb_incidents"].fillna(0).sum()
    nb_ias = (df_period["infection_soins"] == "Oui").sum()
    nb_readm = (df_period["readmission"] == "Oui").sum()
    nb_dossiers_ok = (df_period["dossier_complet"] == "Oui").sum()
    nb_effets_graves = (df_period["effets_graves"] == "Oui").sum()
    delai_moyen = df_period["delai_admission"].mean()
    nb_diag_ok = (df_period["diagnostic_etabli"] == "Oui").sum()
    nb_plaintes = (df_period["plaintes_reclamations"] == "Oui").sum()

    evol = df_period["evolution_patient"].value_counts()

    # période précédente
    total_prev = len(df_prev)
    prev_vals = {
        "effets": (df_prev["effets_graves"] == "Oui").sum(),
        "plaintes": (df_prev["plaintes_reclamations"] == "Oui").sum(),
        "remission": (df_prev["evolution_patient"] == "Rémission").sum(),
        "echec": (df_prev["evolution_patient"] == "Échec de traitement").sum(),
        "rechute": (df_prev["evolution_patient"] == "Rechute").sum(),
        "mort": (df_prev["evolution_patient"] == "Mortalité").sum(),
    }

    # ------------------------
    # KPI VALUES
    # ------------------------
    kpis = [
        ("Taux d'incidents (%)", safe_pct(nb_incidents, total), "< 2 %", status_threshold(safe_pct(nb_incidents, total), 2, "lt")),
        ("Taux IAS (%)", safe_pct(nb_ias, total), "< 3 %", status_threshold(safe_pct(nb_ias, total), 3, "lt")),
        ("Taux de réadmission (%)", safe_pct(nb_readm, total), "< 10 %", status_threshold(safe_pct(nb_readm, total), 10, "lt")),
        ("Traçabilité dossiers (%)", safe_pct(nb_dossiers_ok, total), "> 95 %", status_threshold(safe_pct(nb_dossiers_ok, total), 95, "gt")),
        ("Délai moyen admission (jours)", delai_moyen, "< 30", status_threshold(delai_moyen, 30, "lt")),
        ("Dossiers complets avec diagnostic (%)", safe_pct(nb_diag_ok, total), "> 90 %", status_threshold(safe_pct(nb_diag_ok, total), 90, "gt")),
    ]

    st.subheader("📌 KPI avec objectifs")
    cols = st.columns(3)
    for i, (name, val, target, status) in enumerate(kpis):
        with cols[i % 3]:
            st.metric(name, f"{val:.2f}", target)
            st.caption(status)

    st.divider()

    # ------------------------
    # TRENDS
    # ------------------------
    st.subheader("📈 KPI en tendance")

    trend_data = {
        "Effets indésirables graves /1000": (
            safe_pct(nb_effets_graves, total) * 10,
            safe_pct(prev_vals["effets"], total_prev) * 10,
        ),
        "Rémission (%)": (
            safe_pct(evol.get("Rémission", 0), total),
            safe_pct(prev_vals["remission"], total_prev),
        ),
        "Échec (%)": (
            safe_pct(evol.get("Échec de traitement", 0), total),
            safe_pct(prev_vals["echec"], total_prev),
        ),
        "Rechute (%)": (
            safe_pct(evol.get("Rechute", 0), total),
            safe_pct(prev_vals["rechute"], total_prev),
        ),
        "Mortalité (%)": (
            safe_pct(evol.get("Mortalité", 0), total),
            safe_pct(prev_vals["mort"], total_prev),
        ),
        "Taux de plaintes (%)": (
            safe_pct(nb_plaintes, total),
            safe_pct(prev_vals["plaintes"], total_prev),
        ),
    }

    rows = []
    for k, (cur, prev) in trend_data.items():
        rows.append({
            "KPI": k,
            "Valeur actuelle": round(cur, 2),
            "Valeur précédente": round(prev, 2),
            "Tendance": trend(cur, prev)
        })

    df_trend = pd.DataFrame(rows)
    st.dataframe(df_trend, use_container_width=True)

    fig = px.bar(df_trend, x="KPI", y="Valeur actuelle", title="Comparaison des KPI")
    st.plotly_chart(fig, use_container_width=True)

    # ------------------------
    # EXPORT
    # ------------------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_trend.to_excel(writer, index=False, sheet_name="KPI_Objectifs")

    st.download_button(
        "⬇️ Télécharger les KPI",
        data=output.getvalue(),
        file_name="kpi_objectifs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
