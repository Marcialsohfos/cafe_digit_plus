import streamlit as st
import streamlit.components.v1 as components

from common import init_page, footer
from db import (
    add_chat_message, get_channel_messages, get_direct_messages,
    search_members, get_recent_dm_partners,
)
from i18n import t
import auth

init_page(t("Café Chat", "Café Chat"), icon="💬")

user = auth.current_user()
if not user:
    st.warning(t("Connectez-vous pour accéder au Café Chat.", "Log in to access Café Chat."))
    st.page_link("pages/5_🔐_Connexion.py", label=t("Se connecter →", "Log in →"))
    st.stop()

st.title(t("💬 Café Chat", "💬 Café Chat"))
st.caption(t(
    "Le salon de discussion de la communauté Café_digit — échangez avec les autres membres, "
    "en salon général ou en message privé.",
    "Café_digit's community chat room — talk with other members, in the general channel or via direct message.",
))

top_c1, top_c2 = st.columns([3, 1])
with top_c1:
    if st.button(t("🔄 Actualiser maintenant", "🔄 Refresh now"), key="chat_manual_refresh"):
        st.rerun()
with top_c2:
    auto_refresh = st.checkbox(
        t("Auto (5 s)", "Auto (5s)"), value=st.session_state.get("chat_autorefresh", False),
        key="chat_autorefresh",
        help=t(
            "Recharge la page toutes les 5 secondes pour simuler des messages en temps réel.",
            "Reloads the page every 5 seconds to simulate real-time messages.",
        ),
    )

if auto_refresh:
    components.html(
        "<script>setTimeout(function(){ window.parent.location.reload(); }, 5000);</script>",
        height=0,
    )

tab_general, tab_dm = st.tabs([
    t("☕ Salon général", "☕ General channel"),
    t("✉️ Messages privés", "✉️ Direct messages"),
])

# ============================================================ Salon général
with tab_general:
    messages = get_channel_messages()
    chat_box = st.container(height=420)
    with chat_box:
        if not messages:
            st.caption(t(
                "Aucun message pour le moment — lancez la discussion !",
                "No messages yet — start the conversation!",
            ))
        for m in messages:
            is_me = m["sender_id"] == user["id"]
            is_staff = m["sender_role"] in ("ADMIN", "SUPER_ADMIN")
            avatar = "🧑‍🍳" if is_me else ("🛠️" if is_staff else "🧑‍🎓")
            label = t("Vous", "You") if is_me else m["sender_name"]
            with st.chat_message("user" if is_me else "assistant", avatar=avatar):
                st.markdown(f"**{label}**" + (" · 🛠️" if (is_staff and not is_me) else ""))
                st.write(m["body"])
                st.caption(m["created_at"][:16].replace("T", " "))

    general_input = st.chat_input(
        t("Écrire un message dans le salon général…", "Write a message in the general channel…"),
        key="general_chat_input",
    )
    if general_input:
        add_chat_message(user["id"], general_input, recipient_id=None)
        st.rerun()

# ============================================================ Messages privés
with tab_dm:
    dm_col1, dm_col2 = st.columns([1, 2])

    with dm_col1:
        st.markdown(f"###### {t('🔎 Rechercher un membre', '🔎 Search a member')}")
        query = st.text_input(
            t("Nom ou e-mail", "Name or email"), key="member_search",
            label_visibility="collapsed", placeholder=t("Nom ou e-mail…", "Name or email…"),
        )
        if query.strip():
            results = search_members(query, user["id"])
            if not results:
                st.caption(t("Aucun membre trouvé.", "No member found."))
            for r in results:
                r_badge = " 🛠️" if r["role"] in ("ADMIN", "SUPER_ADMIN") else ""
                if st.button(f"💬 {r['full_name']}{r_badge}", key=f"searchres-{r['id']}", use_container_width=True):
                    st.session_state["chat_partner_id"] = r["id"]
                    st.session_state["chat_partner_name"] = r["full_name"]
                    st.rerun()

        st.markdown(f"###### {t('Conversations récentes', 'Recent conversations')}")
        partners = get_recent_dm_partners(user["id"])
        if not partners:
            st.caption(t("Aucune conversation pour le moment.", "No conversation yet."))
        for p in partners:
            active = st.session_state.get("chat_partner_id") == p["id"]
            p_badge = " 🛠️" if p["role"] in ("ADMIN", "SUPER_ADMIN") else ""
            btn_label = f'{"▶ " if active else ""}{p["full_name"]}{p_badge}'
            if st.button(btn_label, key=f"partner-{p['id']}", use_container_width=True):
                st.session_state["chat_partner_id"] = p["id"]
                st.session_state["chat_partner_name"] = p["full_name"]
                st.rerun()

    partner_id = st.session_state.get("chat_partner_id")
    partner_name = st.session_state.get("chat_partner_name")

    with dm_col2:
        if not partner_id:
            st.info(t(
                "Recherchez un membre ou choisissez une conversation récente pour commencer à discuter.",
                "Search for a member or pick a recent conversation to start chatting.",
            ))
        else:
            st.markdown(f"###### {t('Conversation avec', 'Conversation with')} {partner_name}")
            dm_messages = get_direct_messages(user["id"], partner_id)
            dm_box = st.container(height=340)
            with dm_box:
                if not dm_messages:
                    st.caption(t("Aucun message échangé pour le moment.", "No messages exchanged yet."))
                for m in dm_messages:
                    is_me = m["sender_id"] == user["id"]
                    label = t("Vous", "You") if is_me else m["sender_name"]
                    with st.chat_message("user" if is_me else "assistant"):
                        st.markdown(f"**{label}**")
                        st.write(m["body"])
                        st.caption(m["created_at"][:16].replace("T", " "))

    # st.chat_input ne peut pas être imbriqué dans st.columns : on le place au
    # niveau de l'onglet, conditionné à la sélection d'un interlocuteur.
    if partner_id:
        dm_input = st.chat_input(
            t("Écrire un message privé…", "Write a private message…"), key="dm_chat_input",
        )
        if dm_input:
            add_chat_message(user["id"], dm_input, recipient_id=partner_id)
            st.rerun()

footer()
