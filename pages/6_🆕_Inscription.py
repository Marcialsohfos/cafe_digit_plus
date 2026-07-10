import streamlit as st

from common import init_page, footer
import auth

init_page("Inscription", icon="🆕")

_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.title("Rejoindre la communauté")
    st.caption("L'accès à la communauté et aux sessions découverte est gratuit.")

    if auth.current_user():
        st.info(f"Vous êtes déjà connecté(e) en tant que {auth.current_user()['fullName']}.")
        st.page_link("pages/7_🎓_Mon_espace.py", label="Aller à mon espace →")
    else:
        with st.form("register_form"):
            full_name = st.text_input("Nom complet *")
            email = st.text_input("Email *")
            password = st.text_input("Mot de passe (8 caractères min.) *", type="password")
            c1, c2 = st.columns(2)
            city = c1.text_input("Ville", placeholder="Yaoundé, Bafoussam…")
            organization = c2.text_input("Institution")
            submitted = st.form_submit_button("Créer mon compte gratuit", use_container_width=True)

        if submitted:
            user, error = auth.register_user(email, password, full_name, city, organization)
            if error:
                st.error(error)
            else:
                st.session_state["user"] = user
                st.success("Compte créé avec succès. Bienvenue au Café_digit !")
                st.switch_page("pages/7_🎓_Mon_espace.py")

        st.caption("Déjà membre ?")
        st.page_link("pages/5_🔐_Connexion.py", label="Se connecter →")

footer()
