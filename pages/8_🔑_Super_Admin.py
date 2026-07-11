import streamlit as st

from common import init_page, footer
from i18n import t
import auth

init_page(t("Accès Super Admin", "Super Admin access"), icon="🔑")

_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.markdown('<div class="cd-card">', unsafe_allow_html=True)
    st.markdown(f"### 🔑 {t('Accès Super Administrateur', 'Super Administrator access')}")
    st.caption(t(
        "Réservé au Super Admin de Café_digit. Saisissez le code d'accès unique — aucun mot de "
        "passe classique n'est requis.",
        "Reserved for the Café_digit Super Admin. Enter the unique access code — no standard "
        "password is required.",
    ))

    if auth.is_super_admin():
        st.success(t(
            "Vous êtes déjà connecté(e) en tant que Super Administrateur.",
            "You're already logged in as Super Administrator.",
        ))
        st.page_link("pages/9_🛠️_Administration.py", label=t("Aller à l'administration →", "Go to administration →"))
    else:
        with st.form("superadmin_form"):
            code = st.text_input(t("Code d'accès Super Admin", "Super Admin access code"), type="password")
            submitted = st.form_submit_button(t("Se connecter", "Log in"), use_container_width=True)

        if submitted:
            user, error = auth.super_admin_login(code)
            if error:
                st.error(error)
            else:
                st.session_state["user"] = user
                st.success(t("Accès Super Admin confirmé.", "Super Admin access confirmed."))
                st.switch_page("pages/9_🛠️_Administration.py")
    st.markdown("</div>", unsafe_allow_html=True)

footer()
