# Guide de déploiement AgriVision AI sur PythonAnywhere

## Étape 1 — Créer un compte PythonAnywhere
- Aller sur https://www.pythonanywhere.com
- Cliquer "Start running Python online in less than a minute"
- Choisir le plan **Beginner (gratuit)**
- Créer un compte (email + mot de passe)

## Étape 2 — Ouvrir une console Bash
- Dans le dashboard, cliquer "Bash" dans la section "New console"

## Étape 3 — Uploader les fichiers
Dans la console Bash, taper :

```bash
mkdir agrivision
cd agrivision
```

Puis dans l'onglet "Files" de PythonAnywhere :
- Naviguer vers /home/VOTRE_USERNAME/agrivision/
- Uploader : app.py et requirements.txt

## Étape 4 — Installer les dépendances
Dans la console Bash :

```bash
cd ~/agrivision
pip3.10 install streamlit pandas plotly --user
```

## Étape 5 — Lancer Streamlit
```bash
streamlit run app.py --server.port 8501 --server.headless true &
```

## Étape 6 — Configurer le Web App (proxy)
⚠️ PythonAnywhere gratuit ne supporte pas Streamlit directement.
Il faut utiliser un tunnel ou passer à une autre plateforme.

## Alternative recommandée : Streamlit Community Cloud (100% gratuit)

### Déploiement en 3 minutes :

1. Créer un repo GitHub avec les fichiers app.py et requirements.txt
2. Aller sur https://share.streamlit.io
3. Se connecter avec GitHub
4. Cliquer "New app" → sélectionner votre repo → sélectionner app.py
5. Cliquer "Deploy"

→ URL générée : https://VOTRE_NOM-agrivision.streamlit.app

### Commandes Git pour uploader le projet :
```bash
git init
git add app.py requirements.txt
git commit -m "AgriVision AI - première version"
git remote add origin https://github.com/VOTRE_USERNAME/agrivision.git
git push -u origin main
```

## Test en local (sur votre machine)
```bash
pip install streamlit pandas plotly
streamlit run app.py
```
→ S'ouvre automatiquement sur http://localhost:8501
