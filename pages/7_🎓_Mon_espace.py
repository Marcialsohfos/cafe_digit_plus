import streamlit as st

from common import init_page, footer
from db import get_conn
import auth

init_page("Mon espace", icon="🎓")

user = auth.current_user()
if not user:
    st.warning("Connectez-vous pour accéder à votre espace.")
    st.page_link("pages/5_🔐_Connexion.py", label="Se connecter →")
    st.stop()

st.title(f"Bonjour, {user['fullName'].split(' ')[0]} 👋")

conn = get_conn()
enrollments = conn.execute(
    "SELECT e.*, c.title, c.slug FROM enrollments e JOIN courses c ON e.course_id=c.id "
    "WHERE e.user_id=? ORDER BY e.enrolled_at DESC", (user["id"],)
).fetchall()
attempts = conn.execute(
    "SELECT a.*, q.title as quiz_title FROM quiz_attempts a JOIN quizzes q ON a.quiz_id=q.id "
    "WHERE a.user_id=? ORDER BY a.submitted_at DESC", (user["id"],)
).fetchall()
subs = conn.execute(
    "SELECT * FROM subscriptions WHERE user_id=? ORDER BY started_at DESC", (user["id"],)
).fetchall()
conn.close()

st.markdown("### Mes cours")
if not enrollments:
    st.caption("Aucune inscription pour l'instant.")
else:
    cols = st.columns(2)
    for i, e in enumerate(enrollments):
        with cols[i % 2]:
            st.markdown(
                f'<div class="cd-card"><b>{e["title"]}</b>'
                f'<div style="background:rgba(42,27,18,0.1); border-radius:999px; height:8px; margin-top:0.5rem;">'
                f'<div style="background:#B4622B; width:{e["progress_pct"]}%; height:8px; border-radius:999px;"></div></div>'
                f'<p style="font-size:0.75rem; color:rgba(30,42,36,0.5); margin-top:0.3rem;">{e["progress_pct"]}% complété</p></div>',
                unsafe_allow_html=True,
            )
            if st.button("Continuer →", key=f"cont-{e['id']}"):
                st.query_params["cours"] = e["slug"]
                st.switch_page("pages/1_📚_Cours.py")

st.markdown("### Mes tentatives de quiz")
if not attempts:
    st.caption("Aucun quiz passé pour le moment.")
else:
    for a in attempts:
        ok = bool(a["passed"])
        st.markdown(
            f'<div class="cd-card" style="display:flex; justify-content:space-between; align-items:center;">'
            f'<span>{a["quiz_title"]}</span>'
            f'<span style="color:{"#2F5D50" if ok else "#B4622B"}; font-weight:600;">{a["score_pct"]}% {"✓" if ok else "✗"}</span></div>',
            unsafe_allow_html=True,
        )

st.markdown("### Mes offres")
if not subs:
    st.caption("Aucune offre souscrite.")
else:
    for s in subs:
        active = s["status"] == "ACTIVE"
        st.markdown(
            f'<div class="cd-card" style="display:flex; justify-content:space-between; align-items:center;">'
            f'<span>{s["plan"]}</span>'
            f'<span class="cd-badge" style="background:{"rgba(47,93,80,0.12)" if active else "rgba(224,138,62,0.15)"}; '
            f'color:{"#2F5D50" if active else "#E08A3E"};">{s["status"]}</span></div>',
            unsafe_allow_html=True,
        )
st.page_link("pages/3_💳_Abonnement.py", label="Gérer mes offres →")

footer()
