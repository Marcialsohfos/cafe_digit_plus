from datetime import datetime, timedelta

import streamlit as st

from common import init_page, footer
from db import get_conn, new_id, get_settings, PLAN_PRICES_FCFA
from i18n import t
import auth

init_page(t("Abonnement", "Subscription"), icon="💳")

st.title(t("Nos offres", "Our plans"))
st.write(
    t(
        "Le palier communautaire reste gratuit. Choisissez une offre payante pour débloquer les "
        "modules certifiants, le mentorat ou une mission sur mesure.",
        "The community tier stays free. Choose a paid plan to unlock certifying modules, "
        "mentoring or a custom engagement.",
    )
)

OFFRES = [
    (
        "PREMIUM", t("Premium mensuel", "Monthly Premium"), t("15 000 FCFA / mois", "15,000 FCFA / month"),
        t("Replays illimités, ateliers en direct, mentorat de groupe.", "Unlimited replays, live workshops, group mentoring."),
    ),
    (
        "MODULE", t("Module certifiant", "Certifying module"), t("≈ 60 000 FCFA", "≈ 60,000 FCFA"),
        t("Cycle de 4 à 6 semaines, certificat Lab_Math.", "4- to 6-week cycle, Lab_Math certificate."),
    ),
    (
        "B2B", t("Mission sur mesure", "Custom engagement"), t("Sur devis (500k – 2,5M FCFA)", "Custom quote (500k – 2.5M FCFA)"),
        t("Formation dédiée entreprise, ONG ou collectivité.", "Dedicated training for companies, NGOs or local authorities."),
    ),
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
        if st.button(t("Choisir cette offre", "Choose this plan"), key=f"choose-{plan}", use_container_width=True):
            st.session_state["selected_plan"] = plan

st.markdown("---")
settings = get_settings()

st.markdown(f"## {t('Espaces de paiement', 'Payment options')}")
st.caption(t("Choisissez le mode de paiement adapté à votre situation.", "Choose the payment method that suits your situation."))

p1, p2 = st.columns(2)
with p1:
    st.markdown(f"#### {t('Paiement local (Mobile Money)', 'Local payment (Mobile Money)')}")
    st.markdown(
        f'<div class="cd-card" style="border-style:dashed; border-color:#B4622B; background:rgba(180,98,43,0.05);">'
        f'<b>MTN Mobile Money</b><br>📱 {settings["momo_numbers"]}<br><br>'
        f'<b>Orange Money</b><br>📱 {settings["om_numbers"]}</div>',
        unsafe_allow_html=True,
    )
with p2:
    st.markdown(f"#### {t('Carte internationale', 'International card')}")
    st.markdown(
        f'<div class="cd-card" style="border-style:dashed; border-color:#4C7A8C; background:rgba(76,122,140,0.05); font-size:0.9rem;">'
        f'{settings["intl_card_text"]}</div>', unsafe_allow_html=True,
    )
    st.markdown(f"#### {t('Dépôt bancaire', 'Bank deposit')}")
    st.markdown(
        f'<div class="cd-card" style="border-style:dashed; border-color:#2F5D50; background:rgba(47,93,80,0.05); font-size:0.9rem;">'
        f'{settings["bank_deposit_text"]}</div>', unsafe_allow_html=True,
    )
    st.page_link(
        "pages/4_✉️_Support.py",
        label=t(f"✉️ Contacter l'administration ({settings['support_email']})", f"✉️ Contact the administration ({settings['support_email']})"),
    )

st.markdown(
    f'<div class="cd-card" style="display:flex; justify-content:space-between; align-items:center;">'
    f'{t("Besoin d\'aide pour choisir ou payer votre offre ?", "Need help choosing or paying for your plan?")}</div>',
    unsafe_allow_html=True,
)
st.page_link("pages/4_✉️_Support.py", label=t("Écrire au support →", "Contact support →"))

plan = st.session_state.get("selected_plan")
if plan:
    st.markdown("---")
    st.subheader(t(f"Confirmer la demande — {plan}", f"Confirm the request — {plan}"))
    user = auth.current_user()
    if not user:
        st.warning(t("Connectez-vous pour envoyer une demande d'abonnement.", "Log in to send a subscription request."))
        st.page_link("pages/5_🔐_Connexion.py", label=t("Se connecter →", "Log in →"))
    else:
        payment_ref = st.text_input(
            t("Référence de paiement (Mobile Money / banque)", "Payment reference (Mobile Money / bank)"),
            placeholder=t("Ex : MTN-2026-XXXXXX", "E.g.: MTN-2026-XXXXXX"),
        )
        if st.button(t("Envoyer ma demande", "Send my request")):
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
            st.success(t(
                "Demande enregistrée. Un administrateur validera votre paiement et activera l'accès.",
                "Request recorded. An administrator will validate your payment and activate access.",
            ))
            st.session_state["selected_plan"] = None

footer()
