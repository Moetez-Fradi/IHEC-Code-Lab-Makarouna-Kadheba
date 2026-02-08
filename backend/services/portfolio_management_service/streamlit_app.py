"""Streamlit demo — Conseiller en Portefeuille Tunisien."""

import os
import time

import httpx
import pandas as pd
import streamlit as st

BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# ── page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Conseiller Portefeuille BVMT",
    page_icon="🇹🇳",
    layout="wide",
)


def _post(path: str, body: dict, timeout: float = 600):
    try:
        r = httpx.post(f"{BASE}{path}", json=body, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return None


def _get(path: str, timeout: float = 120):
    try:
        r = httpx.get(f"{BASE}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return None


# ── header ───────────────────────────────────────────────────
st.markdown(
    """
    <div style='text-align:center; padding: 1rem 0 0.5rem 0;'>
        <h1 style='margin-bottom:0;'>🇹🇳 Conseiller en Portefeuille — BVMT</h1>
        <p style='color:gray; font-size:1.1rem; margin-top:0.3rem;'>
            Optimisation intelligente par RL · Données réelles · Explainability IA
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ── step 1 : user input ─────────────────────────────────────
st.markdown("## 1️⃣  Votre profil d'investisseur")

col_profile, col_capital = st.columns([1, 1])

with col_profile:
    PROFILES = {
        "🛡️ Conservateur": "conservateur",
        "⚖️ Modéré": "modere",
        "🚀 Agressif": "agressif",
    }
    PROFILE_INFO = {
        "conservateur": (
            "Priorité à la **préservation du capital**. "
            "Diversification maximale, faible concentration (max 15 %/actif), volatilité limitée."
        ),
        "modere": (
            "**Équilibre rendement / risque**. "
            "Concentration modérée (max 25 %/actif), volatilité maîtrisée."
        ),
        "agressif": (
            "Recherche de **rendement maximal**. "
            "Concentration élevée (jusqu'à 50 %/actif), tolérance au drawdown."
        ),
    }

    selected_label = st.radio(
        "Choisissez votre profil de risque :",
        list(PROFILES.keys()),
        index=1,
        horizontal=True,
    )
    profile = PROFILES[selected_label]
    st.info(PROFILE_INFO[profile])

with col_capital:
    capital = st.number_input(
        "💰 Capital à investir (TND)",
        min_value=1_000,
        max_value=10_000_000,
        value=5_000,
        step=1_000,
        help="Montant en Dinars Tunisiens que vous souhaitez investir.",
    )
    st.markdown(f"**Vous investissez {capital:,.0f} TND** avec un profil **{profile}**.")

st.divider()

# ── step 2 : launch ─────────────────────────────────────────
st.markdown("## 2️⃣  Lancer l'analyse")

run_btn = st.button("🔍  Analyser et recommander", type="primary", use_container_width=True)

if run_btn:
    # ── 2a. fetch macro data ─────────────────────────────────
    with st.spinner("📡 Collecte des données macroéconomiques (Banque Mondiale, FMI, BCT)…"):
        macro = _get("/macro")

    # ── 2b. quick-train if needed ────────────────────────────
    with st.spinner("🧠 Entraînement de l'agent RL (PPO) + stress adversarial…"):
        _post("/train", {"timesteps": 4096, "adversarial": False})

    # ── 2c. recommend ────────────────────────────────────────
    with st.spinner("🤖 Calcul de la recommandation + SHAP + LLM…"):
        rec = _post("/recommend", {"profile": profile})

    # ── 2d. simulate ─────────────────────────────────────────
    with st.spinner("📊 Simulation historique avec votre capital…"):
        sim = _post("/simulate", {"profile": profile, "capital": capital})

    if not rec or not sim:
        st.error("Une erreur est survenue. Vérifiez que l'API est lancée.")
        st.stop()

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # RESULTS
    # ═══════════════════════════════════════════════════════════

    st.markdown("## 3️⃣  Résultats de votre analyse")

    # ── 3a. key metrics row ──────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    gain = sim["final_value"] - sim["initial_capital"]
    m1.metric("Capital initial", f"{sim['initial_capital']:,.0f} TND")
    m2.metric("Valeur finale", f"{sim['final_value']:,.2f} TND", delta=f"{gain:+,.2f} TND")
    m3.metric("ROI", f"{sim['roi']:+.2f} %")
    m4.metric("Max Drawdown", f"{sim['max_drawdown']:.2f} %")

    st.markdown("")

    # ── 3b. allocation chart + details side by side ──────────
    col_chart, col_detail = st.columns([3, 2])

    with col_chart:
        st.markdown("### 📊 Répartition recommandée")

        # Filter out zero-weight tickers for cleaner display
        w_items = [(k, v) for k, v in rec["weights"].items() if v > 0.001]
        if w_items:
            wdf = pd.DataFrame(w_items, columns=["Actif", "Poids"])
            wdf["Poids %"] = (wdf["Poids"] * 100).round(2)
            wdf["Montant (TND)"] = (wdf["Poids"] * capital).round(2)
            st.bar_chart(wdf.set_index("Actif")["Poids %"])
        cash_pct = (1.0 - sum(v for _, v in w_items)) * 100
        if cash_pct > 0.5:
            st.caption(f"💵 Cash conservé : {cash_pct:.1f} % ({cash_pct * capital / 100:,.0f} TND)")

    with col_detail:
        st.markdown("### 💼 Détail de l'allocation")
        if w_items:
            detail_df = wdf[["Actif", "Poids %", "Montant (TND)"]].copy()
            detail_df = detail_df.sort_values("Poids %", ascending=False)
            st.dataframe(detail_df, width="stretch", hide_index=True)

        st.markdown("### 📈 Métriques de performance")
        met = rec["metrics"]
        perf_data = {
            "Ratio de Sharpe": f"{met['sharpe']:.3f}",
            "Ratio de Sortino": f"{met['sortino']:.3f}",
            "Volatilité annualisée": f"{sim['volatility']:.2f} %",
            "Rendement total": f"{met['total_return'] * 100:+.2f} %",
            "Jours simulés": f"{sim['n_days']}",
        }
        perf_df = pd.DataFrame(perf_data.items(), columns=["Métrique", "Valeur"])
        st.dataframe(perf_df, width="stretch", hide_index=True)

    st.markdown("")

    # ── 3c. equity curve ─────────────────────────────────────
    st.markdown("### 📉 Courbe d'équité — évolution de votre capital")
    eq_df = pd.DataFrame({
        "Jour": range(len(sim["daily_values"])),
        "Valeur (TND)": sim["daily_values"],
    })
    st.line_chart(eq_df.set_index("Jour"), height=350)

    st.markdown("")

    # ── 3d. LLM explanation ──────────────────────────────────
    st.markdown("### 💬 Explication de l'IA")
    st.success(rec["explanation"])

    st.markdown("")

    # ── 3e. macro context ────────────────────────────────────
    if macro:
        st.markdown("### 🌍 Contexte macroéconomique utilisé")
        md = macro["data"]
        MACRO_LABELS = {
            "gdp_growth": ("Croissance PIB", "%"),
            "inflation": ("Inflation", "%"),
            "unemployment": ("Chômage", "%"),
            "exchange_rate_usd": ("Taux de change USD/TND", "TND"),
            "policy_rate": ("Taux directeur BCT", "%"),
            "tmm": ("Taux Marché Monétaire", "%"),
            "govt_debt_pct": ("Dette publique", "% du PIB"),
            "current_account": ("Balance courante", "% du PIB"),
            "reserves_usd": ("Réserves de change", "USD"),
        }
        mc1, mc2, mc3 = st.columns(3)
        cols = [mc1, mc2, mc3]
        for i, (key, (label, unit)) in enumerate(MACRO_LABELS.items()):
            val = md.get(key)
            if val is not None:
                if key == "reserves_usd":
                    display = f"{val / 1e9:.1f} Mrd"
                else:
                    display = f"{val:.2f}"
                cols[i % 3].metric(label, f"{display} {unit}")

    st.markdown("")

    # ── 3f. how it works ─────────────────────────────────────
    st.markdown("### ⚙️ Comment notre système fonctionne")
    with st.expander("Voir les détails techniques", expanded=False):
        st.markdown("""
**1. Collecte de données réelles**
- 🏦 **Banque Mondiale** : PIB, inflation, chômage, taux de change, réserves (API v2, pas de clé requise)
- 🌐 **FMI DataMapper** : croissance PIB, dette publique, balance courante (API publique)
- 🇹🇳 **BCT** : taux directeur, TMM, taux de change EUR/TND & USD/TND (scraping XLS)
- 📊 **BVMT** : cours historiques des 8 sociétés cotées (BIAT, BH, ATB, STB, SFBT, UIB, BNA, ATTIJARI)

**2. Feature engineering**
- Rendements journaliers, volatilité (rolling), RSI, SMA, MACD pour chaque titre

**3. Agent RL (PPO — Proximal Policy Optimization)**
- L'agent apprend à allouer les poids du portefeuille pour maximiser un ratio de Sharpe ajusté
- Récompense = rendement ajusté au risque − pénalité de drawdown − pénalité de stress
- Entraînement adversarial optionnel (un 2ᵉ agent injecte des crises pour renforcer la robustesse)

**4. Ajustement au profil de risque**
- Les poids bruts de l'agent RL sont ajustés selon votre profil :
  - 🛡️ Conservateur → max 15%/actif, volatilité plafonnée à 20%, 10% cash minimum
  - ⚖️ Modéré → max 25%/actif, volatilité plafonnée à 35%, 5% cash minimum
  - 🚀 Agressif → max 50%/actif, pas de plafond de volatilité

**5. Explainability (SHAP + LLM)**
- **SHAP** (SHapley Additive Explanations) identifie les facteurs qui ont le plus influencé la décision
- **LLM** (via OpenRouter) génère une explication en français adaptée à votre profil
- Si le LLM est indisponible → explication template locale

**6. Simulation**
- Votre capital virtuel est simulé sur l'historique de prix réel avec les poids recommandés
- Métriques calculées : ROI, Sharpe, Sortino, Max Drawdown, Volatilité annualisée
        """)

    st.divider()
    st.caption(
        "🏗️ Module 4 — Décision & Portefeuille · "
        "Données : Banque Mondiale · FMI · BCT · "
        "RL : Stable-Baselines3 (PPO) · "
        "Explainability : SHAP + LLM (OpenRouter)"
    )
