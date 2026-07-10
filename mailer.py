"""
Café_digit — envoi des messages du formulaire de support vers l'adresse
support@scsmaubmar.org. Si aucun serveur SMTP n'est configuré dans
st.secrets (section [smtp]), le message reste de toute façon enregistré en
base et visible par les administrateurs dans le back-office ; l'envoi réel
de l'e-mail est alors simplement ignoré (aucune erreur affichée au membre).
"""
import smtplib
from email.mime.text import MIMEText

import streamlit as st


def smtp_configured() -> bool:
    try:
        return "smtp" in st.secrets
    except Exception:
        return False


def send_support_email(to_addr, full_name, from_email, phone, category, subject, message) -> tuple[bool, str]:
    if not smtp_configured():
        return False, "SMTP non configuré — message conservé dans le back-office uniquement."

    cfg = st.secrets["smtp"]
    body = (
        f"Nouvelle demande depuis Café_digit\n\n"
        f"Catégorie : {category}\n"
        f"Nom : {full_name}\n"
        f"E-mail du membre : {from_email}\n"
        f"Téléphone : {phone or '—'}\n\n"
        f"Message :\n{message}\n"
    )
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = f"[Café_digit] {subject or 'Nouvelle demande'}"
    msg["From"] = cfg.get("sender", to_addr)
    msg["To"] = to_addr
    msg["Reply-To"] = from_email

    try:
        with smtplib.SMTP(cfg["host"], int(cfg.get("port", 587)), timeout=15) as server:
            if cfg.get("use_tls", True):
                server.starttls()
            if cfg.get("user"):
                server.login(cfg["user"], cfg["password"])
            server.sendmail(msg["From"], [to_addr], msg.as_string())
        return True, "E-mail envoyé."
    except Exception as exc:  # noqa: BLE001
        return False, f"Envoi impossible ({exc}). Le message reste enregistré dans le back-office."
