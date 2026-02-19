# Recherche Pro - Anti-Flemme Edition

Application Streamlit légère et fun pour aider les élèves (5e à Terminale) à structurer une recherche documentaire sérieuse sans copier-coller sauvage.

## Fonctionnalités

- Sujet + profil élève (nom/prénom, classe)
- Génération automatique de questions de recherche guidées
- Génération de mots-clés FR + EN
- Sources fiables recommandées avec liens cliquables
- Ajout de sources personnelles (avec extrait optionnel)
- Prise de notes structurée par onglets avec compteur de mots
- Alerte anti copier-coller (heuristique)
- Checklist anti-fake news avec score de fiabilité (1-5)
- Export PDF complet du dossier
- Mode clair/sombre
- Timer en sidebar + tips méthodo
- Bonus image illustrative facultative

## Lancement local

1. Créer un environnement virtuel (optionnel mais recommandé)

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\\Scripts\\activate  # Windows
```

2. Installer les dépendances

```bash
pip install -r requirements.txt
```

3. Lancer l'application

```bash
streamlit run app.py
```

## Déploiement gratuit

## 1) Streamlit Community Cloud

1. Pousser le repo sur GitHub.
2. Aller sur [share.streamlit.io](https://share.streamlit.io).
3. Connecter le repo.
4. Définir le fichier principal: `app.py`.
5. Déployer.

## 2) Hugging Face Spaces

1. Créer un Space de type **Streamlit**.
2. Ajouter `app.py` et `requirements.txt`.
3. Commit/push via l'interface ou git.
4. Le Space se build automatiquement.

## 3) Render (Web Service)

1. Créer un nouveau **Web Service** relié au repo.
2. Build command:

```bash
pip install -r requirements.txt
```

3. Start command:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## Offline-friendly

- L'app fonctionne sans API payante.
- Les liens de sources s'ouvrent seulement si internet est dispo.
- La partie image illustrative est facultative.

## Personnalisation rapide

- Nom de l'app: constante `APP_NAME` dans `app.py`.
- Couleurs: fonction `apply_theme()`.
- Messages: sections `st.success`, `st.warning`, etc.

