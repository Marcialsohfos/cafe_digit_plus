# ☕ Café_digit — édition Streamlit

Plateforme de formation Café_digit (SCSM Sarl · Lab_Math), entièrement réécrite
pour être déployée en un clic sur **Streamlit Community Cloud** (streamlit.io).
Le style visuel d'origine (palette « espresso / clay / ember / parchment »,
typographies Fraunces + Inter) est conservé.

## Fonctionnalités

- **Catalogue de cours** avec modules, leçons (texte, vidéo, PDF, sandbox R),
  exercices, travaux pratiques et quiz notés automatiquement.
- **Sandbox R** pédagogique (simulation Python équivalente, sans installation).
- **Espace membre** : inscription, connexion, suivi de progression, historique
  des quiz, gestion des offres.
- **Offres & paiement** (Mobile Money, Orange Money, carte internationale,
  dépôt bancaire) avec demande d'activation validée par un administrateur.
- **Espace Support** : tout membre peut écrire directement à
  **support@scsmaubmar.org** pour une demande de paiement, une doléance ou
  une requête générale. Le message est stocké et visible par l'administration,
  et envoyé par e-mail si un serveur SMTP est configuré (voir plus bas).
- **Super Admin** : connexion par code d'accès unique
  (`labscsm32015@10001b` par défaut, modifiable), qui peut ensuite créer et
  révoquer des comptes **Administrateur**.
- **Administrateurs** : déposent des cours, modules, leçons, exercices,
  travaux pratiques et quiz ; valident les inscriptions/paiements ; gèrent les
  messages du support et les paramètres publics du site.

## Démarrage local

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

L'application crée automatiquement un fichier `cafedigit.db` (SQLite) au
premier lancement, avec un cours de démonstration déjà publié.

## Déploiement sur Streamlit Community Cloud

1. Poussez ce dossier dans un dépôt GitHub (public ou privé).
2. Rendez-vous sur **share.streamlit.io**, connectez votre compte GitHub et
   cliquez sur **"New app"**.
3. Sélectionnez le dépôt, la branche, puis indiquez `streamlit_app.py` comme
   fichier principal.
4. (Optionnel mais recommandé) Dans **Settings → Secrets**, collez le contenu
   de `.streamlit/secrets.toml.example` en adaptant vos vraies valeurs
   (code Super Admin, identifiants SMTP) — voir ci-dessous.
5. Cliquez sur **Deploy**. L'application est en ligne en quelques minutes.

> ⚠️ Le stockage `cafedigit.db` est local au conteneur Streamlit Cloud : il
> persiste tant que l'application n'est pas redéployée à neuf ou remise en
> veille prolongée. Pour une plateforme en production avec de gros volumes,
> pensez à migrer vers une base externe (Postgres/Supabase) — la couche
> `db.py` est isolée pour faciliter cette évolution plus tard.

## Configuration du courrier vers support@scsmaubmar.org

Par défaut, les messages du formulaire "Support & doléances" sont toujours
**enregistrés** et visibles par les administrateurs dans l'onglet
**Administration → ✉️ Support**, même sans configuration e-mail.

Pour un envoi *réel* et automatique vers `support@scsmaubmar.org`, ajoutez
une section `[smtp]` dans vos secrets Streamlit (voir
`.streamlit/secrets.toml.example`) avec les identifiants d'un compte e-mail
autorisé à envoyer (Gmail avec mot de passe d'application, ou tout autre
fournisseur SMTP).

## Code d'accès Super Admin

Le code par défaut est `labscsm32015@10001b`. Vous pouvez le remplacer en
définissant `SUPER_ADMIN_CODE` dans vos secrets Streamlit, sans toucher au
code source. Le Super Admin se connecte depuis la page **🔑 Accès Super
Admin** du menu latéral (aucun mot de passe classique n'est requis).

## Structure du projet

```
streamlit_app.py        Page d'accueil (contenu de la landing page d'origine)
common.py                Style visuel + barre latérale partagée
db.py                    Schéma SQLite + amorçage des données de démo
auth.py                  Authentification (mots de passe, sessions, Super Admin)
mailer.py                Envoi des messages de support par e-mail (SMTP optionnel)
pages/
  1_📚_Cours.py           Catalogue + détail de cours + leçons
  2_🧪_Sandbox_R.py       Bac à sable R (simulation Python)
  3_💳_Abonnement.py      Offres et informations de paiement
  4_✉️_Support.py         Formulaire vers support@scsmaubmar.org
  5_🔐_Connexion.py       Connexion membre
  6_🆕_Inscription.py     Inscription membre (gratuite)
  7_🎓_Mon_espace.py      Tableau de bord personnel
  8_🔑_Super_Admin.py     Connexion Super Admin par code unique
  9_🛠️_Administration.py  Back-office (cours, quiz, utilisateurs, paiements,
                           support, paramètres, gestion des admins)
  10_📝_Quiz.py           Passage d'un quiz (ouvert depuis un cours)
```
