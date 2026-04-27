# 🌱 AgriVision AI — Collecte & Analyse de Données Agricoles

> **Smart farming for Africa's future**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/Licence-MIT-green?style=flat)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-brightgreen?style=flat)]()

---

## 📌 Présentation

**AgriVision AI** est une plateforme web de collecte et d'analyse descriptive de données agricoles conçue pour les petits exploitants agricoles d'Afrique subsaharienne. Elle permet de saisir, stocker, visualiser et analyser des données terrain en temps réel, sans compétences techniques particulières.

Développée, cette plateforme couvre **15 pays africains** et **15 cultures principales**.

---

## 🎯 Fonctionnalités

| Module | Description |
|--------|-------------|
| 📊 **Tableau de bord** | KPIs en temps réel + 5 graphiques interactifs Plotly |
| ➕ **Collecte** | Formulaire structuré avec validation des données |
| 📈 **Analyse descriptive** | Stats complètes : moyenne, médiane, écart-type, boxplots, corrélations |
| 🗃️ **Données** | Tableau filtrable avec recherche et suppression |
| 💾 **Export** | Téléchargement CSV et JSON |

---

## 🗺️ Couverture géographique

Cameroun · Côte d'Ivoire · Sénégal · Mali · Ghana · Nigeria · RDC · Éthiopie · Kenya · Tanzania · Burkina Faso · Niger · Guinée · Togo · Bénin

---

## 🌾 Cultures supportées

Maïs · Cacao · Café · Manioc · Plantain · Sorgho · Mil · Riz · Arachide · Igname · Tomate · Oignon · Coton · Haricot · Banane

---

## 🚀 Installation locale

### Prérequis
- Python 3.10+
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/juniornatolo-ctrl/AgriVision-collect.git
cd AgriVision-collect

# 2. Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
streamlit run app.py
```

L'application s'ouvre automatiquement sur **http://localhost:8501**

---

## 🌐 Déploiement en ligne

L'application est déployée sur **Streamlit Community Cloud** :

🔗 **[https://juniornatolo-ctrl-agrivision-collect.streamlit.app](https://juniornatolo-ctrl-agrivision-collect.streamlit.app)**

---

## 🗄️ Structure du projet

```
AgriVision-collect/
│
├── app.py                  # Application Streamlit principale
├── requirements.txt        # Dépendances Python
├── agrivision_data.db      # Base de données SQLite (générée automatiquement)
└── README.md               # Ce fichier
```

---

## 📊 Variables collectées

| Variable | Type | Description |
|----------|------|-------------|
| `pays` | Texte | Pays africain |
| `region` | Texte | Région / Province |
| `culture` | Texte | Culture principale |
| `superficie` | Numérique | Surface en hectares |
| `rendement` | Numérique | Rendement estimé (t/ha) |
| `sol` | Catégoriel | Type de sol |
| `irrigation` | Catégoriel | Mode d'irrigation |
| `engrais` | Catégoriel | Type d'engrais |
| `maladie` | Catégoriel | Maladie observée |
| `ph_sol` | Numérique | pH du sol (optionnel) |
| `temperature` | Numérique | Température moyenne °C (optionnel) |
| `pluviometrie` | Numérique | Pluviométrie annuelle mm (optionnel) |
| `notes` | Texte | Observations libres |

---

## 📦 Dépendances

```
streamlit==1.32.0
pandas==2.2.1
plotly==5.20.0
```

---

## 🧑‍💻 Auteur

**Junior Natolo**
- GitHub : [@juniornatolo-ctrl](https://github.com/juniornatolo-ctrl)
- YouTube : [@JUNIORNATOLO](https://youtube.com/@JUNIORNATOLO)
- Université de Yaoundé 1 — Département d'Informatique

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

> *Développé avec ❤️ pour les agriculteurs africains — AgriVision AI © 2026*
