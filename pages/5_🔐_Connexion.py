import streamlit as st

from common import init_page, footer
from i18n import t
import auth

init_page(t("Connexion", "Log in"), icon="🔐")

_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.title(t("Bon retour au Café_digit", "Welcome back to Café_digit"))
    st.caption(t(
        "Connectez-vous pour retrouver vos cours et votre progression.",
        "Log in to find your courses and your progress again.",
    ))

    if auth.current_user():
        st.success(t(
            f"Vous êtes déjà connecté(e) en tant que {auth.current_user()['fullName']}.",
            f"You're already logged in as {auth.current_user()['fullName']}.",
        ))
        st.page_link("pages/7_🎓_Mon_espace.py", label=t("Aller à mon espace →", "Go to my space →"))
    else:
        with st.form("login_form"):
            email = st.text_input(t("Email", "Email"))
            password = st.text_input(t("Mot de passe", "Password"), type="password")
            submitted = st.form_submit_button(t("Se connecter", "Log in"), use_container_width=True)

        if submitted:
            user, error = auth.login_user(email, password)
            if error:
                st.error(error)
            else:
                st.session_state["user"] = user
                st.success(t(f"Bienvenue, {user['fullName']} !", f"Welcome, {user['fullName']}!"))
                if user["role"] in ("ADMIN", "SUPER_ADMIN"):
                    st.switch_page("pages/9_🛠️_Administration.py")
                else:
                    st.switch_page("pages/7_🎓_Mon_espace.py")

        st.caption(t("Pas encore de compte ?", "Don't have an account yet?"))
        st.page_link("pages/6_🆕_Inscription.py", label=t("Rejoindre la communauté →", "Join the community →"))

footer()
