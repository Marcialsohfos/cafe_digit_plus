import json
from datetime import datetime

import streamlit as st

from common import init_page, footer
from db import get_conn, new_id, is_module_unlocked, add_submission, get_submissions
from i18n import t, tf
import auth

init_page(t("Cours", "Courses"), icon="📚")

LESSON_ICON = {"VIDEO": "🎬", "PDF": "📄", "TEXT": "📖", "R_SANDBOX": "🧪", "RESOURCE": "📦", "LAB": "🔧"}


def load_courses():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM courses WHERE published=1 ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def load_course_detail(course_id):
    conn = get_conn()
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    modules = conn.execute("SELECT * FROM modules WHERE course_id=? ORDER BY position", (course_id,)).fetchall()
    data = []
    for m in modules:
        lessons = conn.execute("SELECT * FROM lessons WHERE module_id=? ORDER BY position", (m["id"],)).fetchall()
        quizzes = conn.execute("SELECT * FROM quizzes WHERE module_id=? AND published=1", (m["id"],)).fetchall()
        data.append({"module": m, "lessons": lessons, "quizzes": quizzes})
    conn.close()
    return course, data


def is_enrolled(user_id, course_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM enrollments WHERE user_id=? AND course_id=?", (user_id, course_id)).fetchone()
    conn.close()
    return row


def enroll(user_id, course):
    is_free = (course["price_fcfa"] == 0) and not course["is_premium_only"]
    conn = get_conn()
    if not is_free:
        premium = conn.execute(
            "SELECT * FROM subscriptions WHERE user_id=? AND plan='PREMIUM' AND status='ACTIVE'", (user_id,)
        ).fetchone()
        if not premium:
            conn.close()
            return False, t(
                "Ce cours est payant. Un paiement ou un abonnement premium actif est requis.",
                "This is a paid course. An active payment or premium subscription is required.",
            )
    existing = conn.execute("SELECT id FROM enrollments WHERE user_id=? AND course_id=?", (user_id, course["id"])).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO enrollments(id,user_id,course_id,progress_pct,enrolled_at,completed_at) VALUES (?,?,?,?,?,?)",
            (new_id(), user_id, course["id"], 0, datetime.utcnow().isoformat(), None),
        )
        conn.commit()
    conn.close()
    return True, t("Inscription confirmée ! Bon apprentissage.", "Enrollment confirmed! Happy learning.")


def mark_complete(user_id, lesson_id, course_id):
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    existing = conn.execute("SELECT id FROM lesson_progress WHERE user_id=? AND lesson_id=?", (user_id, lesson_id)).fetchone()
    if existing:
        conn.execute("UPDATE lesson_progress SET completed=1, updated_at=? WHERE id=?", (now, existing["id"]))
    else:
        conn.execute(
            "INSERT INTO lesson_progress(id,user_id,lesson_id,completed,updated_at) VALUES (?,?,?,?,?)",
            (new_id(), user_id, lesson_id, 1, now),
        )
    all_lessons = conn.execute(
        "SELECT l.id FROM lessons l JOIN modules m ON l.module_id=m.id WHERE m.course_id=?", (course_id,)
    ).fetchall()
    ids = [r["id"] for r in all_lessons]
    if ids:
        placeholders = ",".join("?" * len(ids))
        done = conn.execute(
            f"SELECT COUNT(*) c FROM lesson_progress WHERE user_id=? AND completed=1 AND lesson_id IN ({placeholders})",
            (user_id, *ids),
        ).fetchone()["c"]
        pct = round(done / len(ids) * 100)
    else:
        pct = 0
    conn.execute(
        "UPDATE enrollments SET progress_pct=?, completed_at=? WHERE user_id=? AND course_id=?",
        (pct, now if pct >= 100 else None, user_id, course_id),
    )
    conn.commit()
    conn.close()


qp = st.query_params
selected_slug = qp.get("cours")

