import json
from datetime import datetime

import streamlit as st

from common import init_page, footer
from db import (
    get_conn, new_id, get_settings, set_setting,
    get_sandbox_examples, add_sandbox_example, delete_sandbox_example,
    validate_subscription_by_email, PLAN_PRICES_FCFA,
)
import auth

init_page("Administration", icon="🛠️")

if not auth.is_admin():
    st.error("Cette section est réservée aux administrateurs de Café_digit.")
    st.page_link("pages/5_🔐_Connexion.py", label="Se connecter →")
    st.page_link("pages/8_🔑_Super_Admin.py", label="Accès Super Admin →")
    st.stop()

user = auth.current_user()
st.title("🛠️ Administration Café_digit")
st.caption(f"Connecté en tant que {user['fullName']} — {user['role']}")


def slugify(text):
    import re
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or new_id()[:8]


tabs = ["📊 Tableau de bord", "📚 Cours & contenus", "📝 Quiz & questions",
        "🧪 Sandbox R", "👥 Utilisateurs", "💳 Paiements", "✉️ Support", "⚙️ Paramètres"]
if auth.is_super_admin():
    tabs.append("🛡️ Gestion des admins")

selected = st.tabs(tabs)
TAB = {name: i for i, name in enumerate(tabs)}

# ---------------------------------------------------------------- Dashboard
with selected[TAB["📊 Tableau de bord"]]:
    conn = get_conn()
    n_users = conn.execute("SELECT COUNT(*) c FROM users WHERE role='STUDENT'").fetchone()["c"]
    n_courses = conn.execute("SELECT COUNT(*) c FROM courses").fetchone()["c"]
    n_enroll = conn.execute("SELECT COUNT(*) c FROM enrollments").fetchone()["c"]
    n_attempts = conn.execute("SELECT COUNT(*) c FROM quiz_attempts").fetchone()["c"]
    n_active_subs = conn.execute("SELECT COUNT(*) c FROM subscriptions WHERE status='ACTIVE' AND plan!='FREE'").fetchone()["c"]
    n_tickets_new = conn.execute("SELECT COUNT(*) c FROM support_messages WHERE status='NEW'").fetchone()["c"]
    conn.close()
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Membres", n_users)
    c2.metric("Cours", n_courses)
    c3.metric("Inscriptions", n_enroll)
    c4.metric("Tentatives quiz", n_attempts)
    c5.metric("Abonnements actifs", n_active_subs)
    c6.metric("Tickets support ouverts", n_tickets_new)

