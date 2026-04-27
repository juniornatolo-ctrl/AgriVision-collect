import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import os
import json
import statistics

# ─── CONFIG PAGE ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgriVision AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS CUSTOM ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f7faf8; }
  [data-testid="stSidebar"] { background: #0F6E56 !important; }
  [data-testid="stSidebar"] * { color: white !important; }
  [data-testid="stSidebar"] .stRadio label { color: white !important; }
  [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2); }
  .metric-card {
    background: white; border-radius: 12px; padding: 1.2rem 1.5rem;
    border: 1px solid #e0ede8; margin-bottom: 0.5rem;
    box-shadow: 0 1px 4px rgba(15,110,86,0.07);
  }
  .metric-label { font-size: 12px; color: #6b8f7e; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
  .metric-value { font-size: 2rem; font-weight: 700; color: #0F6E56; line-height: 1.2; }
  .metric-unit  { font-size: 12px; color: #9ab5ab; margin-top: 2px; }
  .section-header {
    font-size: 1.1rem; font-weight: 700; color: #0F6E56;
    border-left: 4px solid #1D9E75; padding-left: 10px;
    margin: 1.5rem 0 1rem;
  }
  .badge-bon    { background:#d1f5e8; color:#0F6E56; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge-moyen  { background:#faeeda; color:#854F0B; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge-faible { background:#fde8e8; color:#9b2335; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
  .stButton>button {
    background: #0F6E56; color: white; border: none;
    border-radius: 8px; font-weight: 600; padding: 0.5rem 1.5rem;
  }
  .stButton>button:hover { background: #1D9E75; }
  div[data-testid="stForm"] { background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e0ede8; }
</style>
""", unsafe_allow_html=True)

# ─── BASE DE DONNÉES ──────────────────────────────────────────────────────────
DB_PATH = "agrivision_data.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collectes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            date_saisie   TEXT NOT NULL,
            pays          TEXT NOT NULL,
            region        TEXT NOT NULL,
            culture       TEXT NOT NULL,
            superficie    REAL NOT NULL,
            rendement     REAL NOT NULL,
            sol           TEXT NOT NULL,
            irrigation    TEXT NOT NULL,
            engrais       TEXT NOT NULL,
            maladie       TEXT NOT NULL,
            ph_sol        REAL,
            temperature   REAL,
            pluviometrie  REAL,
            notes         TEXT
        )
    """)
    conn.commit()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM collectes")
    if cur.fetchone()[0] == 0:
        demo = [
            ("2026-01-15","Cameroun","Centre","Cacao",3.2,1.4,"Limoneux","Pluviale","Organique","Aucune",6.2,26.0,1600,""),
            ("2026-01-20","Cameroun","Ouest","Maïs",1.8,2.6,"Volcanique","Mixte","Chimique","Pucerons",6.8,22.0,1400,"Traitements préventifs"),
            ("2026-02-03","Côte d'Ivoire","Nord","Café",4.5,1.1,"Latéritique","Pluviale","Aucun","Rouille",5.5,28.0,1100,"Sol acide"),
            ("2026-02-10","Sénégal","Centre","Mil",6.0,0.7,"Sableux","Pluviale","Aucun","Aucune",6.5,34.0,600,"Zone aride"),
            ("2026-02-18","Ghana","Sud","Cacao",2.1,1.9,"Argileux","Pluviale","Organique","Aucune",6.3,25.5,1800,""),
            ("2026-03-05","Nigeria","Est","Manioc",0.8,4.5,"Argileux","Irriguée","Chimique","Aucune",6.6,27.0,1200,"Bonne productivité"),
            ("2026-03-12","Kenya","Centre","Café",5.0,2.1,"Volcanique","Mixte","Mixte","Anthracnose",6.1,20.0,1500,"Highland coffee"),
            ("2026-03-20","RDC","Nord","Manioc",3.5,3.8,"Limoneux","Pluviale","Organique","Aucune",6.4,29.0,2000,""),
            ("2026-04-01","Mali","Nord","Sorgho",8.0,0.8,"Sableux","Pluviale","Aucun","Aucune",6.7,38.0,400,"Zone sahélienne"),
            ("2026-04-10","Cameroun","Littoral","Plantain",1.2,8.5,"Argileux","Irriguée","Organique","Mosaïque",6.9,27.0,2200,"Variété améliorée"),
            ("2026-04-15","Éthiopie","Centre","Café",7.0,1.6,"Volcanique","Pluviale","Organique","Aucune",6.0,18.0,1800,"Arabica highland"),
            ("2026-04-18","Tanzania","Sud","Riz",2.5,2.9,"Argileux","Irriguée","Chimique","Fusariose",6.5,26.0,1700,""),
        ]
        conn.executemany("""
            INSERT INTO collectes
            (date_saisie,pays,region,culture,superficie,rendement,sol,irrigation,engrais,maladie,ph_sol,temperature,pluviometrie,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, demo)
        conn.commit()
    conn.close()

@st.cache_data(ttl=5)
def load_data():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM collectes ORDER BY date_saisie DESC", conn)
    conn.close()
    return df

def invalidate_cache():
    load_data.clear()

# ─── CONSTANTES ───────────────────────────────────────────────────────────────
CULTURES   = ["Maïs","Cacao","Café","Manioc","Plantain","Sorgho","Mil","Riz","Arachide","Igname","Tomate","Oignon","Coton","Haricot","Banane"]
PAYS       = ["Cameroun","Côte d'Ivoire","Sénégal","Mali","Ghana","Nigeria","RDC","Éthiopie","Kenya","Tanzania","Burkina Faso","Niger","Guinée","Togo","Bénin"]
SOLS       = ["Argileux","Limoneux","Sableux","Latéritique","Volcanique","Tourbeux"]
IRRIGATIONS= ["Pluviale","Irriguée","Mixte"]
ENGRAIS    = ["Aucun","Organique","Chimique","Mixte"]
MALADIES   = ["Aucune","Mildiou","Rouille","Pourriture","Pucerons","Chenilles","Anthracnose","Fusariose","Mosaïque","Cercosporiose"]
COLORS     = ["#1D9E75","#0F6E56","#5DCAA5","#9FE1CB","#BA7517","#EF9F27","#E24B4A","#378ADD","#7F77DD","#D85A30","#FAC775","#F09595"]

GREEN_PALETTE = px.colors.sequential.Greens

init_db()

init_db()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌱 AgriVision AI")
    st.markdown("*Smart farming for Africa's future*")
    st.markdown("---")
    page = st.radio("Navigation", [
        "📊 Tableau de bord",
        "➕ Nouvelle collecte",
        "📈 Analyse descriptive",
        "🗃️ Données",
        "💾 Export"
    ])
    st.markdown("---")
    df_all = load_data()
    st.markdown(f"**{len(df_all)}** collectes enregistrées")
    st.markdown(f"**{df_all['pays'].nunique() if len(df_all) else 0}** pays couverts")

# ════════════════════════════════════════════════════════════════════════════════
# PAGE 1 : TABLEAU DE BORD
# ════════════════════════════════════════════════════════════════════════════════
if page == "📊 Tableau de bord":
    st.markdown("## 📊 Tableau de bord AgriVision AI")
    df = load_data()

    if df.empty:
        st.info("Aucune donnée. Commencez par saisir une collecte.")
        st.stop()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Collectes</div><div class="metric-value">{len(df)}</div><div class="metric-unit">entrées totales</div></div>', unsafe_allow_html=True)
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

    # Rendement par culture
    with col1:
        st.markdown('<div class="section-header">Rendement moyen par culture</div>', unsafe_allow_html=True)
        cult_avg = df.groupby("culture")["rendement"].mean().sort_values(ascending=True).reset_index()
        fig = px.bar(cult_avg, x="rendement", y="culture", orientation='h',
                     color="rendement", color_continuous_scale=["#9FE1CB","#1D9E75","#0F6E56"],
                     labels={"rendement":"t/ha","culture":"Culture"})
        fig.update_traces(texttemplate='%{x:.2f} t/ha', textposition='outside')
        fig.update_layout(margin=dict(l=0,r=40,t=10,b=10), height=320,
                          coloraxis_showscale=False, plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    # Répartition sols
    with col2:
        st.markdown('<div class="section-header">Types de sol</div>', unsafe_allow_html=True)
        sol_counts = df["sol"].value_counts().reset_index()
        sol_counts.columns = ["sol","count"]
        fig2 = px.pie(sol_counts, values="count", names="sol",
                      color_discrete_sequence=COLORS,
                      hole=0.45)
        fig2.update_traces(textposition='outside', textinfo='percent+label')
        fig2.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=320,
                           showlegend=False, plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    # Superficie par pays
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

    # Scatter rendement/superficie
    with col4:
        st.markdown('<div class="section-header">Rendement vs Superficie</div>', unsafe_allow_html=True)
        fig4 = px.scatter(df, x="superficie", y="rendement", color="culture",
                          size_max=18, opacity=0.85,
                          color_discrete_sequence=COLORS,
                          labels={"superficie":"Superficie (ha)","rendement":"Rendement (t/ha)","culture":"Culture"},
                          hover_data=["pays","sol","engrais"])
        fig4.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=300,
                           plot_bgcolor='white', paper_bgcolor='white',
                           legend=dict(font_size=10, orientation='h', yanchor='bottom', y=-0.4))
        st.plotly_chart(fig4, use_container_width=True)

    # Évolution temporelle
    st.markdown('<div class="section-header">Évolution des rendements dans le temps</div>', unsafe_allow_html=True)
    df_time = df.sort_values("date_saisie")
    fig5 = px.line(df_time, x="date_saisie", y="rendement", color="culture",
                   markers=True, color_discrete_sequence=COLORS,
                   labels={"date_saisie":"Date","rendement":"Rendement (t/ha)","culture":"Culture"})
    fig5.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=260,
                       plot_bgcolor='white', paper_bgcolor='white',
                       legend=dict(font_size=10, orientation='h', yanchor='bottom', y=-0.4))
    st.plotly_chart(fig5, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# PAGE 2 : NOUVELLE COLLECTE
# ════════════════════════════════════════════════════════════════════════════════
elif page == "➕ Nouvelle collecte":
    st.markdown("## ➕ Nouvelle collecte de données")

    with st.form("form_collecte", clear_on_submit=True):
        st.markdown('<div class="section-header">Localisation & Culture</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            pays    = st.selectbox("Pays *", PAYS)
            culture = st.selectbox("Culture principale *", CULTURES)
            sol     = st.selectbox("Type de sol *", SOLS)
            engrais = st.selectbox("Engrais utilisé", ENGRAIS)
        with c2:
            region    = st.text_input("Région / Province *", placeholder="ex : Centre, Nord, Ouest...")
            superficie= st.number_input("Superficie (ha) *", min_value=0.05, max_value=500.0, value=1.0, step=0.1)
            irrigation= st.selectbox("Mode d'irrigation", IRRIGATIONS)
            maladie   = st.selectbox("Maladie observée", MALADIES)

        st.markdown('<div class="section-header">Rendement & Paramètres climatiques</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            rendement   = st.slider("Rendement estimé (t/ha) *", 0.1, 20.0, 1.5, 0.1)
            ph_sol      = st.number_input("pH du sol (optionnel)", min_value=3.5, max_value=9.5, value=6.5, step=0.1)
        with c4:
            temperature  = st.number_input("Température moyenne °C (optionnel)", min_value=5.0, max_value=50.0, value=25.0, step=0.5)
            pluviometrie = st.number_input("Pluviométrie annuelle mm (optionnel)", min_value=50.0, max_value=5000.0, value=1200.0, step=50.0)

        notes = st.text_area("Observations libres", placeholder="Taches foliaires, attaques d'insectes, qualité du sol...")

        submitted = st.form_submit_button("✅ Enregistrer la collecte")

        if submitted:
            if not region.strip():
                st.error("La région est obligatoire.")
            else:
                conn = get_conn()
                conn.execute("""
                    INSERT INTO collectes
                    (date_saisie,pays,region,culture,superficie,rendement,sol,irrigation,engrais,maladie,ph_sol,temperature,pluviometrie,notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (datetime.date.today().isoformat(), pays, region, culture, superficie,
                      rendement, sol, irrigation, engrais, maladie, ph_sol, temperature, pluviometrie, notes))
                conn.commit()
                conn.close()
                invalidate_cache()
                st.success(f"✅ Collecte enregistrée : **{culture}** — **{pays}** — {rendement} t/ha")
                st.balloons()

# ════════════════════════════════════════════════════════════════════════════════
# PAGE 3 : ANALYSE DESCRIPTIVE
# ════════════════════════════════════════════════════════════════════════════════
elif page == "📈 Analyse descriptive":
    st.markdown("## 📈 Analyse descriptive complète")
    df = load_data()

    if df.empty:
        st.info("Aucune donnée disponible.")
        st.stop()

    # Filtres
    with st.expander("🔍 Filtres", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        pays_filtre    = fc1.multiselect("Pays", df["pays"].unique(), default=list(df["pays"].unique()))
        culture_filtre = fc2.multiselect("Culture", df["culture"].unique(), default=list(df["culture"].unique()))
        sol_filtre     = fc3.multiselect("Sol", df["sol"].unique(), default=list(df["sol"].unique()))
        df = df[df["pays"].isin(pays_filtre) & df["culture"].isin(culture_filtre) & df["sol"].isin(sol_filtre)]

    st.markdown(f"*{len(df)} entrées sélectionnées*")

    # Stats descriptives
    st.markdown('<div class="section-header">Statistiques du rendement (t/ha)</div>', unsafe_allow_html=True)
    rend = df["rendement"]
    s1, s2, s3, s4, s5, s6, s7 = st.columns(7)
    stats_vals = [
        ("Moyenne",    f"{rend.mean():.3f}"),
        ("Médiane",    f"{rend.median():.3f}"),
        ("Écart-type", f"{rend.std():.3f}"),
        ("Minimum",    f"{rend.min():.2f}"),
        ("Maximum",    f"{rend.max():.2f}"),
        ("Q1 (25%)",   f"{rend.quantile(0.25):.2f}"),
        ("Q3 (75%)",   f"{rend.quantile(0.75):.2f}"),
    ]
    for col, (label, val) in zip([s1,s2,s3,s4,s5,s6,s7], stats_vals):
        col.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value" style="font-size:1.4rem">{val}</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Boxplot rendement par culture
    with col1:
        st.markdown('<div class="section-header">Distribution par culture (Boxplot)</div>', unsafe_allow_html=True)
        fig = px.box(df, x="culture", y="rendement", color="culture",
                     color_discrete_sequence=COLORS,
                     labels={"rendement":"Rendement (t/ha)","culture":"Culture"})
        fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=10,b=60),
                          height=340, plot_bgcolor='white', paper_bgcolor='white',
                          xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    # Histogram rendement
    with col2:
        st.markdown('<div class="section-header">Distribution des rendements</div>', unsafe_allow_html=True)
        fig2 = px.histogram(df, x="rendement", nbins=15, color_discrete_sequence=["#1D9E75"],
                            labels={"rendement":"Rendement (t/ha)","count":"Fréquence"})
        fig2.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=340,
                           plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig2, use_container_width=True)

    # Tableau stats par culture
    st.markdown('<div class="section-header">Statistiques par culture</div>', unsafe_allow_html=True)
    stats_cult = df.groupby("culture")["rendement"].agg(
        Effectif="count", Moyenne="mean", Médiane="median",
        Min="min", Max="max", Écart_type="std", Total="sum"
    ).round(3).reset_index()
    stats_cult["Niveau"] = stats_cult["Moyenne"].apply(
        lambda x: "🟢 Bon" if x >= 2 else ("🟡 Moyen" if x >= 1 else "🔴 Faible")
    )
    st.dataframe(stats_cult, use_container_width=True, hide_index=True)

    # Corrélation
    st.markdown('<div class="section-header">Matrice de corrélation</div>', unsafe_allow_html=True)
    num_cols = ["superficie","rendement","ph_sol","temperature","pluviometrie"]
    corr_df  = df[num_cols].dropna().corr().round(3)
    fig_corr = px.imshow(corr_df, text_auto=True, color_continuous_scale="Greens",
                         title="", labels=dict(color="r"))
    fig_corr.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=320,
                           plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(fig_corr, use_container_width=True)

    # Maladies
    st.markdown('<div class="section-header">Maladies observées</div>', unsafe_allow_html=True)
    mal_counts = df["maladie"].value_counts().reset_index()
    mal_counts.columns = ["maladie","count"]
    mal_counts["color"] = mal_counts["maladie"].apply(lambda x: "#1D9E75" if x=="Aucune" else "#E24B4A")
    fig_m = px.bar(mal_counts, x="count", y="maladie", orientation='h',
                   color="maladie", color_discrete_sequence=COLORS,
                   labels={"count":"Nombre de cas","maladie":"Maladie"})
    fig_m.update_layout(showlegend=False, margin=dict(l=0,r=40,t=10,b=10),
                        height=280, plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(fig_m, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# PAGE 4 : DONNÉES
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🗃️ Données":
    st.markdown("## 🗃️ Toutes les données collectées")
    df = load_data()

    if df.empty:
        st.info("Aucune donnée.")
        st.stop()

    # Filtre rapide
    search = st.text_input("🔍 Recherche rapide (pays, culture...)", "")
    if search:
        mask = df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
        df   = df[mask]
    st.markdown(f"*{len(df)} entrée(s) affichée(s)*")

    # Ajout badge rendement
    def badge(v):
        if v >= 2:   return "🟢 Bon"
        if v >= 1:   return "🟡 Moyen"
        return "🔴 Faible"
    df_disp = df.copy()
    df_disp["niveau"] = df_disp["rendement"].apply(badge)
    cols_show = ["id","date_saisie","pays","region","culture","superficie","rendement","niveau","sol","irrigation","engrais","maladie"]
    st.dataframe(df_disp[cols_show], use_container_width=True, hide_index=True)

    # Suppression
    st.markdown("---")
    st.markdown("**Supprimer une entrée**")
    del_id = st.number_input("ID à supprimer", min_value=1, step=1, value=1)
    if st.button("🗑️ Supprimer", type="secondary"):
        conn = get_conn()
        conn.execute("DELETE FROM collectes WHERE id=?", (int(del_id),))
        conn.commit()
        conn.close()
        invalidate_cache()
        st.success(f"Entrée {del_id} supprimée.")
        st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# PAGE 5 : EXPORT
# ════════════════════════════════════════════════════════════════════════════════
elif page == "💾 Export":
    st.markdown("## 💾 Export des données")
    df = load_data()

    if df.empty:
        st.info("Aucune donnée à exporter.")
        st.stop()

    st.markdown(f"**{len(df)}** entrées prêtes à l'export.")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Export CSV")
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⬇️ Télécharger CSV",
            data=csv_data,
            file_name=f"agrivision_{datetime.date.today()}.csv",
            mime="text/csv"
        )

    with c2:
        st.markdown("#### Export JSON")
        json_data = json.dumps({
            "export_date": datetime.date.today().isoformat(),
            "total": len(df),
            "donnees": df.to_dict(orient="records")
        }, ensure_ascii=False, indent=2)
        st.download_button(
            label="⬇️ Télécharger JSON",
            data=json_data,
            file_name=f"agrivision_{datetime.date.today()}.json",
            mime="application/json"
        )

    st.markdown("---")
    st.markdown("#### Aperçu des données")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)
