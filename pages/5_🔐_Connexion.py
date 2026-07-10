import streamlit as st

from common import init_page, footer
import auth

init_page("Connexion", icon="🔐")

_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.title("Bon retour au Café_digit")
    st.caption("Connectez-vous pour retrouver vos cours et votre progression.")

    if auth.current_user():
        st.success(f"Vous êtes déjà connecté(e) en tant que {auth.current_user()['fullName']}.")
        st.page_link("pages/7_🎓_Mon_espace.py", label="Aller à mon espace →")
    else:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

        if submitted:
            user, error = auth.login_user(email, password)
            if error:
                st.error(error)
            else:
                st.session_state["user"] = user
                st.success(f"Bienvenue, {user['fullName']} !")
                if user["role"] in ("ADMIN", "SUPER_ADMIN"):
                    st.switch_page("pages/9_🛠️_Administration.py")
                else:
                    st.switch_page("pages/7_🎓_Mon_espace.py")

        st.caption("Pas encore de compte ?")
        st.page_link("pages/6_🆕_Inscription.py", label="Rejoindre la communauté →")

footer()
