# 💼 Portfolio Service

> **Portfolio optimization service with Markowitz theory and SHAP explainability**

## 📋 Overview

The Portfolio Service implements Modern Portfolio Theory (Markowitz) to optimize asset allocation for BVMT stocks. It uses SHAP (SHapley Additive exPlanations) to provide interpretability and explain portfolio recommendations.

## 🚀 Configuration

### Port
- **8007** (Production)

### Environment Variables

Create `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bvmt

# Optimization Parameters
MIN_WEIGHT=0.01        # Minimum weight per stock (1%)
MAX_WEIGHT=0.30        # Maximum weight per stock (30%)
RISK_FREE_RATE=0.05    # Risk-free rate (5%)

# ML Models
ENABLE_SHAP=true
SHAP_CACHE_DIR=./shap_cache

# Portfolio Constraints
MAX_STOCKS=20
MIN_STOCKS=5
REBALANCE_THRESHOLD=0.05  # 5% drift triggers rebalance
```

## 📦 Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Key Dependencies

```
cvxpy==1.4.2          # Convex optimization
shap==0.44.1          # ML explainability
pandas==2.1.4
numpy==1.26.3
scikit-learn==1.4.0
matplotlib==3.8.2
fastapi==0.109.0
uvicorn==0.27.0
```

## ▶️ Lancement

```bash
# Mode développement
python app.py

# Mode production
uvicorn app:app --host 0.0.0.0 --port 8007 --workers 2
```

## 🛠️ Endpoints

### 1. Optimisation de Portefeuille

```bash
POST /api/portfolio/optimize
```

**Body:**
```json
{
  "symbols": ["BNA", "BT", "ATB", "SFBT", "TUNISAIR"],
  "capital": 50000,
  "risk_profile": "moderate",
  "constraints": {
    "min_weight": 0.05,
    "max_weight": 0.25,
    "max_volatility": 0.20
  }
}
```

**Risk Profiles:**
- `conservative`: Min variance, max safety
- `moderate`: Balanced risk/return (Sharpe ratio)
- `aggressive`: Max return, higher risk

**Response:**
```json
{
  "portfolio": {
    "allocations": [
      {"symbol": "BNA", "weight": 0.25, "amount": 12500},
      {"symbol": "BT", "weight": 0.20, "amount": 10000},
      {"symbol": "ATB", "weight": 0.20, "amount": 10000},
      {"symbol": "SFBT", "weight": 0.20, "amount": 10000},
      {"symbol": "TUNISAIR", "weight": 0.15, "amount": 7500}
    ],
    "expected_return": 0.145,
    "expected_volatility": 0.182,
    "sharpe_ratio": 1.85
  },
  "shap_explanation": {
    "feature_importance": {
      "historical_return": 0.35,
      "volatility": 0.25,
      "sharpe_ratio": 0.20,
      "sector_diversification": 0.15,
      "liquidity": 0.05
    },
    "top_factors": [
      "BNA has strong historical returns (12% annually)",
      "Low correlation between BT and SFBT improves diversification",
      "TUNISAIR has high volatility but good risk/reward"
    ]
  }
}
```

### 2. Analyse de Portefeuille Existant

```bash
POST /api/portfolio/analyze
```

**Body:**
```json
{
  "holdings": [
    {"symbol": "BNA", "shares": 100, "avg_cost": 8.00},
    {"symbol": "BT", "shares": 200, "avg_cost": 5.50}
  ]
}
```

**Response:**
```json
{
  "current_value": 16500,
  "total_cost": 16000,
  "unrealized_gain": 500,
  "return_percent": 3.12,
  "metrics": {
    "expected_return": 0.11,
    "volatility": 0.19,
    "sharpe_ratio": 1.52,
    "beta": 0.95,
    "alpha": 0.02
  },
  "diversification": {
    "sector_weights": {
      "Banques": 0.75,
      "Industrie": 0.25
    },
    "concentration_risk": "moderate"
  }
}
```

### 3. Simulation Monte Carlo

```bash
POST /api/portfolio/simulate
```

**Body:**
```json
{
  "portfolio_id": "uuid-or-allocations",
  "simulations": 10000,
  "time_horizon_days": 252,
  "confidence_levels": [0.95, 0.99]
}
```

**Response:**
```json
{
  "simulations": 10000,
  "final_values": {
    "mean": 55000,
    "median": 54200,
    "std": 8500,
    "min": 32000,
    "max": 89000
  },
  "var": {
    "95%": -6500,
    "99%": -11000
  },
  "probability_of_loss": 0.32,
  "best_case": 89000,
  "worst_case": 32000
}
```

