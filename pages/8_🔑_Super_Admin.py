import streamlit as st

from common import init_page, footer
import auth

init_page("Accès Super Admin", icon="🔑")

_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.markdown('<div class="cd-card">', unsafe_allow_html=True)
    st.markdown("### 🔑 Accès Super Administrateur")
    st.caption(
        "Réservé au Super Admin de Café_digit. Saisissez le code d'accès unique — aucun mot de "
        "passe classique n'est requis."
    )

    if auth.is_super_admin():
        st.success("Vous êtes déjà connecté(e) en tant que Super Administrateur.")
        st.page_link("pages/9_🛠️_Administration.py", label="Aller à l'administration →")
    else:
        with st.form("superadmin_form"):
            code = st.text_input("Code d'accès Super Admin", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

        if submitted:
            user, error = auth.super_admin_login(code)
            if error:
                st.error(error)
            else:
                st.session_state["user"] = user
                st.success("Accès Super Admin confirmé.")
                st.switch_page("pages/9_🛠️_Administration.py")
    st.markdown("</div>", unsafe_allow_html=True)

footer()
