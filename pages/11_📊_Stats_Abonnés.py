"""
Café_digit — Statistiques du nombre d'abonnés.

Cette page (réservée aux administrateurs) permet de retracer :
- le nombre total de comptes créés (membres) ;
- le nombre d'abonnés payants actifs, par formule (PREMIUM / MODULE / B2B) ;
- l'évolution dans le temps (courbe cumulative) des inscriptions et des
  abonnements payants ;
- le détail (table exportable en CSV) des abonnements payants.

Toutes les données proviennent directement des tables `users` et
`subscriptions` de la base (voir db.py) — aucune donnée supplémentaire n'est
nécessaire.
"""
from datetime import datetime

import pandas as pd
import streamlit as st

from common import init_page, footer
from db import get_conn, PLAN_PRICES_FCFA
from i18n import t
import auth

init_page(t("Statistiques abonnés", "Subscriber statistics"), icon="📊")

if not auth.is_admin():
    st.error(t(
        "Cette section est réservée aux administrateurs de Café_digit.",
        "This section is reserved for Café_digit administrators.",
    ))
    st.page_link("pages/5_🔐_Connexion.py", label=t("Se connecter →", "Log in →"))
    st.page_link("pages/8_🔑_Super_Admin.py", label=t("Accès Super Admin →", "Super Admin access →"))
    st.stop()

user = auth.current_user()
st.title(t("📊 Statistiques abonnés", "📊 Subscriber statistics"))
st.caption(t(
    f"Connecté en tant que {user['fullName']} — {user['role']}",
    f"Logged in as {user['fullName']} — {user['role']}",
))

# --------------------------------------------------------------- Chargement
conn = get_conn()
users_df = pd.read_sql_query(
    "SELECT id, email, full_name, city, organization, created_at "
    "FROM users WHERE role='STUDENT'",
    conn,
)
subs_df = pd.read_sql_query(
    "SELECT s.*, u.full_name, u.email FROM subscriptions s "
    "JOIN users u ON s.user_id = u.id",
    conn,
)
conn.close()

users_df["created_at"] = pd.to_datetime(users_df["created_at"], errors="coerce")
subs_df["started_at"] = pd.to_datetime(subs_df["started_at"], errors="coerce")

paid_df = subs_df[subs_df["plan"] != "FREE"].copy()
paid_active_df = paid_df[paid_df["status"] == "ACTIVE"].copy()

# ------------------------------------------------------------------- KPIs
total_members = len(users_df)
n_paid_active_users = paid_active_df["user_id"].nunique()
n_paid_total_ever = paid_df["user_id"].nunique()
revenue_active_fcfa = int(paid_active_df["amount_fcfa"].sum()) if not paid_active_df.empty else 0
conversion_pct = round((n_paid_active_users / total_members) * 100, 1) if total_members else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(t("Total comptes créés", "Total accounts created"), total_members)
k2.metric(t("Abonnés payants actifs", "Active paying subscribers"), n_paid_active_users)
k3.metric(t("Ont déjà souscrit (payant)", "Have ever subscribed (paid)"), n_paid_total_ever)
k4.metric(t("Taux de conversion", "Conversion rate"), f"{conversion_pct}%")
k5.metric(t("Revenu actif (FCFA)", "Active revenue (FCFA)"), f"{revenue_active_fcfa:,}".replace(",", " "))

st.divider()

# --------------------------------------------------- Répartition par plan
st.subheader(t("Répartition des abonnés payants actifs par formule", "Active paying subscribers by plan"))
if paid_active_df.empty:
    st.info(t("Aucun abonnement payant actif pour le moment.", "No active paid subscription yet."))
else:
    plan_counts = (
        paid_active_df.groupby("plan")["user_id"].nunique().reindex(list(PLAN_PRICES_FCFA.keys())).fillna(0).astype(int)
    )
    pc1, pc2 = st.columns([2, 1])
    with pc1:
        st.bar_chart(plan_counts)
    with pc2:
        for plan, count in plan_counts.items():
            st.metric(plan, int(count))

st.divider()

# -------------------------------------------------------------- Évolution
st.subheader(t("Évolution du nombre d'abonnés dans le temps", "Subscriber growth over time"))

granularity = st.radio(
    t("Granularité", "Granularity"),
    options=["D", "W", "ME"],
    format_func=lambda x: {"D": t("Jour", "Day"), "W": t("Semaine", "Week"), "ME": t("Mois", "Month")}[x],
    horizontal=True,
    index=2,
)

ev1, ev2 = st.columns(2)

with ev1:
    st.markdown(f"**{t('Comptes créés (cumulé)', 'Accounts created (cumulative)')}**")
    if users_df["created_at"].notna().any():
        members_series = (
            users_df.dropna(subset=["created_at"])
            .set_index("created_at")
            .resample(granularity)
            .size()
            .cumsum()
        )
        members_series.name = t("Comptes cumulés", "Cumulative accounts")
        st.line_chart(members_series)
    else:
        st.caption(t("Pas encore de données.", "No data yet."))

with ev2:
    st.markdown(f"**{t('Abonnements payants souscrits (cumulé)', 'Paid subscriptions started (cumulative)')}**")
    if not paid_df.empty and paid_df["started_at"].notna().any():
        paid_series = (
            paid_df.dropna(subset=["started_at"])
            .set_index("started_at")
            .resample(granularity)
            .size()
            .cumsum()
        )
        paid_series.name = t("Abonnements cumulés", "Cumulative subscriptions")
        st.line_chart(paid_series)
    else:
        st.caption(t("Pas encore de données.", "No data yet."))

st.divider()

# -------------------------------------------------------------- Détail /export
st.subheader(t("Détail des abonnements payants", "Paid subscriptions detail"))

status_filter = st.multiselect(
    t("Filtrer par statut", "Filter by status"),
    options=sorted(paid_df["status"].unique()) if not paid_df.empty else [],
    default=sorted(paid_df["status"].unique()) if not paid_df.empty else [],
)

if paid_df.empty:
    st.info(t("Aucun abonnement payant à afficher.", "No paid subscription to display."))
else:
    detail_df = paid_df[paid_df["status"].isin(status_filter)][
        ["full_name", "email", "plan", "status", "amount_fcfa", "started_at", "expires_at", "payment_ref"]
    ].sort_values("started_at", ascending=False)
    detail_df = detail_df.rename(columns={
        "full_name": t("Nom", "Name"),
        "email": t("E-mail", "Email"),
        "plan": t("Formule", "Plan"),
        "status": t("Statut", "Status"),
        "amount_fcfa": t("Montant (FCFA)", "Amount (FCFA)"),
        "started_at": t("Démarré le", "Started on"),
        "expires_at": t("Expire le", "Expires on"),
        "payment_ref": t("Référence paiement", "Payment ref."),
    })
    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    csv_bytes = detail_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        f"⬇️ {t('Exporter en CSV', 'Export as CSV')}",
        data=csv_bytes,
        file_name=f"abonnes_cafedigit_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

footer()
