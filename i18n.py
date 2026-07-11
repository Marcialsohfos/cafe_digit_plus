"""
Café_digit — internationalisation légère (FR / EN).

Usage dans une page :
    from i18n import t
    st.write(t("Bonjour", "Hello"))

`t(fr, en)` retourne simplement le texte correspondant à la langue active,
stockée dans `st.session_state["lang"]` ("fr" par défaut). Le sélecteur de
langue (`language_switcher`) est appelé une seule fois, dans la barre
latérale commune (`common.render_sidebar`), et s'applique donc à toutes
les pages de l'application.
"""
import streamlit as st

DEFAULT_LANG = "fr"


def get_lang() -> str:
    return st.session_state.get("lang", DEFAULT_LANG)


def set_lang(lang: str) -> None:
    st.session_state["lang"] = lang


def t(fr: str, en: str) -> str:
    """Retourne le texte dans la langue actuellement sélectionnée."""
    return en if get_lang() == "en" else fr


def language_switcher(location=st.sidebar) -> None:
    """Affiche le sélecteur 🇫🇷 / 🇬🇧 et déclenche un rerun si on change de langue."""
    current = get_lang()
    choice = location.radio(
        "Langue / Language",
        options=["fr", "en"],
        index=0 if current == "fr" else 1,
        format_func=lambda x: "🇫🇷 Français" if x == "fr" else "🇬🇧 English",
        horizontal=True,
        key="lang_switcher_widget",
        label_visibility="collapsed",
    )
    if choice != current:
        set_lang(choice)
        st.rerun()
