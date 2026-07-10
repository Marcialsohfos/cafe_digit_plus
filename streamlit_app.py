import streamlit as st
from common import init_page, footer

init_page("Accueil")

st.markdown(
    """
<div class="cd-hero">
  <span class="cd-badge" style="background: rgba(246,239,228,0.15); color:#F6EFE4;">
    Yaoundé · Bafoussam · Visioconférence
  </span>
  <h1 style="font-size:2.4rem; margin-top:0.8rem;">De la description à la prédiction, une tasse à la fois.</h1>
  <p style="max-width:640px; color:rgba(246,239,228,0.85); font-size:1.05rem;">
    Café_digit forme librement aux modèles mathématiques, à l'IA et aux Big Data, avec des cas
    réels du territoire : quartiers, épidémies, équipements. Un dispositif porté par
    SCSM Sarl — Lab_Math.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 1])
with col1:
    st.page_link("pages/1_📚_Cours.py", label="📚  Explorer les cours", use_container_width=True)
with col2:
    st.page_link("pages/2_🧪_Sandbox_R.py", label="🧪  Essayer la sandbox R →", use_container_width=True)

st.markdown("")
with st.expander("demo.R — Indice de Pression d'Équipement", expanded=False):
    st.markdown(
        """<div class="cd-mono">K &lt;- 10000; r &lt;- 0.3; N0 &lt;- 100
t &lt;- 0:50
N &lt;- K / (1 + ((K - N0)/N0) * exp(-r*t))
plot(t, N, type = "l", col = "darkgreen",
     main = "Métabolisme des Quartiers Hors-Piste")</div>""",
        unsafe_allow_html=True,
    )
    st.caption("Projet vitrine — prédire le point de bascule des quartiers informels avant qu'il ne survienne.")

st.markdown("## Quatre piliers de contenu")
piliers = [
    ("Modélisation mathématique", "Traduire un phénomène du terrain — santé, urbanisme, démographie — en équations simulables."),
    ("Intelligence artificielle", "Des fondamentaux jusqu'aux applications concrètes de l'IA supervisée."),
    ("Big Data", "Collecte, traitement, analyse et visualisation de données de terrain."),
    ("Cas pratiques", "Prédiction d'expansion urbaine, anticipation épidémiologique, indices de pression d'équipement."),
]
cols = st.columns(4)
for c, (titre, texte) in zip(cols, piliers):
    with c:
        st.markdown(f'<div class="cd-card"><h3 style="margin-top:0;">{titre}</h3><p style="color:rgba(30,42,36,0.7); font-size:0.9rem;">{texte}</p></div>', unsafe_allow_html=True)

st.markdown("## Un modèle hybride, pensé pour durer")
st.caption("La gratuité alimente la communauté ; la valeur ajoutée pédagogique et professionnelle se monétise, sans jamais fermer la porte d'entrée.")
paliers = [
    ("Communauté", "Gratuit", "Sessions découverte, contenus courts, communauté ouverte."),
    ("Module certifiant", "40 000 – 80 000 FCFA", "Cycle de 4 à 6 semaines, certificat Lab_Math."),
    ("Premium", "15 000 FCFA / mois", "Replays illimités, ateliers en direct, mentorat de groupe."),
    ("Missions B2B", "Sur devis", "Formations sur mesure pour entreprises, ONG et collectivités."),
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
st.page_link("pages/3_💳_Abonnement.py", label="Voir les offres en détail →")

st.markdown("## Projet vitrine")
st.markdown(
    '<div class="cd-card" style="border-color: rgba(47,93,80,0.3); background: rgba(47,93,80,0.05);">'
    '<span class="cd-badge" style="background: rgba(47,93,80,0.12); color:#2F5D50;">Projet vitrine</span>'
    '<h3>Métabolisme des Quartiers Hors-Piste</h3>'
    '<p style="color:rgba(30,42,36,0.7);">Un Indice de Pression d\'Équipement combinant automates cellulaires '
    'et IA supervisée pour prédire le point de bascule des quartiers informels avant qu\'il ne survienne — '
    'démonstrateur pédagogique et outil d\'aide à la décision pour les partenaires institutionnels.</p></div>',
    unsafe_allow_html=True,
)

footer()
