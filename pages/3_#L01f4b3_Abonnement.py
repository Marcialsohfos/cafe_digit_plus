from datetime import datetime, timedelta

import streamlit as st

from common import init_page, footer
from db import get_conn, new_id, get_settings, PLAN_PRICES_FCFA
import auth

init_page("Abonnement", icon="💳")

st.title("Nos offres")
st.write(
    "Le palier communautaire reste gratuit. Choisissez une offre payante pour débloquer les "
    "modules certifiants, le mentorat ou une mission sur mesure."
)

OFFRES = [
    ("PREMIUM", "Premium mensuel", "15 000 FCFA / mois", "Replays illimités, ateliers en direct, mentorat de groupe."),
    ("MODULE", "Module certifiant", "≈ 60 000 FCFA", "Cycle de 4 à 6 semaines, certificat Lab_Math."),
    ("B2B", "Mission sur mesure", "Sur devis (500k – 2,5M FCFA)", "Formation dédiée entreprise, ONG ou collectivité."),
]

if "selected_plan" not in st.session_state:
    st.session_state["selected_plan"] = None

cols = st.columns(3)
for c, (plan, nom, prix, detail) in zip(cols, OFFRES):
    with c:
        st.markdown(
            f'<div class="cd-card"><span class="cd-badge">{nom}</span>'
            f'<p style="font-family:Fraunces,serif; font-size:1.2rem; margin:0.4rem 0;">{prix}</p>'
            f'<p style="font-size:0.85rem; color:rgba(30,42,36,0.65);">{detail}</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("Choisir cette offre", key=f"choose-{plan}", use_container_width=True):
            st.session_state["selected_plan"] = plan

st.markdown("---")
settings = get_settings()

st.markdown("## Espaces de paiement")
st.caption("Choisissez le mode de paiement adapté à votre situation.")

p1, p2 = st.columns(2)
with p1:
    st.markdown("#### Paiement local (Mobile Money)")
    st.markdown(
        f'<div class="cd-card" style="border-style:dashed; border-color:#B4622B; background:rgba(180,98,43,0.05);">'
        f'<b>MTN Mobile Money</b><br>📱 {settings["momo_numbers"]}<br><br>'
        f'<b>Orange Money</b><br>📱 {settings["om_numbers"]}</div>',
        unsafe_allow_html=True,
    )
with p2:
    st.markdown("#### Carte internationale")
    st.markdown(
        f'<div class="cd-card" style="border-style:dashed; border-color:#4C7A8C; background:rgba(76,122,140,0.05); font-size:0.9rem;">'
        f'{settings["intl_card_text"]}</div>', unsafe_allow_html=True,
    )
    st.markdown("#### Dépôt bancaire")
    st.markdown(
        f'<div class="cd-card" style="border-style:dashed; border-color:#2F5D50; background:rgba(47,93,80,0.05); font-size:0.9rem;">'
        f'{settings["bank_deposit_text"]}</div>', unsafe_allow_html=True,
    )
    st.page_link("pages/4_✉️_Support.py", label=f"✉️ Contacter l'administration ({settings['support_email']})")

st.markdown(
    '<div class="cd-card" style="display:flex; justify-content:space-between; align-items:center;">'
    'Besoin d\'aide pour choisir ou payer votre offre ?</div>', unsafe_allow_html=True,
)
st.page_link("pages/4_✉️_Support.py", label="Écrire au support →")

plan = st.session_state.get("selected_plan")
if plan:
    st.markdown("---")
    st.subheader(f"Confirmer la demande — {plan}")
    user = auth.current_user()
    if not user:
        st.warning("Connectez-vous pour envoyer une demande d'abonnement.")
        st.page_link("pages/5_🔐_Connexion.py", label="Se connecter →")
    else:
        payment_ref = st.text_input("Référence de paiement (Mobile Money / banque)", placeholder="Ex : MTN-2026-XXXXXX")
        if st.button("Envoyer ma demande"):
            amount = PLAN_PRICES_FCFA[plan]
            expires = (datetime.utcnow() + timedelta(days=30)).isoformat() if plan == "PREMIUM" else None
            conn = get_conn()
            conn.execute(
                "INSERT INTO subscriptions(id,user_id,plan,status,started_at,expires_at,amount_fcfa,payment_ref) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (new_id(), user["id"], plan, "PENDING", datetime.utcnow().isoformat(), expires, amount, payment_ref or None),
            )
            conn.commit()
            conn.close()
            st.success("Demande enregistrée. Un administrateur validera votre paiement et activera l'accès.")
            st.session_state["selected_plan"] = None

footer()