if not selected_slug:
    st.title(t("Catalogue de formations", "Course catalog"))
    st.caption(
        t(
            "Cycles thématiques en modélisation mathématique, IA et Big Data — du palier gratuit "
            "aux modules certifiants.",
            "Thematic cycles in mathematical modeling, AI and Big Data — from the free tier "
            "to certifying modules.",
        )
    )
    courses = load_courses()
    if not courses:
        st.info(t("Aucun cours publié pour le moment. Revenez bientôt !", "No course published yet. Check back soon!"))
    else:
        cols = st.columns(3)
        for i, c in enumerate(courses):
            with cols[i % 3]:
                price = t("Gratuit", "Free") if c["price_fcfa"] == 0 else f"{c['price_fcfa']:,} FCFA".replace(",", " ")
                c_title = tf(c, "title")
                c_desc = tf(c, "description")
                st.markdown(
                    f'<div class="cd-card">'
                    f'<span class="cd-badge">{c["pillar"]}</span>'
                    f'<h3 style="margin:0.5rem 0 0.3rem;">{c_title}</h3>'
                    f'<p style="font-size:0.85rem; color:rgba(30,42,36,0.65);">{c_desc[:140]}…</p>'
                    f'<div style="display:flex; justify-content:space-between; margin-top:0.6rem;">'
                    f'<span class="cd-pill">{c["level"]}</span>'
                    f'<span style="font-weight:600; color:#B4622B;">{price}</span></div></div>',
                    unsafe_allow_html=True,
                )
                if st.button(t("Voir le cours →", "View course →"), key=f"open-{c['id']}", use_container_width=True):
                    st.query_params["cours"] = c["slug"]
                    st.rerun()
