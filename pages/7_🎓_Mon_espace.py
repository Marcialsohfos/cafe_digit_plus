import streamlit as st

from common import init_page, footer
from db import (
    get_conn, get_course_quiz_summary, get_submissions,
    ensure_premium_access, get_active_subscription_plan, get_premium_courses,
    get_resources, get_resource_bytes, human_size,
)
from i18n import t
import auth

init_page(t("Mon espace", "My space"), icon="🎓")

user = auth.current_user()
if not user:
    st.warning(t("Connectez-vous pour accéder à votre espace.", "Log in to access your space."))
    st.page_link("pages/5_🔐_Connexion.py", label=t("Se connecter →", "Log in →"))
    st.stop()

st.title(t(f"Bonjour, {user['fullName'].split(' ')[0]} 👋", f"Hello, {user['fullName'].split(' ')[0]} 👋"))

active_plan = ensure_premium_access(user["id"])


def _resource_card(r):
    course_label = r["course_title"] or t("Ressource générale", "General resource")
    desc_html = (
        f'<p style="font-size:0.85rem; color:rgba(30,42,36,0.7); margin-top:0.3rem;">{r["description"]}</p>'
        if r["description"] else ""
    )
    st.markdown(
        f'<div class="cd-card"><b>{r["title"]}</b> — <span style="font-size:0.8rem; '
        f'color:rgba(30,42,36,0.6);">{course_label} · {human_size(r["file_size"])} · {r["file_ext"].upper()}</span>'
        f'{desc_html}</div>',
        unsafe_allow_html=True,
    )
    st.download_button(
        t("⬇️ Télécharger", "⬇️ Download"), data=get_resource_bytes(r), file_name=r["file_name"],
        key=f"dlres-{r['id']}",
    )

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

premium_courses = get_premium_courses()
if premium_courses:
    st.markdown(f"### {t('🌟 Cours Premium', '🌟 Premium courses')}")
    if active_plan:
        st.success(t(
            f"Votre offre **{active_plan}** est active : vous avez un accès direct à tous les cours Premium ci-dessous.",
            f"Your **{active_plan}** plan is active: you have direct access to all the Premium courses below.",
        ))
        p_cols = st.columns(2)
        for i, pc in enumerate(premium_courses):
            with p_cols[i % 2]:
                st.markdown(
                    f'<div class="cd-card" style="border-color:#E08A3E;">'
                    f'<span class="cd-badge" style="background:rgba(224,138,62,0.18); color:#B4622B;">⭐ Premium</span>'
                    f'<h4 style="margin:0.4rem 0 0.2rem;">{pc["title"]}</h4></div>',
                    unsafe_allow_html=True,
                )
                if st.button(t("🔓 Ouvrir directement →", "🔓 Open directly →"), key=f"premopen-{pc['id']}", use_container_width=True):
                    st.query_params["cours"] = pc["slug"]
                    st.switch_page("pages/1_📚_Cours.py")
    else:
        st.info(t(
            "Souscrivez une offre payante (Premium, Module certifiant, B2B…) pour débloquer "
            "l'accès direct à tous les cours Premium.",
            "Subscribe to a paid plan (Premium, Certifying module, B2B…) to unlock direct access "
            "to all Premium courses.",
        ))
        st.page_link("pages/3_💳_Abonnement.py", label=t("Voir les offres →", "See the plans →"))
    st.markdown("---")

st.markdown(f"### {t('📦 Ressources & datasets', '📦 Resources & datasets')}")
all_resources = get_resources()
open_resources = [r for r in all_resources if not r["is_premium_only"]]
premium_resources = [r for r in all_resources if r["is_premium_only"]]

if not all_resources:
    st.caption(t("Aucune ressource disponible pour le moment.", "No resources available yet."))
else:
    if open_resources:
        st.markdown(f"###### {t('Ouvertes à tous les membres', 'Open to all members')}")
        for r in open_resources:
            _resource_card(r)
    if premium_resources:
        st.markdown(f"###### {t('⭐ Réservées aux membres Premium', '⭐ Premium-only')}")
        if active_plan:
            for r in premium_resources:
                _resource_card(r)
        else:
            st.caption(t(
                f"{len(premium_resources)} ressource(s) Premium disponibles — souscrivez une offre "
                "payante pour les télécharger.",
                f"{len(premium_resources)} Premium resource(s) available — subscribe to a paid plan "
                "to download them.",
            ))
            st.page_link("pages/3_💳_Abonnement.py", label=t("Voir les offres →", "See the plans →"))