### 4. Rebalancement

```bash
POST /api/portfolio/rebalance
```

**Body:**
```json
{
  "current_holdings": [...],
  "target_allocations": [...]
}
```

**Response:**
```json
{
  "transactions": [
    {"symbol": "BNA", "action": "buy", "shares": 50, "amount": 412.5},
    {"symbol": "SFBT", "action": "sell", "shares": 30, "amount": 375}
  ],
  "total_cost": 37.5,
  "estimated_fees": 5.0
}
```

### 5. Frontière Efficiente

```bash
GET /api/portfolio/efficient-frontier
```

**Query Parameters:**
- `symbols`: Liste d'actions (comma-separated)
- `points`: Nombre de points (défaut: 50)

**Response:**
```json
{
  "frontier": [
    {"risk": 0.10, "return": 0.08},
    {"risk": 0.12, "return": 0.10},
    {"risk": 0.15, "return": 0.13},
    ...
  ],
  "optimal_portfolio": {
    "risk": 0.18,
    "return": 0.145,
    "sharpe": 1.85
  }
}
```

## 🧮 Algorithmes

### 1. Optimisation de Markowitz

**Objectif:**
Minimiser $\sigma^2 = w^T \Sigma w$ sous contraintes

**Contraintes:**
- $\sum_{i=1}^{n} w_i = 1$ (poids totaux = 100%)
- $w_{min} \leq w_i \leq w_{max}$ (limites par action)
- $\mu^T w \geq r_{target}$ (rendement minimum)

**Implémentation:**
```python
import cvxpy as cp

# Variables
weights = cp.Variable(n_assets)

# Objectif
portfolio_variance = cp.quad_form(weights, covariance_matrix)
objective = cp.Minimize(portfolio_variance)

# Contraintes
constraints = [
    cp.sum(weights) == 1,
    weights >= min_weight,
    weights <= max_weight,
    expected_returns @ weights >= target_return
]

# Résolution
problem = cp.Problem(objective, constraints)
problem.solve()
```

### 2. SHAP Explainability

```python
import shap

# Train model to predict optimal weights
model = XGBRegressor()
model.fit(features, optimal_weights)

# SHAP values
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(features)

# Top features influencing allocation
shap.summary_plot(shap_values, features)
```

## 📊 Métriques de Performance

### Sharpe Ratio
$$\text{Sharpe} = \frac{E[R_p] - R_f}{\sigma_p}$$

### Beta
$$\beta = \frac{\text{Cov}(R_p, R_m)}{\text{Var}(R_m)}$$

### Alpha (Jensen)
$$\alpha = E[R_p] - (R_f + \beta (E[R_m] - R_f))$$

## 🔧 Technologies

- **cvxpy** - Optimisation convexe
- **SHAP** - Explainability ML
- **NumPy/Pandas** - Calcul matriciel
- **scikit-learn** - ML models
- **FastAPI** - API REST

## 📝 Structure du Projet

```
portfolio_service/
├── app.py                     # API FastAPI
├── optimization/
│   ├── markowitz.py          # Optimisation Markowitz
│   ├── black_litterman.py    # Modèle Black-Litterman (optionnel)
│   └── constraints.py        # Gestion des contraintes
├── explainability/
│   ├── shap_explainer.py     # SHAP integration
│   └── reports.py            # Génération de rapports
├── simulation/
│   ├── monte_carlo.py        # Simulations MC
│   └── stress_testing.py     # Tests de stress
├── models/
│   ├── portfolio.py          # Modèles SQLAlchemy
│   └── schemas.py            # Schémas Pydantic
├── requirements.txt
└── README.md
```

## 🐛 Debugging

```bash
# Tester l'optimisation
curl -X POST http://localhost:8007/api/portfolio/optimize \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BNA", "BT"], "capital": 10000, "risk_profile": "moderate"}'

# Vérifier SHAP
python -c "import shap; print(shap.__version__)"

# Logs détaillés
LOG_LEVEL=DEBUG python app.py
```

## ⚡ Performance

- **Optimisation**: <1s pour 10-20 actions
- **Simulation MC**: ~3s pour 10k simulations
- **SHAP Calculation**: ~2s
- **Cache**: Résultats en cache (TTL 1h)

## 📚 Ressources

- **Markowitz (1952)**: [Portfolio Selection](https://www.jstor.org/stable/2975974)
- **SHAP**: [SHAP Documentation](https://shap.readthedocs.io/)
- **cvxpy**: [cvxpy Documentation](https://www.cvxpy.org/)

---

**Maintenu par:** Makarouna Kadheba - IHEC CodeLab 2.0
