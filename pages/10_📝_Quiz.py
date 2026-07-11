import json
from datetime import datetime

import streamlit as st

from common import init_page, footer
from db import get_conn, new_id
from i18n import t
import auth

init_page(t("Quiz", "Quiz"), icon="📝")

user = auth.current_user()
if not user:
    st.warning(t("Connectez-vous pour passer un quiz.", "Log in to take a quiz."))
    st.page_link("pages/5_🔐_Connexion.py", label=t("Se connecter →", "Log in →"))
    st.stop()

quiz_id = st.session_state.get("active_quiz_id")
if not quiz_id:
    st.info(t(
        "Aucun quiz sélectionné. Ouvrez un cours puis cliquez sur un quiz de module.",
        "No quiz selected. Open a course, then click on a module quiz.",
    ))
    st.page_link("pages/1_📚_Cours.py", label=t("← Aller au catalogue", "← Go to catalog"))
    st.stop()

conn = get_conn()
quiz = conn.execute("SELECT * FROM quizzes WHERE id=? AND published=1", (quiz_id,)).fetchone()
if not quiz:
    conn.close()
    st.error(t("Quiz introuvable.", "Quiz not found."))
    st.stop()
questions = conn.execute("SELECT * FROM questions WHERE quiz_id=? ORDER BY position", (quiz_id,)).fetchall()
conn.close()

st.title(quiz["title"])
st.caption(t(f"Seuil de réussite : {quiz['pass_score_pct']}%", f"Passing score: {quiz['pass_score_pct']}%"))

result_key = f"quiz_result_{quiz_id}"

if result_key not in st.session_state:
    answers = {}
    with st.form(f"quiz_form_{quiz_id}"):
        for idx, q in enumerate(questions):
            st.markdown(f'<div class="cd-card">', unsafe_allow_html=True)
            st.markdown(f"**{idx + 1}. {q['prompt']}**")
            options = json.loads(q["options"]) if q["options"] else None
            if q["type"] in ("MCQ_SINGLE", "TRUE_FALSE"):
                opts = options or [
                    {"id": "true", "text": t("Vrai", "True")},
                    {"id": "false", "text": t("Faux", "False")},
                ]
                labels = [o["text"] for o in opts]
                choice = st.radio(t("Réponse", "Answer"), labels, key=f"q_{q['id']}", label_visibility="collapsed")
                answers[q["id"]] = next(o["id"] for o in opts if o["text"] == choice)
            elif q["type"] == "MCQ_MULTI":
                selected = []
                for o in options or []:
                    if st.checkbox(o["text"], key=f"q_{q['id']}_{o['id']}"):
                        selected.append(o["id"])
                answers[q["id"]] = selected
            elif q["type"] == "SHORT_ANSWER":
                answers[q["id"]] = st.text_input(t("Votre réponse", "Your answer"), key=f"q_{q['id']}", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
        submitted = st.form_submit_button(t("Soumettre mes réponses", "Submit my answers"))

    if submitted:
        earned, total, correction = 0, 0, []
        for q in questions:
            total += q["points"]
            expected = json.loads(q["correct_answer"])
            given = answers.get(q["id"])
            if q["type"] == "MCQ_MULTI":
                correct = sorted(given or []) == sorted(expected)
            elif q["type"] == "SHORT_ANSWER":
                correct = str(given or "").strip().lower() == str(expected).strip().lower()
            else:
                exp = expected[0] if isinstance(expected, list) else expected
                correct = str(given) == str(exp)
            if correct:
                earned += q["points"]
            correction.append({
                "prompt": q["prompt"], "given": given, "correct": correct,
                "correct_answer": expected, "explanation": q["explanation"],
            })
        score_pct = round(earned / total * 100) if total else 0
        passed = score_pct >= quiz["pass_score_pct"]

        conn = get_conn()
        conn.execute(
            "INSERT INTO quiz_attempts(id,user_id,quiz_id,answers,score_pct,passed,submitted_at,"
            "earned_points,total_points) VALUES (?,?,?,?,?,?,?,?,?)",
            (new_id(), user["id"], quiz_id, json.dumps(answers), score_pct, int(passed),
             datetime.utcnow().isoformat(), earned, total),
        )
        conn.commit()
        conn.close()

        st.session_state[result_key] = {"score_pct": score_pct, "passed": passed, "correction": correction}
        st.rerun()
else:
    result = st.session_state[result_key]
    bg = "#2F5D50" if result["passed"] else "#B4622B"
    status_txt = (
        t("Quiz réussi — félicitations !", "Quiz passed — congratulations!")
        if result["passed"]
        else t(f"Non validé (seuil : {quiz['pass_score_pct']}%)", f"Not passed (threshold: {quiz['pass_score_pct']}%)")
    )
    st.markdown(
        f'<div style="background:rgba(47,93,80,0.08); border-radius:18px; padding:1.6rem; text-align:center;">'
        f'<p style="font-family:Fraunces,serif; font-size:2rem; color:{bg}; margin:0;">{result["score_pct"]}%</p>'
        f'<p style="color:{bg};">{status_txt}</p></div>',
        unsafe_allow_html=True,
    )
    for idx, c in enumerate(result["correction"]):
        ok = c["correct"]
        reponse_label = t("Votre réponse", "Your answer")
        attendue_label = t("Réponse attendue", "Expected answer")
        st.markdown(
            f'<div class="cd-card" style="border-color:{"#2F5D50" if ok else "#B4622B"};">'
            f'<b>{idx + 1}. {c["prompt"]}</b><br>{reponse_label} : {c["given"]}'
            + ("" if ok else f'<br>{attendue_label} : {c["correct_answer"]}')
            + (f'<br><i>{c["explanation"]}</i>' if c["explanation"] else "")
            + "</div>",
            unsafe_allow_html=True,
        )
    if st.button(t("Repasser le quiz", "Retake the quiz")):
        del st.session_state[result_key]
        st.rerun()
    st.page_link("pages/7_🎓_Mon_espace.py", label=t("← Retour à mon espace", "← Back to my space"))

footer()
