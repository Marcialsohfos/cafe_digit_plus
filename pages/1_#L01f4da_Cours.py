import json
from datetime import datetime

import streamlit as st

from common import init_page, footer
from db import get_conn, new_id, is_module_unlocked, add_submission, get_submissions
import auth

init_page("Cours", icon="📚")

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
            return False, "Ce cours est payant. Un paiement ou un abonnement premium actif est requis."
    existing = conn.execute("SELECT id FROM enrollments WHERE user_id=? AND course_id=?", (user_id, course["id"])).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO enrollments(id,user_id,course_id,progress_pct,enrolled_at,completed_at) VALUES (?,?,?,?,?,?)",
            (new_id(), user_id, course["id"], 0, datetime.utcnow().isoformat(), None),
        )
        conn.commit()
    conn.close()
    return True, "Inscription confirmée ! Bon apprentissage."


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
    st.title("Catalogue de formations")
    st.caption(
        "Cycles thématiques en modélisation mathématique, IA et Big Data — du palier gratuit "
        "aux modules certifiants."
    )
    courses = load_courses()
    if not courses:
        st.info("Aucun cours publié pour le moment. Revenez bientôt !")
    else:
        cols = st.columns(3)
        for i, c in enumerate(courses):
            with cols[i % 3]:
                price = "Gratuit" if c["price_fcfa"] == 0 else f"{c['price_fcfa']:,} FCFA".replace(",", " ")
                st.markdown(
                    f'<div class="cd-card">'
                    f'<span class="cd-badge">{c["pillar"]}</span>'
                    f'<h3 style="margin:0.5rem 0 0.3rem;">{c["title"]}</h3>'
                    f'<p style="font-size:0.85rem; color:rgba(30,42,36,0.65);">{c["description"][:140]}…</p>'
                    f'<div style="display:flex; justify-content:space-between; margin-top:0.6rem;">'
                    f'<span class="cd-pill">{c["level"]}</span>'
                    f'<span style="font-weight:600; color:#B4622B;">{price}</span></div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Voir le cours →", key=f"open-{c['id']}", use_container_width=True):
                    st.query_params["cours"] = c["slug"]
                    st.rerun()
else:
    conn = get_conn()
    course_row = conn.execute("SELECT * FROM courses WHERE slug=? AND published=1", (selected_slug,)).fetchone()
    conn.close()
    if not course_row:
        st.error("Cours introuvable.")
        st.page_link("pages/1_📚_Cours.py", label="← Retour au catalogue")
    else:
        course, module_data = load_course_detail(course_row["id"])
        user = auth.current_user()
        enrolled = is_enrolled(user["id"], course["id"]) if user else None
        is_free = (course["price_fcfa"] == 0) and not course["is_premium_only"]

        if st.button("← Retour au catalogue"):
            del st.query_params["cours"]
            st.rerun()

        st.markdown(f'<span class="cd-badge">{course["pillar"]}</span>', unsafe_allow_html=True)
        st.title(course["title"])
        st.write(course["description"])
        if course["context"]:
            with st.expander("📖 Présentation du cours & objectifs", expanded=True):
                st.markdown(course["context"])

        if course["final_project_text"] or course["certification_text"] or course["mentoring_text"]:
            with st.expander("🎓 Évaluation, accompagnement & certification"):
                if course["final_project_text"]:
                    st.markdown("**🏁 Projet de fin d'études (Fil Rouge)**")
                    st.write(course["final_project_text"])
                if course["certification_text"]:
                    st.markdown("**📜 Certification Café_digit**")
                    st.write(course["certification_text"])
                if course["mentoring_text"]:
                    st.markdown("**🤝 Espace Accompagnement (post-formation)**")
                    st.write(course["mentoring_text"])

        c1, c2, c3 = st.columns([1, 1, 3])
        c1.markdown(f'<span class="cd-pill">{course["level"]}</span>', unsafe_allow_html=True)
        price_txt = "Gratuit" if is_free else f"{course['price_fcfa']:,} FCFA".replace(",", " ")
        c2.markdown(f'<span style="font-weight:600; color:#B4622B;">{price_txt}</span>', unsafe_allow_html=True)

        if not enrolled:
            if not user:
                st.info("Connectez-vous pour vous inscrire à ce cours.")
                st.page_link("pages/5_🔐_Connexion.py", label="Se connecter →")
            else:
                label = "S'inscrire gratuitement" if is_free else "Débloquer ce cours"
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
                st.markdown(f"**{title_prefix}{block['module']['title']}**")
                if block['module']['objective']:
                    st.caption(block['module']['objective'])
                if not module_unlocked:
                    st.caption("🔒 Réussissez le quiz du module précédent pour déverrouiller ce module.")
                access_locked = (not is_free and not enrolled) or not module_unlocked
                for l in block["lessons"]:
                    icon = "🔒" if access_locked else LESSON_ICON.get(l["type"], "•")
                    if st.button(f"{icon} {l['title']}", key=f"les-{l['id']}", disabled=access_locked, use_container_width=True):
                        st.session_state[lesson_key] = l["id"]
                        st.rerun()
                for q in block["quizzes"]:
                    if st.button(f"📝 Quiz : {q['title']}", key=f"quiz-{q['id']}", disabled=access_locked, use_container_width=True):
                        st.session_state["active_quiz_id"] = q["id"]
                        st.switch_page("pages/10_📝_Quiz.py")

        with right:
            active_lesson = None
            for block in module_data:
                for l in block["lessons"]:
                    if l["id"] == st.session_state.get(lesson_key):
                        active_lesson = l
            if not active_lesson:
                st.info("Sélectionnez une leçon pour commencer.")
            else:
                st.subheader(active_lesson["title"])
                if active_lesson["type"] == "VIDEO":
                    if active_lesson["video_url"]:
                        st.video(active_lesson["video_url"])
                    else:
                        st.info("Vidéo à venir — l'administrateur alimentera bientôt ce module.")
                elif active_lesson["type"] == "PDF":
                    if active_lesson["pdf_url"]:
                        st.markdown(f"[Ouvrir le PDF]({active_lesson['pdf_url']})")
                    else:
                        st.info("PDF à venir.")
                elif active_lesson["type"] == "TEXT":
                    st.write(active_lesson["content"] or "")
                elif active_lesson["type"] == "R_SANDBOX":
                    st.markdown(f'<div class="cd-mono">{active_lesson["content"] or ""}</div>', unsafe_allow_html=True)
                    st.caption("→ Testez ce code dans l'onglet Sandbox R du menu latéral.")
                elif active_lesson["type"] == "RESOURCE":
                    st.write(active_lesson["content"] or "")
                    if active_lesson["resource_url"]:
                        st.markdown(f"[📦 Télécharger la ressource]({active_lesson['resource_url']})")
                    else:
                        st.info("Ressource à venir.")
                elif active_lesson["type"] == "LAB":
                    st.write(active_lesson["content"] or "")
                    if active_lesson["resource_url"]:
                        st.markdown(f"[📎 Support du cas pratique]({active_lesson['resource_url']})")

                if active_lesson["type"] != "RESOURCE" and active_lesson["resource_url"]:
                    st.markdown(f"[📎 Télécharger le script associé]({active_lesson['resource_url']})")

                if user:
                    if st.button("Marquer comme terminée ✓", key=f"done-{active_lesson['id']}"):
                        mark_complete(user["id"], active_lesson["id"], course["id"])
                        st.success("Progression enregistrée.")
                        st.rerun()

                # 🔧 Sandbox / Dépôt de code : soumission du cas pratique pour correction
                if user and active_lesson["type"] == "LAB":
                    st.markdown("---")
                    st.markdown("##### 🔧 Déposer votre travail pour correction")
                    with st.form(f"submit_lab_{active_lesson['id']}"):
                        sub_file = st.file_uploader(
                            "Fichier de code (.R, .py, .do, .txt...)", key=f"subf-{active_lesson['id']}",
                        )
                        sub_code = st.text_area(
                            "Ou collez directement votre code / rapport ici",
                            key=f"subc-{active_lesson['id']}", height=150,
                        )
                        sub_comment = st.text_input("Commentaire (optionnel)", key=f"subm-{active_lesson['id']}")
                        sub_go = st.form_submit_button("📤 Soumettre pour correction")
                    if sub_go:
                        content, fname = None, None
                        if sub_file is not None:
                            fname = sub_file.name
                            try:
                                content = sub_file.getvalue().decode("utf-8", errors="replace")
                            except Exception:
                                content = "(fichier binaire non prévisualisable)"
                        elif sub_code.strip():
                            content = sub_code
                            fname = f"{active_lesson['title']}.txt"
                        if not content:
                            st.error("Ajoutez un fichier ou collez du code avant de soumettre.")
                        else:
                            add_submission(
                                user["id"], course["id"], active_lesson["title"], kind="LAB",
                                module_id=active_lesson["module_id"], lesson_id=active_lesson["id"],
                                file_name=fname, file_content=content, comment=sub_comment,
                            )
                            st.success("Dépôt envoyé — vous recevrez un retour dans votre espace « Mon espace ».")
                            st.rerun()

                    my_subs = [
                        s for s in get_submissions(course_id=course["id"], user_id=user["id"])
                        if s["lesson_id"] == active_lesson["id"]
                    ]
                    if my_subs:
                        st.caption("Vos dépôts précédents pour ce cas pratique :")
                        for s in my_subs:
                            state = "✅ corrigé" if s["status"] == "REVIEWED" else "🕓 en attente de correction"
                            st.write(f"- {s['created_at'][:16].replace('T', ' ')} — {state}")
                            if s["status"] == "REVIEWED":
                                st.caption(f"Note : {s['grade'] or '—'} · Retour : {s['feedback'] or '—'}")

        # 🏁 Projet de fin d'études (Fil Rouge) : dépôt global du cours
        if user and enrolled and course["final_project_text"]:
            st.markdown("---")
            st.markdown("### 🏁 Projet de fin d'études (Fil Rouge)")
            st.write(course["final_project_text"])
            with st.form(f"submit_final_{course['id']}"):
                fp_file = st.file_uploader("Fichier (script + rapport, .zip/.txt/.R/.py/.do)", key=f"fpf-{course['id']}")
                fp_code = st.text_area("Ou collez votre rapport de synthèse ici", key=f"fpc-{course['id']}", height=150)
                fp_comment = st.text_input("Commentaire (optionnel)", key=f"fpm-{course['id']}")
                fp_go = st.form_submit_button("📤 Soumettre le projet final")
            if fp_go:
                content, fname = None, None
                if fp_file is not None:
                    fname = fp_file.name
                    try:
                        content = fp_file.getvalue().decode("utf-8", errors="replace")
                    except Exception:
                        content = "(fichier binaire non prévisualisable)"
                elif fp_code.strip():
                    content, fname = fp_code, f"projet_final_{course['slug']}.txt"
                if not content:
                    st.error("Ajoutez un fichier ou collez votre rapport avant de soumettre.")
                else:
                    add_submission(
                        user["id"], course["id"], f"Projet final — {course['title']}", kind="FINAL_PROJECT",
                        file_name=fname, file_content=content, comment=fp_comment,
                    )
                    st.success("Projet soumis — un administrateur validera votre certification après correction.")
                    st.rerun()

footer()