# --------------------------------------------------------- Cours & contenus
with selected[TAB["📚 Cours & contenus"]]:
    conn = get_conn()
    courses = conn.execute("SELECT * FROM courses ORDER BY created_at DESC").fetchall()
    conn.close()

    with st.expander("➕ Créer un nouveau cours"):
        with st.form("new_course"):
            title = st.text_input("Titre *")
            description = st.text_area("Description courte *", help="Résumé affiché dans le catalogue.")
            context = st.text_area(
                "Présentation du cours & objectifs (contexte)", height=180,
                placeholder=(
                    "Ex : Objectifs de la formation, public visé, prérequis, équipe pédagogique, "
                    "ressources d'installation... Ce texte s'affiche en tête de la page du cours."
                ),
            )
            pillar = st.selectbox("Pilier", ["Modélisation mathématique", "Intelligence artificielle", "Big Data", "Cas pratiques"])
            level = st.selectbox("Niveau", ["Débutant", "Intermédiaire", "Avancé"])
            price = st.number_input("Prix (FCFA, 0 = gratuit)", min_value=0, step=1000, value=0)
            premium_only = st.checkbox("Réservé aux membres Premium")
            published = st.checkbox("Publier immédiatement", value=True)
            ok = st.form_submit_button("Créer le cours")
        if ok:
            if not title or not description:
                st.error("Titre et description requis.")
            else:
                conn = get_conn()
                base_slug = slugify(title)
                slug, n = base_slug, 1
                while conn.execute("SELECT id FROM courses WHERE slug=?", (slug,)).fetchone():
                    slug = f"{base_slug}-{n}"
                    n += 1
                conn.execute(
                    "INSERT INTO courses(id,title,slug,description,context,pillar,level,price_fcfa,"
                    "is_premium_only,cover_image_url,published,author_id,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (new_id(), title, slug, description, context or None, pillar, level, int(price),
                     int(premium_only), None, int(published), user["id"], datetime.utcnow().isoformat()),
                )
                conn.commit()
                conn.close()
                st.success("Cours créé.")
                st.rerun()

    st.markdown("---")
    if not courses:
        st.info("Aucun cours pour le moment.")
    for course in courses:
        with st.expander(f"{'✅' if course['published'] else '🚧'} {course['title']}  ·  {course['pillar']}"):
            with st.form(f"edit_course_{course['id']}"):
                e_title = st.text_input("Titre", value=course["title"])
                e_desc = st.text_area("Description courte", value=course["description"])
                e_context = st.text_area(
                    "Présentation du cours & objectifs (contexte)",
                    value=course["context"] or "", height=180,
                )
                e_price = st.number_input("Prix (FCFA)", min_value=0, step=1000, value=course["price_fcfa"])
                e_premium = st.checkbox("Réservé Premium", value=bool(course["is_premium_only"]))
                e_pub = st.checkbox("Publié", value=bool(course["published"]))
                col_a, col_b = st.columns(2)
                save = col_a.form_submit_button("💾 Enregistrer")
                delete = col_b.form_submit_button("🗑️ Supprimer le cours")
            if save:
                conn = get_conn()
                conn.execute(
                    "UPDATE courses SET title=?, description=?, context=?, price_fcfa=?, is_premium_only=?, "
                    "published=? WHERE id=?",
                    (e_title, e_desc, e_context or None, int(e_price), int(e_premium), int(e_pub), course["id"]),
                )
                conn.commit()
                conn.close()
                st.success("Cours mis à jour.")
                st.rerun()
            if delete:
                conn = get_conn()
                conn.execute("DELETE FROM courses WHERE id=?", (course["id"],))
                conn.commit()
                conn.close()
                st.warning("Cours supprimé.")
                st.rerun()

            st.markdown("##### Modules, leçons, exercices & travaux pratiques")
            conn = get_conn()
            modules = conn.execute("SELECT * FROM modules WHERE course_id=? ORDER BY position", (course["id"],)).fetchall()
            conn.close()

            with st.form(f"new_module_{course['id']}"):
                m_title = st.text_input("Titre du nouveau module (ex : Module 1 — ...)", key=f"mtitle-{course['id']}")
                m_objective = st.text_area(
                    "Objectif du module (canevas court : « Objectif : ... »)",
                    key=f"mobj-{course['id']}", height=80,
                )
                m_add = st.form_submit_button("➕ Ajouter un module")
            if m_add and m_title:
                conn = get_conn()
                conn.execute("INSERT INTO modules(id,title,objective,position,course_id) VALUES (?,?,?,?,?)",
                             (new_id(), m_title, m_objective or None, len(modules), course["id"]))
                conn.commit()
                conn.close()
                st.rerun()

            for module in modules:
                with st.expander(f"✏️ {module['title']}", expanded=False):
                    with st.form(f"edit_module_{module['id']}"):
                        em_title = st.text_input("Titre du module", value=module["title"], key=f"emt-{module['id']}")
                        em_obj = st.text_area(
                            "Objectif du module", value=module["objective"] or "",
                            key=f"emo-{module['id']}", height=80,
                        )
                        em_save = st.form_submit_button("💾 Enregistrer le module")
                    if em_save:
                        conn = get_conn()
                        conn.execute("UPDATE modules SET title=?, objective=? WHERE id=?",
                                     (em_title, em_obj or None, module["id"]))
                        conn.commit()
                        conn.close()
                        st.rerun()
                if module["objective"]:
                    st.caption(f"🎯 {module['objective']}")
                st.markdown(f"**{module['title']}**")
                conn = get_conn()
                lessons = conn.execute("SELECT * FROM lessons WHERE module_id=? ORDER BY position", (module["id"],)).fetchall()
                quizzes = conn.execute("SELECT * FROM quizzes WHERE module_id=?", (module["id"],)).fetchall()
                conn.close()

                for l in lessons:
                    lc1, lc2 = st.columns([5, 1])
                    lc1.caption(f"{l['type']} — {l['title']}")
                    if lc2.button("🗑️", key=f"dellesson-{l['id']}"):
                        conn = get_conn()
                        conn.execute("DELETE FROM lessons WHERE id=?", (l["id"],))
                        conn.commit()
                        conn.close()
                        st.rerun()

                for q in quizzes:
                    st.caption(f"📝 Quiz — {q['title']} ({'publié' if q['published'] else 'brouillon'})")

                with st.form(f"new_lesson_{module['id']}"):
                    lt = st.text_input("Titre de la leçon / exercice / TP", key=f"lt-{module['id']}")
                    ltype = st.selectbox(
                        "Type", ["TEXT", "VIDEO", "PDF", "R_SANDBOX"],
                        format_func=lambda x: {"TEXT": "📖 Texte / cours", "VIDEO": "🎬 Vidéo",
                                                "PDF": "📄 PDF (exercice / TP)", "R_SANDBOX": "🧪 Sandbox R (pratique)"}[x],
                        key=f"lty-{module['id']}",
                    )
                    lcontent = st.text_area("Contenu texte / code R / notes", key=f"lc-{module['id']}")
                    lurl = st.text_input("URL vidéo ou PDF (optionnel)", key=f"lu-{module['id']}")
                    ladd = st.form_submit_button("➕ Ajouter le contenu")
                if ladd and lt:
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO lessons(id,title,type,position,video_url,pdf_url,content,duration_sec,module_id) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (new_id(), lt, ltype, len(lessons),
                         lurl if ltype == "VIDEO" else None, lurl if ltype == "PDF" else None,
                         lcontent, None, module["id"]),
                    )
                    conn.commit()
                    conn.close()
                    st.rerun()

                with st.form(f"new_quiz_{module['id']}"):
                    qt = st.text_input("Titre du quiz / évaluation", key=f"qt-{module['id']}")
                    qpass = st.number_input("Seuil de réussite (%)", 0, 100, 60, key=f"qp-{module['id']}")
                    qadd = st.form_submit_button("➕ Créer un quiz pour ce module")
                if qadd and qt:
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO quizzes(id,title,module_id,pass_score_pct,published,created_at) VALUES (?,?,?,?,?,?)",
                        (new_id(), qt, module["id"], int(qpass), 1, datetime.utcnow().isoformat()),
                    )
                    conn.commit()
                    conn.close()
                    st.rerun()

                if st.button("🗑️ Supprimer ce module", key=f"delmod-{module['id']}"):
                    conn = get_conn()
                    conn.execute("DELETE FROM modules WHERE id=?", (module["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
                st.markdown("---")

# --------------------------------------------------------- Quiz & questions
with selected[TAB["📝 Quiz & questions"]]:
    conn = get_conn()
    all_courses = [dict(r) for r in conn.execute("SELECT id, title FROM courses ORDER BY created_at DESC").fetchall()]
    conn.close()

    with st.expander("➕ Créer un quiz pour un cours (nouveau ou existant)"):
        if not all_courses:
            st.info("Créez d'abord un cours dans l'onglet « Cours & contenus ».")
        else:
            qc_course = st.selectbox(
                "Cours", all_courses, format_func=lambda c: c["title"], key="qc_course_select",
            )
            conn = get_conn()
            qc_modules = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM modules WHERE course_id=? ORDER BY position", (qc_course["id"],)
                ).fetchall()
            ]
            conn.close()
            if not qc_modules:
                st.info("Ce cours n'a pas encore de module — ajoutez-en un dans « Cours & contenus ».")
            else:
                with st.form("quick_new_quiz"):
                    qc_module = st.selectbox("Module", qc_modules, format_func=lambda m: m["title"])
                    qc_title = st.text_input("Titre du quiz")
                    qc_pass = st.number_input("Seuil de réussite (%)", 0, 100, 60)
                    qc_submit = st.form_submit_button("➕ Créer le quiz")
                if qc_submit and qc_title:
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO quizzes(id,title,module_id,pass_score_pct,published,created_at) VALUES (?,?,?,?,?,?)",
                        (new_id(), qc_title, qc_module["id"], int(qc_pass), 1, datetime.utcnow().isoformat()),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Quiz créé — ajoutez maintenant ses questions ci-dessous.")
                    st.rerun()

    st.markdown("---")
    conn = get_conn()
    quizzes = conn.execute(
        "SELECT q.*, m.title as module_title, c.title as course_title FROM quizzes q "
        "JOIN modules m ON q.module_id=m.id JOIN courses c ON m.course_id=c.id ORDER BY q.created_at DESC"
    ).fetchall()
    conn.close()

    course_filter = st.selectbox(
        "Filtrer par cours", ["Tous les cours"] + [c["title"] for c in all_courses], key="quiz_course_filter",
    )
    if course_filter != "Tous les cours":
        quizzes = [q for q in quizzes if q["course_title"] == course_filter]

    if not quizzes:
        st.info("Aucun quiz pour ce filtre. Créez-en un ci-dessus ou depuis l'onglet « Cours & contenus ».")
    for quiz in quizzes:
        with st.expander(f"📝 {quiz['title']} — {quiz['course_title']} / {quiz['module_title']}"):
            conn = get_conn()
            questions = conn.execute("SELECT * FROM questions WHERE quiz_id=? ORDER BY position", (quiz["id"],)).fetchall()
            conn.close()
            for q in questions:
                qc1, qc2 = st.columns([5, 1])
                qc1.write(f"**{q['prompt']}** _({q['type']}, {q['points']} pt)_")
                if qc2.button("🗑️", key=f"delq-{q['id']}"):
                    conn = get_conn()
                    conn.execute("DELETE FROM questions WHERE id=?", (q["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()

            st.markdown("###### Ajouter une question")
            with st.form(f"new_question_{quiz['id']}"):
                prompt = st.text_area("Énoncé", key=f"qp-{quiz['id']}")
                qtype = st.selectbox("Type", ["MCQ_SINGLE", "MCQ_MULTI", "TRUE_FALSE", "SHORT_ANSWER"], key=f"qt-{quiz['id']}")
                opts_raw = st.text_area(
                    "Options (une par ligne, format id:texte) — pour QCM uniquement",
                    placeholder="a:Réponse possible A\nb:Réponse possible B\nc:Réponse possible C",
                    key=f"qo-{quiz['id']}",
                )
                correct_raw = st.text_input(
                    "Réponse(s) correcte(s) — id(s) séparés par une virgule, ou texte exact pour réponse courte",
                    key=f"qc-{quiz['id']}",
                )
                explanation = st.text_input("Explication / correction affichée après soumission", key=f"qe-{quiz['id']}")
                points = st.number_input("Points", min_value=1, value=1, key=f"qpt-{quiz['id']}")
                addq = st.form_submit_button("➕ Ajouter la question")
            if addq and prompt and correct_raw:
                options = None
                if qtype in ("MCQ_SINGLE", "MCQ_MULTI") and opts_raw.strip():
                    options = [
                        {"id": line.split(":", 1)[0].strip(), "text": line.split(":", 1)[1].strip()}
                        for line in opts_raw.strip().splitlines() if ":" in line
                    ]
                if qtype in ("MCQ_MULTI",):
                    correct = [x.strip() for x in correct_raw.split(",") if x.strip()]
                elif qtype in ("MCQ_SINGLE", "TRUE_FALSE"):
                    correct = [correct_raw.strip()]
                else:
                    correct = correct_raw.strip()
                conn = get_conn()
                conn.execute(
                    "INSERT INTO questions(id,quiz_id,type,prompt,position,options,correct_answer,explanation,points) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (new_id(), quiz["id"], qtype, prompt, len(questions),
                     json.dumps(options) if options else None, json.dumps(correct), explanation, int(points)),
                )
                conn.commit()
                conn.close()
                st.rerun()

            if st.button("🗑️ Supprimer ce quiz", key=f"delquiz-{quiz['id']}"):
                conn = get_conn()
                conn.execute("DELETE FROM quizzes WHERE id=?", (quiz["id"],))
                conn.commit()
                conn.close()
                st.rerun()

# ------------------------------------------------------------------ Sandbox R
with selected[TAB["🧪 Sandbox R"]]:
    st.caption(
        "Chargez ici de nouveaux exemples d'applications R qui apparaîtront directement "
        "dans la page Sandbox R, prêts à être exécutés par les apprenants."
    )
    with st.expander("➕ Ajouter un nouvel exemple"):
        with st.form("new_sandbox_example"):
            sb_title = st.text_input("Titre de l'exemple *", placeholder="Ex : Régression logistique — risque de rechute")
            sb_desc = st.text_area("Description courte (affichée sous le bouton)")
            sb_code = st.text_area(
                "Code R *", height=220,
                placeholder="# Collez ici le script R de démonstration\n...",
            )
            sb_pub = st.checkbox("Publier immédiatement", value=True)
            sb_add = st.form_submit_button("➕ Ajouter l'exemple")
        if sb_add:
            if not sb_title or not sb_code.strip():
                st.error("Titre et code R sont requis.")
            else:
                add_sandbox_example(sb_title, sb_desc, sb_code, user["id"], published=sb_pub)
                st.success("Exemple ajouté à la Sandbox R.")
                st.rerun()

    st.markdown("---")
    examples = get_sandbox_examples(published_only=False)
    if not examples:
        st.info("Aucun exemple personnalisé pour le moment — les deux exemples par défaut restent visibles.")
    for ex in examples:
        with st.expander(f"{'✅' if ex['published'] else '🚧'} {ex['title']}"):
            st.markdown(f'<div class="cd-mono">{ex["code"]}</div>', unsafe_allow_html=True)
            if ex["description"]:
                st.caption(ex["description"])
            if st.button("🗑️ Supprimer", key=f"delsbex-{ex['id']}"):
                delete_sandbox_example(ex["id"])
                st.rerun()

# ------------------------------------------------------------- Utilisateurs
with selected[TAB["👥 Utilisateurs"]]:
    conn = get_conn()
    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    st.caption(f"{len(users)} comptes enregistrés")
    for u in users:
        c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
        c1.write(f"**{u['full_name']}**")
        c2.write(u["email"])
        c3.write(u["role"])
        if u["role"] == "STUDENT" and auth.is_admin():
            if c4.button("Promouvoir Admin", key=f"promote-{u['id']}"):
                conn = get_conn()
                conn.execute("UPDATE users SET role='ADMIN' WHERE id=?", (u["id"],))
                conn.commit()
                conn.close()
                st.rerun()
        elif u["role"] == "ADMIN" and auth.is_super_admin():
            if c4.button("Rétrograder", key=f"demote-{u['id']}"):
                conn = get_conn()
                conn.execute("UPDATE users SET role='STUDENT' WHERE id=?", (u["id"],))
                conn.commit()
                conn.close()
                st.rerun()

# ---------------------------------------------------------------- Paiements
with selected[TAB["💳 Paiements"]]:
    st.markdown("##### ✅ Valider un abonnement Premium directement")
    st.caption(
        "Pour un paiement reçu hors plateforme (Mobile Money, dépôt bancaire...), saisissez "
        "l'e-mail de l'abonné et la référence de paiement : l'accès premium sera activé "
        "immédiatement, sans attendre de demande préalable."
    )
    with st.form("manual_subscription_validation"):
        mv_email = st.text_input("E-mail de l'abonné *", placeholder="exemple@mail.com")
        mv_plan = st.selectbox("Offre", list(PLAN_PRICES_FCFA.keys()), format_func=lambda p: {
            "PREMIUM": "Premium mensuel", "MODULE": "Module certifiant", "B2B": "Mission sur mesure",
        }.get(p, p))
        mv_ref = st.text_input("Référence de paiement *", placeholder="Ex : MTN-2026-XXXXXX")
        mv_amount = st.number_input("Montant reçu (FCFA)", min_value=0, step=1000,
                                     value=PLAN_PRICES_FCFA[mv_plan])
        mv_duration = st.number_input("Durée de l'accès (jours, 0 = illimité)", min_value=0, value=30, step=30)
        mv_submit = st.form_submit_button("✅ Valider et activer l'espace premium")
    if mv_submit:
        if not mv_email or not mv_ref:
            st.error("L'e-mail et la référence de paiement sont requis.")
        else:
            validated_user, err = validate_subscription_by_email(
                mv_email, mv_plan, mv_ref, mv_amount, user["id"], duration_days=int(mv_duration) or None,
            )
            if err:
                st.error(err)
            else:
                st.success(
                    f"Abonnement {mv_plan} validé pour {validated_user['full_name']} "
                    f"({validated_user['email']}) — l'espace premium est désormais accessible."
                )
                st.rerun()

    st.markdown("---")
    st.markdown("##### Demandes reçues via la plateforme")
    conn = get_conn()
    subs = conn.execute(
        "SELECT s.*, u.full_name, u.email FROM subscriptions s JOIN users u ON s.user_id=u.id "
        "WHERE s.plan != 'FREE' ORDER BY s.started_at DESC"
    ).fetchall()
    conn.close()
    if not subs:
        st.info("Aucune demande d'abonnement payante pour le moment.")
    for s in subs:
        c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 2, 2])
        c1.write(s["full_name"])
        c2.write(f"{s['plan']} — {s['amount_fcfa']:,} FCFA".replace(",", " "))
        c3.write(s["payment_ref"] or "—")
        c4.markdown(f'<span class="cd-badge">{s["status"]}</span>', unsafe_allow_html=True)
        if s["status"] == "PENDING":
            cc1, cc2 = c5.columns(2)
            if cc1.button("✅", key=f"val-{s['id']}"):
                conn = get_conn()
                conn.execute(
                    "UPDATE subscriptions SET status='ACTIVE', validated_by=?, validated_at=? WHERE id=?",
                    (user["id"], datetime.utcnow().isoformat(), s["id"]),
                )
                conn.commit()
                conn.close()
                st.rerun()
            if cc2.button("❌", key=f"rej-{s['id']}"):
                conn = get_conn()
                conn.execute("UPDATE subscriptions SET status='CANCELLED' WHERE id=?", (s["id"],))
                conn.commit()
                conn.close()
                st.rerun()

# ----------------------------------------------------------------- Support
with selected[TAB["✉️ Support"]]:
    conn = get_conn()
    tickets = conn.execute("SELECT * FROM support_messages ORDER BY created_at DESC").fetchall()
    conn.close()
    if not tickets:
        st.info("Aucun message reçu pour le moment.")
    for t in tickets:
        with st.expander(f"[{t['status']}] {t['subject']} — {t['full_name']} ({t['category']})"):
            st.write(t["message"])
            st.caption(f"{t['email']} · {t['phone'] or 'sans téléphone'} · {t['created_at']}")
            new_status = st.selectbox(
                "Statut", ["NEW", "IN_PROGRESS", "HANDLED"],
                index=["NEW", "IN_PROGRESS", "HANDLED"].index(t["status"]),
                key=f"status-{t['id']}",
            )
            if st.button("Mettre à jour", key=f"upd-{t['id']}"):
                conn = get_conn()
                conn.execute(
                    "UPDATE support_messages SET status=?, handled_at=? WHERE id=?",
                    (new_status, datetime.utcnow().isoformat() if new_status == "HANDLED" else None, t["id"]),
                )
                conn.commit()
                conn.close()
                st.rerun()

# --------------------------------------------------------------- Paramètres
with selected[TAB["⚙️ Paramètres"]]:
    settings = get_settings()
    with st.form("settings_form"):
        support_email = st.text_input("E-mail support", value=settings["support_email"])
        momo = st.text_input("Numéros MTN Mobile Money", value=settings["momo_numbers"])
        om = st.text_input("Numéros Orange Money", value=settings["om_numbers"])
        intl = st.text_area("Texte paiement carte internationale", value=settings["intl_card_text"])
        bank = st.text_area("Texte dépôt bancaire", value=settings["bank_deposit_text"])
        phones = st.text_input("Téléphones de contact", value=settings["contact_phones"])
        saved = st.form_submit_button("💾 Enregistrer les paramètres")
    if saved:
        for k, v in {
            "support_email": support_email, "momo_numbers": momo, "om_numbers": om,
            "intl_card_text": intl, "bank_deposit_text": bank, "contact_phones": phones,
        }.items():
            set_setting(k, v)
        st.success("Paramètres mis à jour.")
        st.rerun()

# ------------------------------------------------------- Gestion des admins
if auth.is_super_admin():
    with selected[TAB["🛡️ Gestion des admins"]]:
        conn = get_conn()
        admins = conn.execute("SELECT * FROM users WHERE role IN ('ADMIN','SUPER_ADMIN') ORDER BY created_at").fetchall()
        conn.close()
        st.caption("Le Super Admin peut ajouter d'autres administrateurs pour déposer des cours, "
                    "exercices, travaux pratiques et valider les inscriptions.")
        for a in admins:
            c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
            c1.write(a["full_name"])
            c2.write(a["email"])
            c3.write(a["role"])
            if a["role"] == "ADMIN" and a["id"] != user["id"]:
                if c4.button("Rétrograder", key=f"revoke-{a['id']}"):
                    conn = get_conn()
                    conn.execute("UPDATE users SET role='STUDENT' WHERE id=?", (a["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()

        st.markdown("---")
        st.markdown("##### ➕ Ajouter un nouvel administrateur")
        with st.form("new_admin"):
            a_name = st.text_input("Nom complet *")
            a_email = st.text_input("E-mail *")
            a_pass = st.text_input("Mot de passe (8 caractères min.) *", type="password")
            a_add = st.form_submit_button("Créer le compte administrateur")
        if a_add:
            if not a_name or not a_email or len(a_pass) < 8:
                st.error("Nom, e-mail et mot de passe (8 caractères min.) sont requis.")
            else:
                new_user, err = auth.register_user(a_email, a_pass, a_name)
                if err:
                    st.error(err)
                else:
                    conn = get_conn()
                    conn.execute("UPDATE users SET role='ADMIN' WHERE id=?", (new_user["id"],))
                    conn.commit()
                    conn.close()
                    st.success(f"Administrateur {a_name} créé.")
                    st.rerun()

footer()
