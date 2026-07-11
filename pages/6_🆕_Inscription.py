import streamlit as st

from common import init_page, footer
from i18n import t
import auth

init_page(t("Inscription", "Sign up"), icon="🆕")

_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.title(t("Rejoindre la communauté", "Join the community"))
    st.caption(t(
        "L'accès à la communauté et aux sessions découverte est gratuit.",
        "Access to the community and discovery sessions is free.",
    ))

    if auth.current_user():
        st.info(t(
            f"Vous êtes déjà connecté(e) en tant que {auth.current_user()['fullName']}.",
            f"You're already logged in as {auth.current_user()['fullName']}.",
        ))
        st.page_link("pages/7_🎓_Mon_espace.py", label=t("Aller à mon espace →", "Go to my space →"))
    else:
        with st.form("register_form"):
            full_name = st.text_input(t("Nom complet *", "Full name *"))
            email = st.text_input(t("Email *", "Email *"))
            password = st.text_input(t("Mot de passe (8 caractères min.) *", "Password (min. 8 characters) *"), type="password")
            c1, c2 = st.columns(2)
            city = c1.text_input(t("Ville", "City"), placeholder=t("Yaoundé, Bafoussam…", "Yaoundé, Bafoussam…"))
            organization = c2.text_input(t("Institution", "Organization"))
            submitted = st.form_submit_button(t("Créer mon compte gratuit", "Create my free account"), use_container_width=True)

        if submitted:
            user, error = auth.register_user(email, password, full_name, city, organization)
            if error:
                st.error(error)
            else:
                st.session_state["user"] = user
                st.success(t("Compte créé avec succès. Bienvenue au Café_digit !", "Account created successfully. Welcome to Café_digit!"))
                st.switch_page("pages/7_🎓_Mon_espace.py")

        st.caption(t("Déjà membre ?", "Already a member?"))
        st.page_link("pages/5_🔐_Connexion.py", label=t("Se connecter →", "Log in →"))

footer()
