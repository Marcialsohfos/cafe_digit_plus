import urllib.parse
from datetime import datetime

import streamlit as st

from common import init_page, footer
from db import get_conn, new_id, get_settings
from i18n import t
from mailer import send_support_email, smtp_configured
import auth

init_page(t("Support", "Support"), icon="✉️")

settings = get_settings()
support_email = settings["support_email"]

st.title(t("Écrire à l'administration", "Contact the administration"))
st.write(
    t(
        "Vous pouvez écrire directement à l'équipe de Café_digit pour une **demande de paiement**, "
        f"une **doléance** ou une **requête générale**. Votre message est transmis à **{support_email}** "
        "et reste consultable par l'administration dans le back-office.",
        "You can write directly to the Café_digit team for a **payment request**, "
        f"a **complaint** or a **general inquiry**. Your message is sent to **{support_email}** "
        "and remains visible to the administration in the back-office.",
    )
)

user = auth.current_user()

CATEGORY_OPTIONS = [
    ("PAYMENT_REQUEST", t("Demande de paiement", "Payment request")),
    ("COMPLAINT", t("Doléance", "Complaint")),
    ("GENERAL_REQUEST", t("Requête générale", "General inquiry")),
]

with st.form("support_form"):
    c1, c2 = st.columns(2)
    full_name = c1.text_input(t("Nom complet *", "Full name *"), value=(user["fullName"] if user else ""))
    email = c2.text_input(t("E-mail *", "Email *"), value=(user["email"] if user else ""))
    c3, c4 = st.columns(2)
    phone = c3.text_input(t("Téléphone", "Phone"))
    category_code = c4.selectbox(
        t("Catégorie", "Category"),
        CATEGORY_OPTIONS,
        format_func=lambda opt: opt[1],
    )
    subject = st.text_input(t("Objet", "Subject"), value=t("Message depuis Café_digit", "Message from Café_digit"))
    message = st.text_area(t("Message *", "Message *"), height=160)
    submitted = st.form_submit_button(t("Envoyer au support", "Send to support"))

if submitted:
    if not full_name or not email or not message:
        st.error(t("Nom, e-mail et message sont requis.", "Name, email and message are required."))
    else:
        category, category_label = category_code

        conn = get_conn()
        conn.execute(
            "INSERT INTO support_messages(id,full_name,email,phone,category,subject,message,status,created_at,handled_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (new_id(), full_name, email.lower(), phone or None, category,
             subject or t("Message depuis Café_digit", "Message from Café_digit"),
             message, "NEW", datetime.utcnow().isoformat(), None),
        )
        conn.commit()
        conn.close()

        sent, info = send_support_email(support_email, full_name, email, phone, category_label, subject, message)
        st.success(t(
            "Votre message a bien été enregistré et transmis à l'administration. "
            "Vous recevrez une réponse dans les meilleurs délais.",
            "Your message has been recorded and sent to the administration. "
            "You will receive a reply as soon as possible.",
        ))
        if not sent:
            st.caption(info)

st.markdown("---")
st.caption(
    t(
        f"Vous pouvez aussi écrire directement à **{support_email}** depuis votre messagerie habituelle : "
        f"[ouvrir un e-mail](mailto:{support_email}?subject={urllib.parse.quote('Message depuis Café_digit')}).",
        f"You can also write directly to **{support_email}** from your usual mail client: "
        f"[open an email](mailto:{support_email}?subject={urllib.parse.quote('Message from Café_digit')}).",
    )
)
if not smtp_configured():
    st.caption(
        t(
            "ℹ️ L'envoi SMTP automatique n'est pas configuré sur cette instance — chaque message reste "
            "néanmoins enregistré et visible par les administrateurs dans le back-office.",
            "ℹ️ Automatic SMTP sending is not configured on this instance — every message is still "
            "recorded and visible to administrators in the back-office.",
        )
    )

footer()