else:
    conn = get_conn()
    course_row = conn.execute("SELECT * FROM courses WHERE slug=? AND published=1", (selected_slug,)).fetchone()
    conn.close()
    if not course_row:
        st.error(t("Cours introuvable.", "Course not found."))
        st.page_link("pages/1_📚_Cours.py", label=t("← Retour au catalogue", "← Back to catalog"))
    else:
        course, module_data = load_course_detail(course_row["id"])
        user = auth.current_user()
        enrolled = is_enrolled(user["id"], course["id"]) if user else None
        is_free = (course["price_fcfa"] == 0) and not course["is_premium_only"]

        if st.button(t("← Retour au catalogue", "← Back to catalog")):
            del st.query_params["cours"]
            st.rerun()

        st.markdown(f'<span class="cd-badge">{course["pillar"]}</span>', unsafe_allow_html=True)
        st.title(tf(course, "title"))
        st.write(tf(course, "description"))
        if course["context"]:
            with st.expander(t("📖 Présentation du cours & objectifs", "📖 Course overview & objectives"), expanded=True):
                st.markdown(tf(course, "context"))

        if course["final_project_text"] or course["certification_text"] or course["mentoring_text"]:
            with st.expander(t("🎓 Évaluation, accompagnement & certification", "🎓 Assessment, support & certification")):
                if course["final_project_text"]:
                    st.markdown(f"**{t('🏁 Projet de fin d\'études (Fil Rouge)', '🏁 Final project (Capstone)')}**")
                    st.write(tf(course, "final_project_text"))
                if course["certification_text"]:
                    st.markdown(f"**{t('📜 Certification Café_digit', '📜 Café_digit certification')}**")
                    st.write(tf(course, "certification_text"))
                if course["mentoring_text"]:
                    st.markdown(f"**{t('🤝 Espace Accompagnement (post-formation)', '🤝 Post-training support space')}**")
                    st.write(tf(course, "mentoring_text"))

        c1, c2, c3 = st.columns([1, 1, 3])
        c1.markdown(f'<span class="cd-pill">{course["level"]}</span>', unsafe_allow_html=True)
        price_txt = t("Gratuit", "Free") if is_free else f"{course['price_fcfa']:,} FCFA".replace(",", " ")
        c2.markdown(f'<span style="font-weight:600; color:#B4622B;">{price_txt}</span>', unsafe_allow_html=True)

        if not enrolled:
            if not user:
                st.info(t("Connectez-vous pour vous inscrire à ce cours.", "Log in to enroll in this course."))
                st.page_link("pages/5_🔐_Connexion.py", label=t("Se connecter →", "Log in →"))
            else:
                label = t("S'inscrire gratuitement", "Enroll for free") if is_free else t("Débloquer ce cours", "Unlock this course")
                if st.button(label):
                    ok, msg = enroll(user["id"], course)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

        st.markdown("---")
        left, right = st.columns([1, 2])

        lesson_key = f"lesson_{course['id']}"
        if lesson_key not in st.session_state and module_data and module_data[0]["lessons"]:
            st.session_state[lesson_key] = module_data[0]["lessons"][0]["id"]

        with left:
            for block in module_data:
                module_unlocked = (
                    is_module_unlocked(user["id"], course["id"], block["module"]["position"])
                    if user else block["module"]["position"] == 0
                )
                title_prefix = "" if module_unlocked else "🔒 "
                st.markdown(f"**{title_prefix}{tf(block['module'], 'title')}**")
                if block['module']['objective']:
                    st.caption(tf(block['module'], 'objective'))
                if not module_unlocked:
                    st.caption(t(
                        "🔒 Réussissez le quiz du module précédent pour déverrouiller ce module.",
                        "🔒 Pass the previous module's quiz to unlock this module.",
                    ))
                access_locked = (not is_free and not enrolled) or not module_unlocked
                for l in block["lessons"]:
                    icon = "🔒" if access_locked else LESSON_ICON.get(l["type"], "•")
                    if st.button(f"{icon} {tf(l, 'title')}", key=f"les-{l['id']}", disabled=access_locked, use_container_width=True):
                        st.session_state[lesson_key] = l["id"]
                        st.rerun()
                for q in block["quizzes"]:
                    if st.button(f"📝 {t('Quiz', 'Quiz')} : {q['title']}", key=f"quiz-{q['id']}", disabled=access_locked, use_container_width=True):
                        st.session_state["active_quiz_id"] = q["id"]
                        st.switch_page("pages/10_📝_Quiz.py")

        with right:
            active_lesson = None
            for block in module_data:
                for l in block["lessons"]:
                    if l["id"] == st.session_state.get(lesson_key):
                        active_lesson = l
            if not active_lesson:
                st.info(t("Sélectionnez une leçon pour commencer.", "Select a lesson to get started."))
            else:
                st.subheader(tf(active_lesson, "title"))
                if active_lesson["type"] == "VIDEO":
                    if active_lesson["video_url"]:
                        st.video(active_lesson["video_url"])
                    else:
                        st.info(t(
                            "Vidéo à venir — l'administrateur alimentera bientôt ce module.",
                            "Video coming soon — the administrator will update this module shortly.",
                        ))
                elif active_lesson["type"] == "PDF":
                    if active_lesson["pdf_url"]:
                        st.markdown(f"[{t('Ouvrir le PDF', 'Open the PDF')}]({active_lesson['pdf_url']})")
                    else:
                        st.info(t("PDF à venir.", "PDF coming soon."))
                elif active_lesson["type"] == "TEXT":
                    st.write(tf(active_lesson, "content"))
                elif active_lesson["type"] == "R_SANDBOX":
                    st.markdown(f'<div class="cd-mono">{tf(active_lesson, "content")}</div>', unsafe_allow_html=True)
                    st.caption(t(
                        "→ Testez ce code dans l'onglet Sandbox R du menu latéral.",
                        "→ Test this code in the R Sandbox tab from the side menu.",
                    ))
                elif active_lesson["type"] == "RESOURCE":
                    st.write(tf(active_lesson, "content"))
                    if active_lesson["resource_url"]:
                        st.markdown(f"[{t('📦 Télécharger la ressource', '📦 Download the resource')}]({active_lesson['resource_url']})")
                    else:
                        st.info(t("Ressource à venir.", "Resource coming soon."))
                elif active_lesson["type"] == "LAB":
                    st.write(tf(active_lesson, "content"))
                    if active_lesson["resource_url"]:
                        st.markdown(f"[{t('📎 Support du cas pratique', '📎 Case study handout')}]({active_lesson['resource_url']})")

                if active_lesson["type"] != "RESOURCE" and active_lesson["resource_url"]:
                    st.markdown(f"[{t('📎 Télécharger le script associé', '📎 Download the associated script')}]({active_lesson['resource_url']})")

                if user:
                    if st.button(t("Marquer comme terminée ✓", "Mark as complete ✓"), key=f"done-{active_lesson['id']}"):
                        mark_complete(user["id"], active_lesson["id"], course["id"])
                        st.success(t("Progression enregistrée.", "Progress saved."))
                        st.rerun()

                # 🔧 Sandbox / Dépôt de code : soumission du cas pratique pour correction
                if user and active_lesson["type"] == "LAB":
                    st.markdown("---")
                    st.markdown(f"##### {t('🔧 Déposer votre travail pour correction', '🔧 Submit your work for review')}")
                    with st.form(f"submit_lab_{active_lesson['id']}"):
                        sub_file = st.file_uploader(
                            t("Fichier de code (.R, .py, .do, .txt...)", "Code file (.R, .py, .do, .txt...)"),
                            key=f"subf-{active_lesson['id']}",
                        )
                        sub_code = st.text_area(
                            t("Ou collez directement votre code / rapport ici", "Or paste your code / report directly here"),
                            key=f"subc-{active_lesson['id']}", height=150,
                        )
                        sub_comment = st.text_input(t("Commentaire (optionnel)", "Comment (optional)"), key=f"subm-{active_lesson['id']}")
                        sub_go = st.form_submit_button(t("📤 Soumettre pour correction", "📤 Submit for review"))
                    if sub_go:
                        content, fname = None, None
                        if sub_file is not None:
                            fname = sub_file.name
                            try:
                                content = sub_file.getvalue().decode("utf-8", errors="replace")
                            except Exception:
                                content = t("(fichier binaire non prévisualisable)", "(binary file, no preview available)")
                        elif sub_code.strip():
                            content = sub_code
                            fname = f"{active_lesson['title']}.txt"
                        if not content:
                            st.error(t("Ajoutez un fichier ou collez du code avant de soumettre.", "Add a file or paste code before submitting."))
                        else:
                            add_submission(
                                user["id"], course["id"], active_lesson["title"], kind="LAB",
                                module_id=active_lesson["module_id"], lesson_id=active_lesson["id"],
                                file_name=fname, file_content=content, comment=sub_comment,
                            )
                            st.success(t(
                                "Dépôt envoyé — vous recevrez un retour dans votre espace « Mon espace ».",
                                "Submission sent — you'll receive feedback in your « My space » page.",
                            ))
                            st.rerun()

                    my_subs = [
                        s for s in get_submissions(course_id=course["id"], user_id=user["id"])
                        if s["lesson_id"] == active_lesson["id"]
                    ]
                    if my_subs:
                        st.caption(t("Vos dépôts précédents pour ce cas pratique :", "Your previous submissions for this case study:"))
                        for s in my_subs:
                            state = t("✅ corrigé", "✅ reviewed") if s["status"] == "REVIEWED" else t("🕓 en attente de correction", "🕓 awaiting review")
                            st.write(f"- {s['created_at'][:16].replace('T', ' ')} — {state}")
                            if s["status"] == "REVIEWED":
                                st.caption(t(
                                    f"Note : {s['grade'] or '—'} · Retour : {s['feedback'] or '—'}",
                                    f"Grade: {s['grade'] or '—'} · Feedback: {s['feedback'] or '—'}",
                                ))

        # 🏁 Projet de fin d'études (Fil Rouge) : dépôt global du cours
        if user and enrolled and course["final_project_text"]:
            st.markdown("---")
            st.markdown(f"### {t('🏁 Projet de fin d\'études (Fil Rouge)', '🏁 Final project (Capstone)')}")
            st.write(course["final_project_text"])
            with st.form(f"submit_final_{course['id']}"):
                fp_file = st.file_uploader(
                    t("Fichier (script + rapport, .zip/.txt/.R/.py/.do)", "File (script + report, .zip/.txt/.R/.py/.do)"),
                    key=f"fpf-{course['id']}",
                )
                fp_code = st.text_area(t("Ou collez votre rapport de synthèse ici", "Or paste your summary report here"), key=f"fpc-{course['id']}", height=150)
                fp_comment = st.text_input(t("Commentaire (optionnel)", "Comment (optional)"), key=f"fpm-{course['id']}")
                fp_go = st.form_submit_button(t("📤 Soumettre le projet final", "📤 Submit the final project"))
            if fp_go:
                content, fname = None, None
                if fp_file is not None:
                    fname = fp_file.name
                    try:
                        content = fp_file.getvalue().decode("utf-8", errors="replace")
                    except Exception:
                        content = t("(fichier binaire non prévisualisable)", "(binary file, no preview available)")
                elif fp_code.strip():
                    content, fname = fp_code, f"projet_final_{course['slug']}.txt"
                if not content:
                    st.error(t("Ajoutez un fichier ou collez votre rapport avant de soumettre.", "Add a file or paste your report before submitting."))
                else:
                    add_submission(
                        user["id"], course["id"], t(f"Projet final — {course['title']}", f"Final project — {course['title']}"), kind="FINAL_PROJECT",
                        file_name=fname, file_content=content, comment=fp_comment,
                    )
                    st.success(t(
                        "Projet soumis — un administrateur validera votre certification après correction.",
                        "Project submitted — an administrator will validate your certification after review.",
                    ))
                    st.rerun()

footer()
