import streamlit as st
from common import init_page, footer
from i18n import t

init_page(t("Accueil", "Home"))

st.markdown(
    f"""
<div class="cd-hero">
  <span class="cd-badge" style="background: rgba(246,239,228,0.15); color:#F6EFE4;">
    {t("Yaoundé · Bafoussam · Visioconférence", "Yaoundé · Bafoussam · Video conference")}
  </span>
  <h1 style="font-size:2.4rem; margin-top:0.8rem;">{t(
      "De la description à la prédiction, une tasse à la fois.",
      "From description to prediction, one cup at a time.",
  )}</h1>
  <p style="max-width:640px; color:rgba(246,239,228,0.85); font-size:1.05rem;">
    {t(
        "Café_digit forme librement aux modèles mathématiques, à l'IA et aux Big Data, avec des cas "
        "réels du territoire : quartiers, épidémies, équipements. Un dispositif porté par "
        "SCSM Sarl — Lab_Math.",
        "Café_digit offers free training in mathematical modeling, AI and Big Data, using real-world "
        "local cases: neighborhoods, epidemics, infrastructure. An initiative led by "
        "SCSM Sarl — Lab_Math.",
    )}
  </p>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 1])
with col1:
    st.page_link("pages/1_📚_Cours.py", label=t("📚  Explorer les cours", "📚  Explore the courses"), use_container_width=True)
with col2:
    st.page_link("pages/2_🧪_Sandbox_R.py", label=t("🧪  Essayer la sandbox R →", "🧪  Try the R sandbox →"), use_container_width=True)

st.markdown("")
with st.expander(t("demo.R — Indice de Pression d'Équipement", "demo.R — Infrastructure Pressure Index"), expanded=False):
    st.markdown(
        """<div class="cd-mono">K &lt;- 10000; r &lt;- 0.3; N0 &lt;- 100
t &lt;- 0:50
N &lt;- K / (1 + ((K - N0)/N0) * exp(-r*t))
plot(t, N, type = "l", col = "darkgreen",
     main = "Métabolisme des Quartiers Hors-Piste")</div>""",
        unsafe_allow_html=True,
    )
    st.caption(t(
        "Projet vitrine — prédire le point de bascule des quartiers informels avant qu'il ne survienne.",
        "Flagship project — predicting the tipping point of informal neighborhoods before it happens.",
    ))

st.markdown(f"## {t('Quatre piliers de contenu', 'Four content pillars')}")
piliers = [
    (
        t("Modélisation mathématique", "Mathematical modeling"),
        t(
            "Traduire un phénomène du terrain — santé, urbanisme, démographie — en équations simulables.",
            "Translating a real-world phenomenon — health, urban planning, demographics — into simulable equations.",
        ),
    ),
    (
        t("Intelligence artificielle", "Artificial intelligence"),
        t(
            "Des fondamentaux jusqu'aux applications concrètes de l'IA supervisée.",
            "From the fundamentals to concrete applications of supervised AI.",
        ),
    ),
    (
        t("Big Data", "Big Data"),
        t(
            "Collecte, traitement, analyse et visualisation de données de terrain.",
            "Collection, processing, analysis and visualization of field data.",
        ),
    ),
    (
        t("Cas pratiques", "Case studies"),
        t(
            "Prédiction d'expansion urbaine, anticipation épidémiologique, indices de pression d'équipement.",
            "Urban expansion prediction, epidemiological forecasting, infrastructure pressure indices.",
        ),
    ),
]
cols = st.columns(4)
for c, (titre, texte) in zip(cols, piliers):
    with c:
        st.markdown(f'<div class="cd-card"><h3 style="margin-top:0;">{titre}</h3><p style="color:rgba(30,42,36,0.7); font-size:0.9rem;">{texte}</p></div>', unsafe_allow_html=True)

st.markdown(f"## {t('Un modèle hybride, pensé pour durer', 'A hybrid model, built to last')}")
st.caption(t(
    "La gratuité alimente la communauté ; la valeur ajoutée pédagogique et professionnelle se monétise, "
    "sans jamais fermer la porte d'entrée.",
    "Free access grows the community; the pedagogical and professional value-add is monetized, "
    "without ever closing the front door.",
))
paliers = [
    (
        t("Communauté", "Community"), t("Gratuit", "Free"),
        t("Sessions découverte, contenus courts, communauté ouverte.", "Discovery sessions, short content, open community."),
    ),
    (
        t("Module certifiant", "Certifying module"), t("40 000 – 80 000 FCFA", "40,000 – 80,000 FCFA"),
        t("Cycle de 4 à 6 semaines, certificat Lab_Math.", "4- to 6-week cycle, Lab_Math certificate."),
    ),
    (
        t("Premium", "Premium"), t("15 000 FCFA / mois", "15,000 FCFA / month"),
        t("Replays illimités, ateliers en direct, mentorat de groupe.", "Unlimited replays, live workshops, group mentoring."),
    ),
    (
        t("Missions B2B", "B2B engagements"), t("Sur devis", "Custom quote"),
        t(
            "Formations sur mesure pour entreprises, ONG et collectivités.",
            "Tailor-made training for companies, NGOs and local authorities.",
        ),
    ),
]
cols = st.columns(4)
for c, (nom, prix, detail) in zip(cols, paliers):
    with c:
        st.markdown(
            f'<div class="cd-card" style="background:#2A1B12; color:#F6EFE4; border:1px solid rgba(246,239,228,0.15);">'
            f'<p style="text-transform:uppercase; font-size:0.75rem; letter-spacing:0.05em; color:#E08A3E; font-weight:600;">{nom}</p>'
            f'<p style="font-family:Fraunces,serif; font-size:1.2rem; color:#FFFDF9;">{prix}</p>'
            f'<p style="font-size:0.85rem; color:rgba(246,239,228,0.7);">{detail}</p></div>',
            unsafe_allow_html=True,
        )
st.page_link("pages/3_💳_Abonnement.py", label=t("Voir les offres en détail →", "See offer details →"))

st.markdown(f"## {t('Projet vitrine', 'Flagship project')}")
st.markdown(
    f'<div class="cd-card" style="border-color: rgba(47,93,80,0.3); background: rgba(47,93,80,0.05);">'
    f'<span class="cd-badge" style="background: rgba(47,93,80,0.12); color:#2F5D50;">{t("Projet vitrine", "Flagship project")}</span>'
    f'<h3>{t("Métabolisme des Quartiers Hors-Piste", "Off-Grid Neighborhoods Metabolism")}</h3>'
    f'<p style="color:rgba(30,42,36,0.7);">{t(
        "Un Indice de Pression d\'Équipement combinant automates cellulaires "
        "et IA supervisée pour prédire le point de bascule des quartiers informels avant qu\'il ne survienne — "
        "démonstrateur pédagogique et outil d\'aide à la décision pour les partenaires institutionnels.",
        "An Infrastructure Pressure Index combining cellular automata "
        "and supervised AI to predict the tipping point of informal neighborhoods before it happens — "
        "a teaching demonstrator and decision-support tool for institutional partners.",
    )}</p></div>',
    unsafe_allow_html=True,
)

footer()