st.markdown("---")

st.markdown(f"### {t('Mes cours', 'My courses')}")
if not enrollments:
    st.caption(t("Aucune inscription pour l'instant.", "No enrollment yet."))
else:
    cols = st.columns(2)
    for i, e in enumerate(enrollments):
        with cols[i % 2]:
            summary = get_course_quiz_summary(user["id"], e["course_id"])
            quiz_line = ""
            if summary["quizzes_total"]:
                quiz_line = (
                    f'<p style="font-size:0.75rem; color:rgba(30,42,36,0.6); margin-top:0.2rem;">'
                    f'✅ {t(f"{summary["total_correct"]}/{summary["total_possible"]} bonnes réponses trouvées", f"{summary["total_correct"]}/{summary["total_possible"]} correct answers found")} · '
                    f'{t(f"{summary["quizzes_passed"]}/{summary["quizzes_total"]} quiz réussis", f"{summary["quizzes_passed"]}/{summary["quizzes_total"]} quizzes passed")}</p>'
                )
            st.markdown(
                f'<div class="cd-card"><b>{e["title"]}</b>'
                f'<div style="background:rgba(42,27,18,0.1); border-radius:999px; height:8px; margin-top:0.5rem;">'
                f'<div style="background:#B4622B; width:{e["progress_pct"]}%; height:8px; border-radius:999px;"></div></div>'
                f'<p style="font-size:0.75rem; color:rgba(30,42,36,0.5); margin-top:0.3rem;">{t(f"{e['progress_pct']}% complété", f"{e['progress_pct']}% complete")}</p>'
                f'{quiz_line}</div>',
                unsafe_allow_html=True,
            )
            if st.button(t("Continuer →", "Continue →"), key=f"cont-{e['id']}"):
                st.query_params["cours"] = e["slug"]
                st.switch_page("pages/1_📚_Cours.py")

st.markdown(f"### {t('Mes tentatives de quiz', 'My quiz attempts')}")
if not attempts:
    st.caption(t("Aucun quiz passé pour le moment.", "No quiz taken yet."))
else:
    for a in attempts:
        ok = bool(a["passed"])
        st.markdown(
            f'<div class="cd-card" style="display:flex; justify-content:space-between; align-items:center;">'
            f'<span>{a["quiz_title"]}</span>'
            f'<span style="color:{"#2F5D50" if ok else "#B4622B"}; font-weight:600;">{a["score_pct"]}% {"✓" if ok else "✗"}</span></div>',
            unsafe_allow_html=True,
        )

st.markdown(f"### {t('Mes dépôts (cas pratiques & projet final)', 'My submissions (labs & final project)')}")
my_submissions = get_submissions(user_id=user["id"])
if not my_submissions:
    st.caption(t("Aucun dépôt pour le moment.", "No submission yet."))
else:
    for s in my_submissions:
        reviewed = s["status"] == "REVIEWED"
        badge = t("✅ Corrigé", "✅ Reviewed") if reviewed else t("🕓 En attente de correction", "🕓 Awaiting review")
        st.markdown(
            f'<div class="cd-card"><b>{s["title"]}</b> — <span style="font-size:0.8rem; '
            f'color:rgba(30,42,36,0.6);">{s["course_title"]}</span>'
            f'<div style="margin-top:0.3rem;"><span class="cd-badge">{badge}</span></div></div>',
            unsafe_allow_html=True,
        )
        if reviewed:
            st.caption(t(f"Note : {s['grade'] or '—'} · Retour : {s['feedback'] or '—'}", f"Grade: {s['grade'] or '—'} · Feedback: {s['feedback'] or '—'}"))

st.markdown(f"### {t('Mes offres', 'My plans')}")
if not subs:
    st.caption(t("Aucune offre souscrite.", "No plan subscribed."))
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
st.page_link("pages/3_💳_Abonnement.py", label=t("Gérer mes offres →", "Manage my plans →"))

footer()
