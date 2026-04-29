import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import os
import json
import hashlib
import secrets

# ─── CONFIG PAGE ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgriVision AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f7faf8; }
[data-testid="stSidebar"] { background: #0F6E56 !important; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2); }
.metric-card {
    background: white; border-radius: 12px; padding: 1.2rem 1.5rem;
    border: 1px solid #e0ede8; margin-bottom: 0.5rem;
    box-shadow: 0 1px 4px rgba(15,110,86,0.07);
}
.metric-label { font-size: 12px; color: #6b8f7e; font-weight: 600;
    letter-spacing: 0.06em; text-transform: uppercase; }
.metric-value { font-size: 2rem; font-weight: 700; color: #0F6E56; line-height: 1.2; }
.metric-unit { font-size: 12px; color: #9ab5ab; margin-top: 2px; }
.section-header {
    font-size: 1.1rem; font-weight: 700; color: #0F6E56;
    border-left: 4px solid #1D9E75; padding-left: 10px;
    margin: 1.5rem 0 1rem;
}
.ai-card {
    background: linear-gradient(135deg, #0F6E56 0%, #1D9E75 100%);
    border-radius: 12px; padding: 1.5rem; color: white; margin-bottom: 1rem;
}
.ai-rec {
    background: white; border-radius: 8px; padding: 1rem;
    border-left: 4px solid #1D9E75; margin: 0.5rem 0;
}
.auth-card {
    background: white; border-radius: 16px; padding: 2rem;
    border: 1px solid #e0ede8; max-width: 450px; margin: 2rem auto;
    box-shadow: 0 4px 20px rgba(15,110,86,0.12);
}
.stButton>button {
    background: #0F6E56; color: white; border: none;
    border-radius: 8px; font-weight: 600; padding: 0.5rem 1.5rem;
}
.stButton>button:hover { background: #1D9E75; }
div[data-testid="stForm"] {
    background: white; border-radius: 12px; padding: 1.5rem;
    border: 1px solid #e0ede8;
}
</style>
""", unsafe_allow_html=True)

# ─── BASE DE DONNÉES ──────────────────────────────────────────────────────────
DB_PATH = "agrivision_data.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        # Table utilisateurs
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                nom TEXT,
                pays_defaut TEXT,
                created_at TEXT DEFAULT (date('now'))
            )
        """)
        # Table collectes avec user_id
        conn.execute("""
            CREATE TABLE IF NOT EXISTS collectes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date_saisie TEXT NOT NULL,
                pays TEXT NOT NULL,
                region TEXT NOT NULL,
                culture TEXT NOT NULL,
                superficie REAL NOT NULL,
                rendement REAL NOT NULL,
                sol TEXT NOT NULL,
                irrigation TEXT NOT NULL,
                engrais TEXT NOT NULL,
                maladie TEXT NOT NULL,
                ph_sol REAL,
                temperature REAL,
                pluviometrie REAL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()

# ─── AUTHENTIFICATION ─────────────────────────────────────────────────────────
def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()

def register_user(username: str, password: str, nom: str, pays_defaut: str) -> tuple[bool, str]:
    if len(username) < 3:
        return False, "Le nom d'utilisateur doit avoir au moins 3 caractères."
    if len(password) < 6:
        return False, "Le mot de passe doit avoir au moins 6 caractères."
    salt = secrets.token_hex(16)
    pwd_hash = hash_password(password, salt)
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, salt, nom, pays_defaut) VALUES (?,?,?,?,?)",
                (username.strip().lower(), pwd_hash, salt, nom, pays_defaut)
            )
            conn.commit()
        return True, "Compte créé avec succès !"
    except sqlite3.IntegrityError:
        return False, "Ce nom d'utilisateur est déjà pris."

def login_user(username: str, password: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username=?", (username.strip().lower(),)
        ).fetchone()
    if not row:
        return None, "Utilisateur introuvable."
    if hash_password(password, row["salt"]) != row["password_hash"]:
        return None, "Mot de passe incorrect."
    return dict(row), None

def get_user_by_id(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return dict(row) if row else None

# ─── DONNÉES ──────────────────────────────────────────────────────────────────
def load_data(user_id: int) -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql(
            "SELECT * FROM collectes WHERE user_id=? ORDER BY date_saisie DESC",
            conn, params=(user_id,)
        )
    return df

def invalidate_cache():
    pass  # cache désactivé

def insert_collecte(user_id, pays, region, culture, superficie, rendement,
                    sol, irrigation, engrais, maladie, ph_sol, temperature,
                    pluviometrie, notes):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO collectes
            (user_id,date_saisie,pays,region,culture,superficie,rendement,
             sol,irrigation,engrais,maladie,ph_sol,temperature,pluviometrie,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (user_id, datetime.date.today().isoformat(), pays, region, culture,
              superficie, rendement, sol, irrigation, engrais, maladie,
              ph_sol, temperature, pluviometrie, notes))
        conn.commit()
    invalidate_cache()

def delete_collecte(collecte_id: int, user_id: int):
    """Supprime seulement si appartient à l'utilisateur (sécurité)."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM collectes WHERE id=? AND user_id=?",
            (collecte_id, user_id)
        )
        conn.commit()
    invalidate_cache()

# ─── MODULE IA ────────────────────────────────────────────────────────────────

# Rendements de référence par culture (t/ha) basés sur données FAO Afrique subsaharienne
RENDEMENTS_REF = {
    "Maïs": {"faible": 1.0, "moyen": 2.5, "bon": 4.0, "max": 8.0},
    "Cacao": {"faible": 0.5, "moyen": 1.2, "bon": 2.0, "max": 3.5},
    "Café": {"faible": 0.4, "moyen": 1.0, "bon": 1.8, "max": 3.0},
    "Manioc": {"faible": 2.0, "moyen": 6.0, "bon": 10.0, "max": 20.0},
    "Plantain": {"faible": 3.0, "moyen": 7.0, "bon": 12.0, "max": 18.0},
    "Sorgho": {"faible": 0.5, "moyen": 1.2, "bon": 2.0, "max": 4.0},
    "Mil": {"faible": 0.4, "moyen": 0.8, "bon": 1.5, "max": 3.0},
    "Riz": {"faible": 1.5, "moyen": 2.5, "bon": 4.0, "max": 7.0},
    "Arachide": {"faible": 0.5, "moyen": 1.0, "bon": 1.8, "max": 3.5},
    "Igname": {"faible": 5.0, "moyen": 10.0, "bon": 15.0, "max": 25.0},
    "Tomate": {"faible": 5.0, "moyen": 12.0, "bon": 20.0, "max": 35.0},
    "Oignon": {"faible": 3.0, "moyen": 8.0, "bon": 15.0, "max": 25.0},
    "Coton": {"faible": 0.5, "moyen": 1.0, "bon": 1.8, "max": 3.0},
    "Haricot": {"faible": 0.4, "moyen": 0.8, "bon": 1.5, "max": 2.5},
    "Banane": {"faible": 5.0, "moyen": 12.0, "bon": 20.0, "max": 30.0},
}

MALADIES_IMPACT = {
    "Aucune": 0, "Pucerons": -15, "Chenilles": -20, "Mildiou": -30,
    "Rouille": -25, "Anthracnose": -35, "Fusariose": -40,
    "Mosaïque": -45, "Cercosporiose": -30, "Pourriture": -50,
}

ENGRAIS_IMPACT = {
    "Aucun": 0, "Organique": +15, "Chimique": +25, "Mixte": +35
}

IRRIGATION_IMPACT = {
    "Pluviale": 0, "Mixte": +20, "Irriguée": +40
}

def predire_rendement(culture, superficie, sol, irrigation, engrais,
                       maladie, ph_sol, temperature, pluviometrie):
    """Modèle règles-expertes pour prédire le rendement potentiel."""
    ref = RENDEMENTS_REF.get(culture, {"faible": 1, "moyen": 2, "bon": 4, "max": 8})
    base = ref["moyen"]

    # Ajustements (en %)
    score = 100
    score += MALADIES_IMPACT.get(maladie, 0)
    score += ENGRAIS_IMPACT.get(engrais, 0)
    score += IRRIGATION_IMPACT.get(irrigation, 0)

    # pH optimal 6.0–7.0
    if ph_sol:
        if 6.0 <= ph_sol <= 7.0:
            score += 10
        elif ph_sol < 5.5 or ph_sol > 7.5:
            score -= 20

    # Température
    if temperature:
        if 20 <= temperature <= 30:
            score += 5
        elif temperature > 38 or temperature < 10:
            score -= 25

    # Pluviométrie
    if pluviometrie:
        if 800 <= pluviometrie <= 2000:
            score += 10
        elif pluviometrie < 400:
            score -= 30
        elif pluviometrie > 3000:
            score -= 10

    rendement_pred = base * (score / 100)
    rendement_pred = max(ref["faible"] * 0.5, min(rendement_pred, ref["max"]))

    production_totale = rendement_pred * superficie

    # Niveau
    if rendement_pred >= ref["bon"]:
        niveau = "🟢 Bon"
        couleur = "#1D9E75"
    elif rendement_pred >= ref["faible"]:
        niveau = "🟡 Moyen"
        couleur = "#EF9F27"
    else:
        niveau = "🔴 Faible"
        couleur = "#E24B4A"

    return {
        "rendement_pred": round(rendement_pred, 2),
        "production_totale": round(production_totale, 2),
        "score": min(100, max(0, score)),
        "niveau": niveau,
        "couleur": couleur,
        "ref": ref,
    }

def generer_recommandations(culture, sol, irrigation, engrais, maladie,
                              ph_sol, temperature, pluviometrie, rendement_obs=None):
    """Génère des recommandations agronomiques basées sur les données."""
    recs = []

    # Engrais
    if engrais == "Aucun":
        recs.append(("🌿 Fertilisation", "Aucun engrais détecté. L'apport d'engrais organique (compost, fumier) peut augmenter le rendement de 15 à 35%. Commencer par 2 t/ha de compost."))
    elif engrais == "Chimique":
        recs.append(("🌿 Fertilisation", "Engrais chimique seul : risque d'acidification du sol à long terme. Alterner avec de l'organique pour maintenir la structure du sol."))

    # pH
    if ph_sol and ph_sol < 5.5:
        recs.append(("🧪 pH du sol", f"pH trop acide ({ph_sol}). Appliquer de la chaux agricole (1–2 t/ha) pour remonter le pH vers 6.0–6.5, zone optimale pour {culture}."))
    elif ph_sol and ph_sol > 7.5:
        recs.append(("🧪 pH du sol", f"pH trop basique ({ph_sol}). Apporter du soufre ou des matières organiques acides pour réduire le pH."))

    # Irrigation
    if irrigation == "Pluviale" and pluviometrie and pluviometrie < 800:
        recs.append(("💧 Irrigation", f"Pluviométrie insuffisante ({pluviometrie} mm/an). Le {culture} nécessite au moins 800 mm. Envisager un système goutte-à-goutte pour économiser l'eau."))

    # Maladies
    if maladie != "Aucune":
        traitements = {
            "Mildiou": "fongicide à base de cuivre (Bouillie Bordelaise), rotation des cultures",
            "Rouille": "fongicide triazole, éliminer les résidus infectés",
            "Pucerons": "insecticide pyréthrinoïde ou savon insecticide biologique",
            "Chenilles": "Bacillus thuringiensis (bio) ou insecticide à base de chlorpyrifos",
            "Anthracnose": "fongicide mancozèbe, semences certifiées saines",
            "Fusariose": "rotation sur 3 ans, variétés résistantes, drainage du sol",
            "Mosaïque": "contrôle des vecteurs (pucerons/aleurodes), plants sains certifiés",
            "Cercosporiose": "fongicide chlorothalonil, espacement adéquat des plants",
            "Pourriture": "améliorer le drainage, éviter l'excès d'humidité, fongicide préventif",
        }
        traitement = traitements.get(maladie, "consulter un agronome local")
        recs.append(("🦠 Maladie détectée", f"{maladie} identifiée. Recommandation : {traitement}."))

    # Température
    if temperature and temperature > 35:
        recs.append(("🌡️ Température", f"Température élevée ({temperature}°C). Utiliser des variétés tolérantes à la chaleur et augmenter les apports en eau aux heures fraîches."))

    # Rendement comparatif
    ref = RENDEMENTS_REF.get(culture, {})
    if rendement_obs and ref:
        if rendement_obs < ref.get("faible", 1):
            recs.append(("📊 Rendement", f"Rendement ({rendement_obs} t/ha) en dessous du seuil minimal pour {culture} ({ref['faible']} t/ha). Revoir l'ensemble des pratiques : sol, fertilisation, semences."))
        elif rendement_obs >= ref.get("bon", 3):
            recs.append(("📊 Rendement", f"Excellent rendement ! ({rendement_obs} t/ha). Documenter les pratiques actuelles pour les reproduire et partager avec d'autres agriculteurs."))

    # Recommandation générale si tout va bien
    if not recs:
        recs.append(("✅ Bonnes pratiques", "Vos paramètres agronomiques sont dans les normes. Continuer les pratiques actuelles et surveiller régulièrement l'apparition de maladies."))

    return recs

# ─── CONSTANTES ───────────────────────────────────────────────────────────────
CULTURES = ["Maïs","Cacao","Café","Manioc","Plantain","Sorgho","Mil","Riz",
            "Arachide","Igname","Tomate","Oignon","Coton","Haricot","Banane"]
PAYS = ["Cameroun","Côte d'Ivoire","Sénégal","Mali","Ghana","Nigeria","RDC",
        "Éthiopie","Kenya","Tanzania","Burkina Faso","Niger","Guinée","Togo","Bénin"]
SOLS = ["Argileux","Limoneux","Sableux","Latéritique","Volcanique","Tourbeux"]
IRRIGATIONS = ["Pluviale","Irriguée","Mixte"]
ENGRAIS = ["Aucun","Organique","Chimique","Mixte"]
MALADIES = ["Aucune","Mildiou","Rouille","Pourriture","Pucerons","Chenilles",
            "Anthracnose","Fusariose","Mosaïque","Cercosporiose"]
COLORS = ["#1D9E75","#0F6E56","#5DCAA5","#9FE1CB","#BA7517","#EF9F27",
          "#E24B4A","#378ADD","#7F77DD","#D85A30","#FAC775","#F09595"]

# Coordonnées approximatives des pays pour la carte
PAYS_COORDS = {
    "Cameroun": (5.5, 12.3), "Côte d'Ivoire": (7.5, -5.5), "Sénégal": (14.5, -14.5),
    "Mali": (17.0, -4.0), "Ghana": (8.0, -2.0), "Nigeria": (9.0, 8.0),
    "RDC": (-4.0, 23.0), "Éthiopie": (9.0, 39.0), "Kenya": (0.0, 38.0),
    "Tanzania": (-6.0, 35.0), "Burkina Faso": (12.5, -1.5), "Niger": (16.0, 8.0),
    "Guinée": (11.0, -11.5), "Togo": (8.0, 1.0), "Bénin": (9.0, 2.0),
}

init_db()

# ─── GESTION SESSION ──────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE AUTH
# ═══════════════════════════════════════════════════════════════════════════════
def show_auth():
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem">
        <h1 style="color:#0F6E56; font-size:2.5rem">🌱 AgriVision AI</h1>
        <p style="color:#6b8f7e; font-size:1.1rem">Smart farming for Africa's future</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 Connexion", "📝 Créer un compte"])

    with tab_login:
        with st.form("form_login"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter", use_container_width=True)
            if submit:
                user, err = login_user(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error(err)

    with tab_register:
        with st.form("form_register"):
            st.markdown("**Créer votre compte agriculteur**")
            c1, c2 = st.columns(2)
            with c1:
                new_username = st.text_input("Nom d'utilisateur *")
                new_nom = st.text_input("Nom complet")
            with c2:
                new_password = st.text_input("Mot de passe *", type="password")
                new_pays = st.selectbox("Pays principal", PAYS)
            submit_reg = st.form_submit_button("Créer mon compte", use_container_width=True)
            if submit_reg:
                ok, msg = register_user(new_username, new_password, new_nom, new_pays)
                if ok:
                    st.success(msg + " Connectez-vous maintenant.")
                else:
                    st.error(msg)

# ═══════════════════════════════════════════════════════════════════════════════
# APP PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════
def show_app():
    user = st.session_state.user
    user_id = user["id"]

    # SIDEBAR
    with st.sidebar:
        st.markdown(f"### 🌱 AgriVision AI")
        st.markdown(f"*Smart farming for Africa's future*")
        st.markdown("---")
        nom_affiche = user.get("nom") or user["username"]
        st.markdown(f"👤 **{nom_affiche}**")
        st.markdown(f"🌍 {user.get('pays_defaut', '')}")
        st.markdown("---")

        page = st.radio("Navigation", [
            "📊 Tableau de bord",
            "➕ Nouvelle collecte",
            "🤖 IA & Recommandations",
            "🗺️ Carte interactive",
            "📈 Analyse descriptive",
            "🗃️ Mes données",
            "💾 Export",
        ])

        st.markdown("---")
        df_all = load_data(user_id)
        st.markdown(f"**{len(df_all)}** collectes enregistrées")
        if len(df_all) > 0:
            st.markdown(f"**{df_all['pays'].nunique()}** pays couverts")

        st.markdown("---")
        if st.button("🚪 Déconnexion"):
            st.session_state.user = None
            st.rerun()

    # ══════════════════════════════════════════════════════════════
    # PAGE 1 : TABLEAU DE BORD
    # ══════════════════════════════════════════════════════════════
    if page == "📊 Tableau de bord":
        nom_affiche = user.get("nom") or user["username"]
        st.markdown(f"## 📊 Tableau de bord — Bonjour, {nom_affiche} 👋")

        df = load_data(user_id)

        if df.empty:
            st.info("📭 Aucune donnée pour l'instant. Commencez par saisir votre première collecte !")
            st.stop()

        # KPIs
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Mes collectes</div><div class="metric-value">{len(df)}</div><div class="metric-unit">entrées totales</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Pays couverts</div><div class="metric-value">{df["pays"].nunique()}</div><div class="metric-unit">pays africains</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Superficie totale</div><div class="metric-value">{df["superficie"].sum():.1f}</div><div class="metric-unit">hectares</div></div>', unsafe_allow_html=True)
        with c4:
            moy = df["rendement"].mean()
            st.markdown(f'<div class="metric-card"><div class="metric-label">Rendement moyen</div><div class="metric-value">{moy:.2f}</div><div class="metric-unit">t/ha</div></div>', unsafe_allow_html=True)
        with c5:
            maladies_pct = (df["maladie"] != "Aucune").sum() / len(df) * 100
            st.markdown(f'<div class="metric-card"><div class="metric-label">Taux maladie</div><div class="metric-value">{maladies_pct:.0f}%</div><div class="metric-unit">des parcelles</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-header">Rendement moyen par culture</div>', unsafe_allow_html=True)
            cult_avg = df.groupby("culture")["rendement"].mean().sort_values().reset_index()
            fig = px.bar(cult_avg, x="rendement", y="culture", orientation='h',
                         color="rendement", color_continuous_scale=["#9FE1CB","#0F6E56"],
                         labels={"rendement":"t/ha","culture":"Culture"})
            fig.update_traces(texttemplate='%{x:.2f} t/ha', textposition='outside')
            fig.update_layout(margin=dict(l=0,r=50,t=10,b=10), height=320,
                              coloraxis_showscale=False, plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-header">Types de sol</div>', unsafe_allow_html=True)
            sol_counts = df["sol"].value_counts().reset_index()
            sol_counts.columns = ["sol","count"]
            fig2 = px.pie(sol_counts, values="count", names="sol",
                          color_discrete_sequence=COLORS, hole=0.45)
            fig2.update_traces(textposition='outside', textinfo='percent+label')
            fig2.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=320,
                               showlegend=False, plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown('<div class="section-header">Superficie par pays</div>', unsafe_allow_html=True)
            pays_sup = df.groupby("pays")["superficie"].sum().sort_values(ascending=False).reset_index()
            fig3 = px.bar(pays_sup, x="pays", y="superficie",
                          color="superficie", color_continuous_scale=["#9FE1CB","#0F6E56"],
                          labels={"superficie":"Hectares","pays":"Pays"})
            fig3.update_layout(margin=dict(l=0,r=0,t=10,b=60), height=300,
                               coloraxis_showscale=False, plot_bgcolor='white', paper_bgcolor='white',
                               xaxis_tickangle=-35)
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            st.markdown('<div class="section-header">Rendement vs Superficie</div>', unsafe_allow_html=True)
            fig4 = px.scatter(df, x="superficie", y="rendement", color="culture",
                              opacity=0.85, color_discrete_sequence=COLORS,
                              labels={"superficie":"Superficie (ha)","rendement":"Rendement (t/ha)"},
                              hover_data=["pays","sol","engrais"])
            fig4.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=300,
                               plot_bgcolor='white', paper_bgcolor='white',
                               legend=dict(font_size=10, orientation='h', yanchor='bottom', y=-0.5))
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown('<div class="section-header">Évolution des rendements dans le temps</div>', unsafe_allow_html=True)
        df_time = df.sort_values("date_saisie")
        fig5 = px.line(df_time, x="date_saisie", y="rendement", color="culture",
                       markers=True, color_discrete_sequence=COLORS,
                       labels={"date_saisie":"Date","rendement":"Rendement (t/ha)"})
        fig5.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=260,
                           plot_bgcolor='white', paper_bgcolor='white',
                           legend=dict(font_size=10, orientation='h', yanchor='bottom', y=-0.4))
        st.plotly_chart(fig5, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # PAGE 2 : NOUVELLE COLLECTE
    # ══════════════════════════════════════════════════════════════
    elif page == "➕ Nouvelle collecte":
        st.markdown("## ➕ Nouvelle collecte de données")

        pays_defaut = user.get("pays_defaut", PAYS[0])
        pays_idx = PAYS.index(pays_defaut) if pays_defaut in PAYS else 0

        with st.form("form_collecte", clear_on_submit=True):
            st.markdown('<div class="section-header">📍 Localisation & Culture</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                pays = st.selectbox("Pays *", PAYS, index=pays_idx)
                culture = st.selectbox("Culture principale *", CULTURES)
                sol = st.selectbox("Type de sol *", SOLS)
                engrais = st.selectbox("Engrais utilisé", ENGRAIS)
            with c2:
                region = st.text_input("Région / Province *", placeholder="ex : Centre, Nord, Ouest...")
                superficie = st.number_input("Superficie (ha) *", min_value=0.05, max_value=500.0, value=1.0, step=0.1)
                irrigation = st.selectbox("Mode d'irrigation", IRRIGATIONS)
                maladie = st.selectbox("Maladie observée", MALADIES)

            st.markdown('<div class="section-header">📊 Rendement & Paramètres climatiques</div>', unsafe_allow_html=True)
            c3, c4 = st.columns(2)
            with c3:
                rendement = st.slider("Rendement estimé (t/ha) *", 0.1, 20.0, 1.5, 0.1)
                ph_sol = st.number_input("pH du sol (optionnel)", min_value=3.5, max_value=9.5, value=6.5, step=0.1)
            with c4:
                temperature = st.number_input("Température moyenne °C (optionnel)", min_value=5.0, max_value=50.0, value=25.0, step=0.5)
                pluviometrie = st.number_input("Pluviométrie annuelle mm (optionnel)", min_value=50.0, max_value=5000.0, value=1200.0, step=50.0)

            notes = st.text_area("Observations libres", placeholder="Taches foliaires, qualité du sol, variété utilisée...")

            submitted = st.form_submit_button("✅ Enregistrer la collecte")

        if submitted:
            if not region.strip():
                st.error("⚠️ La région est obligatoire.")
            else:
                insert_collecte(user_id, pays, region, culture, superficie, rendement,
                                sol, irrigation, engrais, maladie, ph_sol, temperature,
                                pluviometrie, notes)
                st.success(f"✅ Collecte enregistrée : **{culture}** — **{pays}/{region}** — {rendement} t/ha")
                st.balloons()

                # Afficher une recommandation rapide
                recs = generer_recommandations(culture, sol, irrigation, engrais, maladie,
                                               ph_sol, temperature, pluviometrie, rendement)
                if recs:
                    st.markdown("**💡 Recommandation rapide basée sur vos données :**")
                    titre, texte = recs[0]
                    st.info(f"**{titre}** — {texte}")

    # ══════════════════════════════════════════════════════════════
    # PAGE 3 : IA & RECOMMANDATIONS
    # ══════════════════════════════════════════════════════════════
    elif page == "🤖 IA & Recommandations":
        st.markdown("## 🤖 Module IA — Prédiction & Recommandations")
        st.markdown("*Entrez vos paramètres pour obtenir une prédiction de rendement et des recommandations agronomiques personnalisées.*")

        df = load_data(user_id)

        tab1, tab2 = st.tabs(["🔮 Simulateur de rendement", "📋 Analyse de mes collectes"])

        with tab1:
            st.markdown('<div class="section-header">Paramètres de simulation</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                ia_culture = st.selectbox("Culture", CULTURES, key="ia_culture")
                ia_sol = st.selectbox("Type de sol", SOLS, key="ia_sol")
                ia_engrais = st.selectbox("Engrais", ENGRAIS, key="ia_engrais")
            with c2:
                ia_superficie = st.number_input("Superficie (ha)", min_value=0.1, max_value=500.0, value=1.0, step=0.1, key="ia_sup")
                ia_irrigation = st.selectbox("Irrigation", IRRIGATIONS, key="ia_irr")
                ia_maladie = st.selectbox("Maladie", MALADIES, key="ia_mal")
            with c3:
                ia_ph = st.number_input("pH du sol", min_value=3.5, max_value=9.5, value=6.5, step=0.1, key="ia_ph")
                ia_temp = st.number_input("Température °C", min_value=5.0, max_value=50.0, value=25.0, step=0.5, key="ia_temp")
                ia_pluv = st.number_input("Pluviométrie mm", min_value=50.0, max_value=5000.0, value=1200.0, step=50.0, key="ia_pluv")

            if st.button("🤖 Lancer la prédiction IA", type="primary"):
                result = predire_rendement(ia_culture, ia_superficie, ia_sol, ia_irrigation,
                                           ia_engrais, ia_maladie, ia_ph, ia_temp, ia_pluv)

                st.markdown("---")
                st.markdown('<div class="section-header">Résultats de la prédiction</div>', unsafe_allow_html=True)

                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                with col_r1:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Rendement prédit</div><div class="metric-value" style="color:{result["couleur"]}">{result["rendement_pred"]}</div><div class="metric-unit">t/ha</div></div>', unsafe_allow_html=True)
                with col_r2:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Production totale</div><div class="metric-value">{result["production_totale"]}</div><div class="metric-unit">tonnes</div></div>', unsafe_allow_html=True)
                with col_r3:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Score agronomique</div><div class="metric-value">{result["score"]}</div><div class="metric-unit">/ 100</div></div>', unsafe_allow_html=True)
                with col_r4:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Niveau</div><div class="metric-value" style="font-size:1.2rem">{result["niveau"]}</div><div class="metric-unit">potentiel</div></div>', unsafe_allow_html=True)

                # Gauge du score
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=result["score"],
                    title={"text": "Score agronomique global"},
                    gauge={
                        "axis": {"range": [0, 150]},
                        "bar": {"color": result["couleur"]},
                        "steps": [
                            {"range": [0, 60], "color": "#fde8e8"},
                            {"range": [60, 100], "color": "#faeeda"},
                            {"range": [100, 150], "color": "#d1f5e8"},
                        ],
                        "threshold": {"line": {"color": "#0F6E56", "width": 4}, "value": 100}
                    }
                ))
                fig_gauge.update_layout(height=260, margin=dict(l=20,r=20,t=40,b=10),
                                        paper_bgcolor='white')
                st.plotly_chart(fig_gauge, use_container_width=True)

                # Comparatif avec références
                ref = result["ref"]
                categories = ['Faible', 'Moyen', 'Bon', 'Prédit']
                valeurs = [ref["faible"], ref["moyen"], ref["bon"], result["rendement_pred"]]
                couleurs = ["#E24B4A", "#EF9F27", "#1D9E75", result["couleur"]]

                fig_comp = go.Figure(go.Bar(
                    x=categories, y=valeurs,
                    marker_color=couleurs,
                    text=[f"{v:.2f} t/ha" for v in valeurs],
                    textposition='outside'
                ))
                fig_comp.update_layout(
                    title=f"Comparatif rendement — {ia_culture}",
                    yaxis_title="t/ha", height=280,
                    plot_bgcolor='white', paper_bgcolor='white',
                    margin=dict(l=0,r=0,t=40,b=10)
                )
                st.plotly_chart(fig_comp, use_container_width=True)

                # Recommandations
                st.markdown('<div class="section-header">💡 Recommandations agronomiques</div>', unsafe_allow_html=True)
                recs = generer_recommandations(ia_culture, ia_sol, ia_irrigation, ia_engrais,
                                               ia_maladie, ia_ph, ia_temp, ia_pluv)
                for titre, texte in recs:
                    st.markdown(f'<div class="ai-rec"><strong>{titre}</strong><br><span style="color:#444; font-size:0.95rem">{texte}</span></div>', unsafe_allow_html=True)

        with tab2:
            if df.empty:
                st.info("Aucune collecte enregistrée. Commencez par saisir des données.")
            else:
                st.markdown('<div class="section-header">Analyse IA de vos collectes</div>', unsafe_allow_html=True)

                # Prédire pour chaque collecte et comparer
                df_ia = df.copy()
                preds = []
                for _, row in df_ia.iterrows():
                    r = predire_rendement(
                        row["culture"], row["superficie"], row["sol"],
                        row["irrigation"], row["engrais"], row["maladie"],
                        row.get("ph_sol", 6.5), row.get("temperature", 25),
                        row.get("pluviometrie", 1200)
                    )
                    preds.append(r["rendement_pred"])

                df_ia["rendement_predit"] = preds
                df_ia["ecart"] = (df_ia["rendement"] - df_ia["rendement_predit"]).round(2)
                df_ia["performance"] = df_ia["ecart"].apply(
                    lambda x: "🟢 Au-dessus" if x > 0 else ("🟡 Normal" if x > -0.5 else "🔴 En dessous")
                )

                cols_show = ["date_saisie","pays","culture","rendement","rendement_predit","ecart","performance"]
                st.dataframe(df_ia[cols_show], use_container_width=True, hide_index=True)

                # Graphique comparatif
                fig_comp2 = go.Figure()
                fig_comp2.add_trace(go.Bar(name='Observé', x=df_ia["culture"], y=df_ia["rendement"],
                                           marker_color="#1D9E75"))
                fig_comp2.add_trace(go.Bar(name='Prédit IA', x=df_ia["culture"], y=df_ia["rendement_predit"],
                                           marker_color="#EF9F27", opacity=0.7))
                fig_comp2.update_layout(
                    barmode='group', title="Rendement observé vs prédit par l'IA",
                    yaxis_title="t/ha", height=320,
                    plot_bgcolor='white', paper_bgcolor='white',
                    margin=dict(l=0,r=0,t=40,b=60),
                    xaxis_tickangle=-35
                )
                st.plotly_chart(fig_comp2, use_container_width=True)

                # Collectes avec le plus grand écart négatif
                worst = df_ia.nsmallest(3, "ecart")[["pays","culture","rendement","rendement_predit","ecart"]]
                if not worst.empty and worst["ecart"].min() < -0.3:
                    st.markdown("**⚠️ Collectes nécessitant une attention particulière :**")
                    for _, row in worst.iterrows():
                        if row["ecart"] < -0.3:
                            recs = generer_recommandations(
                                row["culture"], row["sol"] if "sol" in row else "Argileux",
                                row["irrigation"] if "irrigation" in row else "Pluviale",
                                row["engrais"] if "engrais" in row else "Aucun",
                                row["maladie"] if "maladie" in row else "Aucune",
                                row.get("ph_sol", 6.5), row.get("temperature", 25),
                                row.get("pluviometrie", 1200), row["rendement"]
                            )
                            with st.expander(f"🔴 {row['culture']} — {row['pays']} (écart: {row['ecart']:.2f} t/ha)"):
                                for titre, texte in recs:
                                    st.markdown(f"**{titre}** : {texte}")

    # ══════════════════════════════════════════════════════════════
    # PAGE 4 : CARTE INTERACTIVE
    # ══════════════════════════════════════════════════════════════
    elif page == "🗺️ Carte interactive":
        st.markdown("## 🗺️ Carte interactive — Répartition géographique")

        df = load_data(user_id)

        if df.empty:
            st.info("Aucune donnée disponible pour la carte.")
            st.stop()

        # Agrégation par pays
        pays_stats = df.groupby("pays").agg(
            nb_collectes=("id", "count"),
            superficie_totale=("superficie", "sum"),
            rendement_moyen=("rendement", "mean"),
            cultures=("culture", lambda x: ", ".join(x.unique()[:3]))
        ).reset_index().round(2)

        # Ajouter coordonnées
        pays_stats["lat"] = pays_stats["pays"].map(lambda p: PAYS_COORDS.get(p, (0,0))[0])
        pays_stats["lon"] = pays_stats["pays"].map(lambda p: PAYS_COORDS.get(p, (0,0))[1])

        col_vue1, col_vue2 = st.columns([2,1])

        with col_vue1:
            # Carte à bulles
            metric_carte = st.selectbox("Métrique à afficher", [
                "nb_collectes", "superficie_totale", "rendement_moyen"
            ], format_func=lambda x: {
                "nb_collectes": "Nombre de collectes",
                "superficie_totale": "Superficie totale (ha)",
                "rendement_moyen": "Rendement moyen (t/ha)"
            }[x])

            fig_map = px.scatter_geo(
                pays_stats,
                lat="lat", lon="lon",
                size=metric_carte,
                color="rendement_moyen",
                hover_name="pays",
                hover_data={
                    "nb_collectes": True,
                    "superficie_totale": True,
                    "rendement_moyen": True,
                    "cultures": True,
                    "lat": False, "lon": False
                },
                color_continuous_scale=["#fde8e8","#EF9F27","#1D9E75","#0F6E56"],
                size_max=50,
                scope="africa",
                labels={
                    "rendement_moyen": "Rendement moy. (t/ha)",
                    "nb_collectes": "Collectes",
                    "superficie_totale": "Superficie (ha)",
                    "cultures": "Cultures principales",
                }
            )
            fig_map.update_layout(
                height=500,
                geo=dict(
                    showframe=False,
                    showcoastlines=True,
                    coastlinecolor="lightgray",
                    showland=True,
                    landcolor="#f0f4f2",
                    showocean=True,
                    oceancolor="#e8f4f8",
                    projection_type="mercator",
                    center=dict(lat=5, lon=20),
                    lataxis_range=[-35, 38],
                    lonaxis_range=[-20, 55],
                ),
                margin=dict(l=0,r=0,t=20,b=0),
                paper_bgcolor='white',
                coloraxis_colorbar=dict(title="Rendement<br>(t/ha)")
            )
            st.plotly_chart(fig_map, use_container_width=True)

        with col_vue2:
            st.markdown('<div class="section-header">Résumé par pays</div>', unsafe_allow_html=True)
            for _, row in pays_stats.sort_values("rendement_moyen", ascending=False).iterrows():
                couleur = "#1D9E75" if row["rendement_moyen"] >= 2 else ("#EF9F27" if row["rendement_moyen"] >= 1 else "#E24B4A")
                st.markdown(f"""
                <div style="background:white; border-radius:8px; padding:0.8rem; margin:0.4rem 0;
                             border-left:4px solid {couleur}; border:1px solid #e0ede8;">
                    <strong>{row['pays']}</strong><br>
                    <span style="font-size:0.85rem; color:#666">
                        📋 {int(row['nb_collectes'])} collecte(s) •
                        🌾 {row['superficie_totale']:.1f} ha •
                        📊 {row['rendement_moyen']:.2f} t/ha
                    </span>
                </div>
                """, unsafe_allow_html=True)

        # Distribution géographique des cultures
        st.markdown('<div class="section-header">Distribution des cultures par pays</div>', unsafe_allow_html=True)
        cult_pays = df.groupby(["pays","culture"]).size().reset_index(name="count")
        fig_cult = px.bar(cult_pays, x="pays", y="count", color="culture",
                          color_discrete_sequence=COLORS,
                          labels={"count":"Nombre de collectes","pays":"Pays","culture":"Culture"})
        fig_cult.update_layout(height=350, plot_bgcolor='white', paper_bgcolor='white',
                               margin=dict(l=0,r=0,t=10,b=60), xaxis_tickangle=-35,
                               legend=dict(font_size=10, orientation='h', yanchor='bottom', y=-0.5))
        st.plotly_chart(fig_cult, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # PAGE 5 : ANALYSE DESCRIPTIVE
    # ══════════════════════════════════════════════════════════════
    elif page == "📈 Analyse descriptive":
        st.markdown("## 📈 Analyse descriptive complète")
        df = load_data(user_id)

        if df.empty:
            st.info("Aucune donnée disponible.")
            st.stop()

        with st.expander("🔍 Filtres", expanded=False):
            fc1, fc2, fc3 = st.columns(3)
            pays_filtre = fc1.multiselect("Pays", df["pays"].unique(), default=list(df["pays"].unique()))
            culture_filtre = fc2.multiselect("Culture", df["culture"].unique(), default=list(df["culture"].unique()))
            sol_filtre = fc3.multiselect("Sol", df["sol"].unique(), default=list(df["sol"].unique()))
            df = df[df["pays"].isin(pays_filtre) & df["culture"].isin(culture_filtre) & df["sol"].isin(sol_filtre)]
        st.markdown(f"*{len(df)} entrée(s) sélectionnée(s)*")

        if df.empty:
            st.warning("Aucune donnée avec ces filtres.")
            st.stop()

        st.markdown('<div class="section-header">Statistiques du rendement (t/ha)</div>', unsafe_allow_html=True)
        rend = df["rendement"]
        s1,s2,s3,s4,s5,s6,s7 = st.columns(7)
        stats_vals = [
            ("Moyenne", f"{rend.mean():.3f}"),
            ("Médiane", f"{rend.median():.3f}"),
            ("Écart-type", f"{rend.std():.3f}" if len(df) > 1 else "N/A"),
            ("Minimum", f"{rend.min():.2f}"),
            ("Maximum", f"{rend.max():.2f}"),
            ("Q1 (25%)", f"{rend.quantile(0.25):.2f}"),
            ("Q3 (75%)", f"{rend.quantile(0.75):.2f}"),
        ]
        for col, (label, val) in zip([s1,s2,s3,s4,s5,s6,s7], stats_vals):
            col.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value" style="font-size:1.4rem">{val}</div></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-header">Distribution par culture (Boxplot)</div>', unsafe_allow_html=True)
            fig = px.box(df, x="culture", y="rendement", color="culture",
                         color_discrete_sequence=COLORS)
            fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=10,b=60),
                              height=340, plot_bgcolor='white', paper_bgcolor='white',
                              xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-header">Distribution des rendements</div>', unsafe_allow_html=True)
            fig2 = px.histogram(df, x="rendement", nbins=15, color_discrete_sequence=["#1D9E75"],
                                labels={"rendement":"Rendement (t/ha)"})
            fig2.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=340,
                               plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="section-header">Statistiques par culture</div>', unsafe_allow_html=True)
        stats_cult = df.groupby("culture")["rendement"].agg(
            Effectif="count", Moyenne="mean", Médiane="median",
            Min="min", Max="max"
        ).round(3).reset_index()
        stats_cult["Niveau"] = stats_cult["Moyenne"].apply(
            lambda x: "🟢 Bon" if x >= 2 else ("🟡 Moyen" if x >= 1 else "🔴 Faible")
        )
        st.dataframe(stats_cult, use_container_width=True, hide_index=True)

        if len(df) >= 3:
            st.markdown('<div class="section-header">Matrice de corrélation</div>', unsafe_allow_html=True)
            num_cols = [c for c in ["superficie","rendement","ph_sol","temperature","pluviometrie"] if c in df.columns]
            corr_df = df[num_cols].dropna().corr().round(3)
            if not corr_df.empty:
                fig_corr = px.imshow(corr_df, text_auto=True, color_continuous_scale="Greens")
                fig_corr.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=320,
                                       plot_bgcolor='white', paper_bgcolor='white')
                st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown('<div class="section-header">Maladies observées</div>', unsafe_allow_html=True)
        mal_counts = df["maladie"].value_counts().reset_index()
        mal_counts.columns = ["maladie","count"]
        fig_m = px.bar(mal_counts, x="count", y="maladie", orientation='h',
                       color="maladie", color_discrete_sequence=COLORS)
        fig_m.update_layout(showlegend=False, margin=dict(l=0,r=40,t=10,b=10),
                            height=280, plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig_m, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # PAGE 6 : MES DONNÉES
    # ══════════════════════════════════════════════════════════════
    elif page == "🗃️ Mes données":
        st.markdown("## 🗃️ Mes données collectées")
        df = load_data(user_id)

        if df.empty:
            st.info("Aucune donnée. Commencez par saisir une collecte !")
            st.stop()

        search = st.text_input("🔍 Recherche rapide (pays, culture...)", "")
        if search:
            mask = df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
            df = df[mask]

        st.markdown(f"*{len(df)} entrée(s) affichée(s)*")

        def badge(v):
            if v >= 2: return "🟢 Bon"
            if v >= 1: return "🟡 Moyen"
            return "🔴 Faible"

        df_disp = df.copy()
        df_disp["niveau"] = df_disp["rendement"].apply(badge)
        cols_show = ["id","date_saisie","pays","region","culture","superficie",
                     "rendement","niveau","sol","irrigation","engrais","maladie"]
        st.dataframe(df_disp[cols_show], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("**🗑️ Supprimer une entrée**")
        st.caption("⚠️ Cette action est irréversible. Seules vos propres collectes peuvent être supprimées.")

        ids_disponibles = df["id"].tolist()
        if ids_disponibles:
            del_id = st.selectbox("Sélectionner l'ID à supprimer",
                                   ids_disponibles,
                                   format_func=lambda i: f"ID {i} — {df[df['id']==i]['culture'].values[0]} ({df[df['id']==i]['pays'].values[0]})")
            col_del1, col_del2 = st.columns([1, 4])
            with col_del1:
                if st.button("🗑️ Confirmer la suppression"):
                    delete_collecte(int(del_id), user_id)
                    st.success(f"Entrée {del_id} supprimée.")
                    st.rerun()

    # ══════════════════════════════════════════════════════════════
    # PAGE 7 : EXPORT
    # ══════════════════════════════════════════════════════════════
    elif page == "💾 Export":
        st.markdown("## 💾 Export de mes données")
        df = load_data(user_id)

        if df.empty:
            st.info("Aucune donnée à exporter.")
            st.stop()

        st.markdown(f"**{len(df)}** entrées prêtes à l'export.")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Export CSV")
            csv_data = df.drop(columns=["user_id"]).to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="⬇️ Télécharger CSV",
                data=csv_data,
                file_name=f"agrivision_{user['username']}_{datetime.date.today()}.csv",
                mime="text/csv"
            )
        with c2:
            st.markdown("#### Export JSON")
            export_df = df.drop(columns=["user_id"])
            json_data = json.dumps({
                "export_date": datetime.date.today().isoformat(),
                "utilisateur": user.get("nom") or user["username"],
                "total": len(export_df),
                "donnees": export_df.to_dict(orient="records")
            }, ensure_ascii=False, indent=2)
            st.download_button(
                label="⬇️ Télécharger JSON",
                data=json_data,
                file_name=f"agrivision_{user['username']}_{datetime.date.today()}.json",
                mime="application/json"
            )

        st.markdown("---")
        st.markdown("#### Aperçu")
        st.dataframe(df.drop(columns=["user_id"]).head(10), use_container_width=True, hide_index=True)


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────
if st.session_state.user is None:
    show_auth()
else:
    show_app()
