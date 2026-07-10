"""
Café_digit — utilitaires partagés par toutes les pages Streamlit :
initialisation de la base, injection du style visuel d'origine (palette
« espresso / clay / ember / parchment », typographies Fraunces + Inter),
et barre latérale d'authentification commune.
"""
import streamlit as st

from db import init_db, get_settings
import auth

PALETTE = {
    "espresso": "#2A1B12",
    "roast": "#5C3A21",
    "clay": "#B4622B",
    "ember": "#E08A3E",
    "parchment": "#F6EFE4",
    "chalk": "#FFFDF9",
    "ink": "#1E2A24",
    "moss": "#2F5D50",
    "sky": "#4C7A8C",
}

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}
h1, h2, h3, .display-font {{
    font-family: 'Fraunces', serif !important;
    color: {PALETTE['espresso']};
}}
[data-testid="stAppViewContainer"] {{
    background-color: {PALETTE['parchment']};
}}
[data-testid="stSidebar"] {{
    background-color: {PALETTE['espresso']};
}}
[data-testid="stSidebar"] * {{
    color: {PALETTE['parchment']} !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(246,239,228,0.2);
}}
.cd-card {{
    background-color: {PALETTE['chalk']};
    border: 1px solid rgba(42,27,18,0.1);
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 1px 3px rgba(42,27,18,0.06);
    margin-bottom: 1rem;
}}
.cd-badge {{
    display: inline-block;
    border-radius: 999px;
    padding: 0.15rem 0.9rem;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: rgba(180,98,43,0.12);
    color: {PALETTE['clay']};
}}
.cd-pill {{
    display: inline-block;
    border-radius: 999px;
    padding: 0.3rem 1rem;
    font-size: 0.85rem;
    background: rgba(42,27,18,0.06);
    color: {PALETTE['ink']};
}}
.cd-hero {{
    background: {PALETTE['espresso']};
    color: {PALETTE['parchment']};
    border-radius: 24px;
    padding: 2.4rem 2.2rem;
    margin-bottom: 1.5rem;
}}
.cd-hero h1 {{ color: {PALETTE['chalk']} !important; }}
.cd-mono {{
    font-family: 'JetBrains Mono', monospace;
    background: {PALETTE['espresso']};
    color: {PALETTE['parchment']};
    border-radius: 12px;
    padding: 1rem;
    font-size: 0.8rem;
    white-space: pre-wrap;
}}
div.stButton > button, div.stDownloadButton > button {{
    background-color: {PALETTE['espresso']};
    color: {PALETTE['chalk']};
    border-radius: 999px;
    border: none;
    padding: 0.5rem 1.4rem;
    font-weight: 600;
}}
div.stButton > button:hover {{
    background-color: {PALETTE['clay']};
    color: {PALETTE['chalk']};
}}
.cd-footer {{
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(42,27,18,0.1);
    color: rgba(30,42,36,0.5);
    font-size: 0.8rem;
    text-align: center;
}}
</style>
"""


def init_page(title: str, icon: str = "☕", layout: str = "wide"):
    st.set_page_config(page_title=f"{title} · Café_digit", page_icon=icon, layout=layout)
    init_db()
    st.markdown(_CSS, unsafe_allow_html=True)
    render_sidebar()


def render_sidebar():
    with st.sidebar:
        st.markdown("### ☕ Café_digit")
        st.caption("SCSM Sarl — Lab_Math")
        st.markdown("---")
        user = auth.current_user()
        if user:
            role_label = {
                "STUDENT": "Membre",
                "ADMIN": "Administrateur",
                "SUPER_ADMIN": "Super Administrateur",
            }.get(user["role"], user["role"])
            st.success(f"**{user['fullName']}**\n\n{role_label}")
            if st.button("Se déconnecter", use_container_width=True):
                auth.logout()
                st.rerun()
        else:
            st.info("Vous n'êtes pas connecté(e).")
        st.markdown("---")
        st.caption("Navigation")
        st.page_link("streamlit_app.py", label="Accueil", icon="🏠")
        st.page_link("pages/1_📚_Cours.py", label="Cours", icon="📚")
        st.page_link("pages/2_🧪_Sandbox_R.py", label="Sandbox R", icon="🧪")
        st.page_link("pages/3_💳_Abonnement.py", label="Abonnement", icon="💳")
        st.page_link("pages/4_✉️_Support.py", label="Support & doléances", icon="✉️")
        if user:
            st.page_link("pages/7_🎓_Mon_espace.py", label="Mon espace", icon="🎓")
        else:
            st.page_link("pages/5_🔐_Connexion.py", label="Connexion", icon="🔐")
            st.page_link("pages/6_🆕_Inscription.py", label="Inscription", icon="🆕")
        if auth.is_admin():
            st.page_link("pages/9_🛠️_Administration.py", label="Administration", icon="🛠️")
        if not user:
            st.page_link("pages/8_🔑_Super_Admin.py", label="Accès Super Admin", icon="🔑")


def footer():
    st.markdown(
        '<div class="cd-footer">Café_digit — un dispositif porté par SCSM Sarl · Lab_Math · '
        'Yaoundé · Bafoussam · Visioconférence</div>',
        unsafe_allow_html=True,
    )
