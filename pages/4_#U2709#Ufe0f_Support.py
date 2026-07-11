import urllib.parse
from datetime import datetime

import streamlit as st

from common import init_page, footer
from db import get_conn, new_id, get_settings
from mailer import send_support_email, smtp_configured
import auth

init_page("Support", icon="✉️")

settings = get_settings()
support_email = settings["support_email"]

st.title("Écrire à l'administration")
st.write(
    "Vous pouvez écrire directement à l'équipe de Café_digit pour une **demande de paiement**, "
    f"une **doléance** ou une **requête générale**. Votre message est transmis à **{support_email}** "
    "et reste consultable par l'administration dans le back-office."
)

user = auth.current_user()

with st.form("support_form"):
    c1, c2 = st.columns(2)
    full_name = c1.text_input("Nom complet *", value=(user["fullName"] if user else ""))
    email = c2.text_input("E-mail *", value=(user["email"] if user else ""))
    c3, c4 = st.columns(2)
    phone = c3.text_input("Téléphone")
    category_label = c4.selectbox(
        "Catégorie",
        ["Demande de paiement", "Doléance", "Requête générale"],
    )
    subject = st.text_input("Objet", value="Message depuis Café_digit")
    message = st.text_area("Message *", height=160)
    submitted = st.form_submit_button("Envoyer au support")

if submitted:
    if not full_name or not email or not message:
        st.error("Nom, e-mail et message sont requis.")
    else:
        category_map = {
            "Demande de paiement": "PAYMENT_REQUEST",
            "Doléance": "COMPLAINT",
            "Requête générale": "GENERAL_REQUEST",
        }
        category = category_map[category_label]

        conn = get_conn()
        conn.execute(
            "INSERT INTO support_messages(id,full_name,email,phone,category,subject,message,status,created_at,handled_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (new_id(), full_name, email.lower(), phone or None, category, subject or "Message depuis Café_digit",
             message, "NEW", datetime.utcnow().isoformat(), None),
        )
        conn.commit()
        conn.close()

        sent, info = send_support_email(support_email, full_name, email, phone, category_label, subject, message)
        st.success(
            "Votre message a bien été enregistré et transmis à l'administration. "
            "Vous recevrez une réponse dans les meilleurs délais."
        )
        if not sent:
            st.caption(info)

mailto_body = urllib.parse.quote(f"Nom : \n E-mail : \n\nVotre message ici…")
st.markdown("---")
st.caption(
    f"Vous pouvez aussi écrire directement à **{support_email}** depuis votre messagerie habituelle : "
    f"[ouvrir un e-mail](mailto:{support_email}?subject={urllib.parse.quote('Message depuis Café_digit')})."
)
if not smtp_configured():
    st.caption(
        "ℹ️ L'envoi SMTP automatique n'est pas configuré sur cette instance — chaque message reste "
        "néanmoins enregistré et visible par les administrateurs dans le back-office."
    )

footer()
