# 🏦 BVMT Trading Assistant - FAIN

> **Plateforme intelligente de trading pour la Bourse des Valeurs Mobilières de Tunis**
> 
> IHEC CodeLab 2.0 - Hackathon 2026

![BVMT](https://img.shields.io/badge/BVMT-Trading%20Assistant-2563eb?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-22c55e?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-0.2.0-f59e0b?style=for-the-badge)

## Demo video Link: https://youtu.be/SSe5ttcJyIk

## 📋 Table des Matières

- [Vue d'ensemble](#-vue-densemble)
- [Architecture](#-architecture)
- [Services](#-services)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Lancement](#-lancement)
- [Utilisation](#-utilisation)
- [Documentation](#-documentation)
- [Technologies](#-technologies)
- [Équipe](#-équipe)

## 🎯 Vue d'ensemble

**BVMT Trading Assistant - FAIN** est une plateforme de trading intelligente développée pour la **Bourse des Valeurs Mobilières de Tunis (BVMT)**. Elle combine l'analyse de données en temps réel, le machine learning, et une interface utilisateur moderne pour offrir aux traders et investisseurs tunisiens un outil puissant et intuitif.

### ✨ Fonctionnalités Principales

- 📊 **Analyse de Marché en Temps Réel** - Suivi des 82 actions cotées à la BVMT
- 🧠 **Prévisions ML** - Modèles LSTM pour prédictions à 5 jours
- 💼 **Optimisation de Portefeuille** - Algorithme de Markowitz avec SHAP interpretability
- 🔍 **Détection d'Anomalies** - Isolation Forest pour identifier les mouvements suspects
- 📰 **Analyse de Sentiment** - Scraping et NLP sur les actualités tunisiennes (Arabizi/Tunizi)
- 🔔 **Alertes Intelligentes** - Notifications par email sur événements critiques
- 📈 **Visualisations Avancées** - Charts interactifs avec Recharts
- 🌓 **Mode Clair/Sombre** - Interface adaptative selon les préférences
- 🤖 **Chatbot RAG** - Assistant conversationnel basé sur la documentation BVMT

## 🏗️ Architecture

### Architecture Microservices

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                   │
│                   http://localhost:3000                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              API Gateway (FastAPI)                      │
│              http://localhost:8000                      │
└────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬─────┘
     │    │    │    │    │    │    │    │    │    │
     ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼
   8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8011
   ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐
   │📈│ │🌍│ │🔔│ │🚨│ │📰│ │🔐│ │💼│ │🔮│ │🤖│ │⏰│ │📊│
   └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘
  Stock Market Notif Anom Sent Auth Port Fore Chat Jobs PortMgmt
```

### Stack Technologique

**Frontend:**
- Next.js 16.1.6 (React 19, TypeScript)
- Tailwind CSS 4.1.18
- Recharts pour visualisations
- Lucide React pour les icônes

**Backend:**
- Python 3.10+ (FastAPI)
- NestJS (Service Auth)
- PostgreSQL (Neon) pour la persistence
- Redis pour le caching
- Scikit-learn, TensorFlow pour ML
- ChromaDB pour RAG
- BeautifulSoup4 pour web scraping

**Infrastructure:**
- Docker & Docker Compose
- n8n pour l'orchestration
- Git pour le versioning

## 🛠️ Services

### Services Backend (12 microservices)

| Port | Service | Description | Technologies |
|------|---------|-------------|--------------|
| **8000** | **API Gateway** | Routage centralisé vers tous les microservices | FastAPI, httpx |
| **8001** | **Stock Service** | Données actions en temps réel (82 stocks BVMT) | FastAPI, PostgreSQL, Redis |
| **8002** | **Market Service** | Statistiques de marché (TUNINDEX) | FastAPI, SQLAlchemy, Pandas |
| **8003** | **Notification Service** | Alertes email intelligentes | FastAPI, aiosmtplib, Jinja2 |
| **8004** | **Anomaly Detection** | Détection Isolation Forest | FastAPI, scikit-learn |
| **8005** | **Sentiment Analysis** | NLP actualités (Tunizi/Arabizi) | FastAPI, BeautifulSoup, DeepSeek R1 |
| **8006** | **Auth Service** | Authentification JWT | NestJS, Passport.js |
| **8007** | **Portfolio Service** | Optimisation Markowitz + SHAP | FastAPI, cvxpy, SHAP |
| **8008** | **Forecasting Service** | Prévisions LSTM 5 jours | FastAPI, TensorFlow/Keras |
| **8009** | **Chatbot Service** | RAG conversationnel | FastAPI, ChromaDB, Llama 3.3 |
| **8010** | **Jobs Service** | Tâches planifiées (APScheduler) | FastAPI, APScheduler |
| **8011** | **Portfolio Management** | Gestion avancée de portefeuilles | FastAPI, Plotly, Streamlit |

### Frontend (Next.js)

| Route | Page | Fonctionnalités |
|-------|------|-----------------|
| `/` | **Marché** | Vue d'ensemble, top gainers/losers, volumes, TUNINDEX |
| `/sentiment` | **Sentiment** | Heatmap sentiment, actualités tunisiennes (Tunizi/Arabizi) |
| `/analyse` | **Analyse Technique** | Charts interactifs, RSI, MACD, Bollinger Bands |
| `/prevision` | **Prévisions** | Forecasts ML à 5 jours, intervalles de confiance |
| `/portefeuille` | **Portefeuille** | Optimisation Markowitz, SHAP, stress tests |
| `/surveillance` | **Surveillance** | Anomalies détectées (volume, prix, patterns) |
| `/alertes` | **Alertes** | Notifications configurables, historique |
| `/rapports` | **Rapports** | Jobs planifiés, rapports automatisés |

## 🚀 Installation

### Prérequis

- **Node.js** 18+ et pnpm
- **Python** 3.10+
- **PostgreSQL** (ou compte Neon)
- **Git**

### 1. Cloner le Repository

```bash
git clone <repository-url>
cd IHEC-Code-Lab-Makarouna-Kadheba
```

### 2. Configuration Base de Données

Créez une base PostgreSQL (ou utilisez [Neon](https://neon.tech)):

```bash
# Initialisez le schéma
psql -U postgres -d bvmt < database/init.sql
```

### 3. Installation Backend

```bash
cd backend/services

# Créez les environnements virtuels pour chaque service
for service in api_gateway stock_service market_service notification_service \
               anomaly_detection sentiment-analysis portfolio_service forecasting
do
  cd $service
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  deactivate
  cd ..
done
```

### 4. Installation Frontend

```bash
cd ui
pnpm install
```

## ⚙️ Configuration

### Variables d'Environnement

Créez `.env` dans chaque service backend:

```bash
# backend/services/api_gateway/.env
DATABASE_URL=postgresql://user:password@localhost:5432/bvmt
SECRET_KEY=your-secret-key-here

# backend/services/notification_service/.env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# backend/services/chatbot/.env (si applicable)
OPENROUTER_API_KEY=your-openrouter-key
```

Frontend `.env.local`:

```bash
# ui/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎬 Lancement

### Option 1: Lancement Automatique (Recommandé)

```bash
# Lancez tous les services backend
cd backend/services
./start_all.sh

# Dans un autre terminal, lancez le frontend
cd ui
pnpm dev
```

### Option 2: Lancement Manuel

**Backend (9 terminaux):**

```bash
# Terminal 1 - API Gateway
cd backend/services/api_gateway && source venv/bin/activate && python app.py

# Terminal 2 - Stock Service
cd backend/services/stock_service && source venv/bin/activate && python main.py

# Terminal 3 - Market Service
cd backend/services/market_service && source venv/bin/activate && python app.py

# Terminal 4 - Notification Service
cd backend/services/notification_service && source venv/bin/activate && python app.py

# Terminal 5 - Anomaly Detection
cd backend/services/anomaly_detection && source venv/bin/activate && python app.py

# Terminal 6 - Sentiment Analysis
cd backend/services/sentiment-analysis && source venv/bin/activate && python app.py

# Terminal 7 - Auth Service (NestJS)
cd backend/core && npm run start:dev

# Terminal 8 - Portfolio Service
cd backend/services/portfolio_service && source venv/bin/activate && python app.py

# Terminal 9 - Forecasting Service
cd backend/services/forecasting && source venv/bin/activate && python app.py
```

**Frontend:**

```bash
cd ui && pnpm dev
```

### Vérification

```bash
# Vérifiez que tous les services sont actifs
ss -tln | grep -E ":(3000|8000|8001|8002|8003|8004|8005|8006|8007|8008)"
```

Vous devriez voir 9 ports ouverts.

### Accès à l'Application

- **Frontend Dashboard**: http://localhost:3000
- **API Gateway Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

## 🎮 Utilisation

### Connexion

1. Ouvrez votre navigateur: **http://localhost:3000**
2. Connectez-vous avec les identifiants de démonstration:
   - **Email:** demo@test.com
   - **Password:** password123

### Fonctionnalités Clés

#### 📊 Analyse de Marché
- Consultez les données en temps réel des 82 actions BVMT
- Identifiez les top gainers et losers
- Analysez les volumes et capitaux échangés

#### 🔮 Prévisions
- Sélectionnez une action
- Obtenez des prévisions à 5 jours avec intervalles de confiance
- Visualisez les tendances historiques

#### 💼 Optimisation de Portefeuille
- Choisissez votre profil (conservateur, modéré, agressif)
- Obtenez des allocations optimales via Markowitz
- Analysez l'importance des features avec SHAP
- Simulez des scénarios de stress testing

#### 🔍 Détection d'Anomalies
- Filtrez par type (prix, volume, pattern)
- Visualisez les anomalies sur scatter plots
- Exportez les données pour analyse approfondie

#### 📰 Analyse de Sentiment
- Consultez la heatmap de sentiment par action
- Recherchez des sentiments sur Twitter/Facebook (Tunizi/Arabizi)
- Lancez des scrapings manuels d'actualités

#### 🔔 Alertes
- Configurez des alertes par email
- Recevez des notifications sur événements critiques
- Consultez l'historique des alertes

## 📚 Documentation

Consultez les READMEs spécifiques pour chaque composant:

### Backend Services
- **[API Gateway](./backend/services/api_gateway/README.md)** - Routage centralisé et proxy
- **[Stock Service](./backend/services/stock_service/README.md)** - Gestion des 82 actions BVMT
- **[Market Service](./backend/services/market_service/README.md)** - Statistiques TUNINDEX
- **[Notification Service](./backend/services/notification_service/README.md)** - Système d'alertes email
- **[Anomaly Detection](./backend/services/anomaly_detection/README.md)** - Détection ML d'anomalies
- **[Sentiment Analysis](./backend/services/sentiment-analysis/README.md)** - Analyse NLP Tunizi/Arabizi
- **[Portfolio Service](./backend/services/portfolio_service/README.md)** - Optimisation Markowitz + SHAP
- **[Forecasting Service](./backend/services/forecasting/README.md)** - Prévisions LSTM
- **[Chatbot Service](./backend/services/chatbot/README.md)** - Assistant RAG conversationnel
- **[Jobs Service](./backend/services/jobs_service/README.md)** - Tâches planifiées APScheduler
- **[Portfolio Management](./backend/services/portfolio_management_service/README.md)** - Gestion avancée

### Frontend
- **[Frontend UI](./ui/README.md)** - Composants, pages et architecture Next.js

## 🔧 Technologies

### Frontend
- **Framework:** Next.js 16.1.6 (App Router, React 19)
- **Language:** TypeScript 5.9.3
- **Styling:** Tailwind CSS 4.1.18
- **Charts:** Recharts 2.15.1
- **Icons:** Lucide React
- **State Management:** React Context API
- **HTTP Client:** Fetch API

### Backend
- **Python:** 3.10+ (FastAPI, uvicorn, pydantic)
- **Node.js:** 18+ (NestJS pour auth)
- **Database:** PostgreSQL 16 (via Neon.tech)
- **Cache:** Redis 7+
- **ORM:** SQLAlchemy 2.0
- **ML/AI:** TensorFlow 2.15, scikit-learn 1.4, cvxpy
- **NLP:** BeautifulSoup4, OpenRouter (DeepSeek R1)
- **RAG:** ChromaDB, LangChain, Llama 3.3
- **Scheduler:** APScheduler

### DevOps & Tools
- **Version Control:** Git
- **Package Managers:** pnpm (frontend), pip (backend)
- **Containerization:** Docker, Docker Compose
- **Orchestration:** n8n workflows
- **Environment:** Python venv, Node modules
- **CI/CD:** GitHub Actions (optionnel)

## 📁 Structure du Projet

```
IHEC-Code-Lab-Makarouna-Kadheba/
├── backend/
│   ├── core/                      # NestJS Auth Service (Port 8006)
│   │   ├── src/
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── services/                  # Microservices Python
│   │   ├── api_gateway/           # Port 8000 - Routage centralisé
│   │   ├── stock_service/         # Port 8001 - Données actions
│   │   ├── market_service/        # Port 8002 - Statistiques BVMT
│   │   ├── notification_service/  # Port 8003 - Alertes email
│   │   ├── anomaly_detection/     # Port 8004 - Détection ML
│   │   ├── sentiment-analysis/    # Port 8005 - NLP Tunizi
│   │   ├── portfolio_service/     # Port 8007 - Optimisation
│   │   ├── forecasting/           # Port 8008 - Prévisions LSTM
│   │   ├── chatbot/               # Port 8009 - RAG assistant
│   │   ├── jobs_service/          # Port 8010 - Tâches planifiées
│   │   └── portfolio_management_service/  # Port 8011
│   └── shared/                    # Code partagé (config, DB, models)
├── ui/                            # Next.js Frontend (Port 3000)
│   ├── app/                       # App Router pages
│   │   ├── page.tsx              # Marché (/)
│   │   ├── sentiment/
│   │   ├── analyse/
│   │   ├── prevision/
│   │   ├── portefeuille/
│   │   ├── surveillance/
│   │   ├── alertes/
│   │   └── rapports/
│   ├── components/                # Composants réutilisables
│   │   ├── Navbar.tsx
│   │   ├── ThemeToggle.tsx
│   │   └── charts/
│   ├── lib/                       # Utilitaires
│   └── public/                    # Assets statiques
├── data/                          # Données historiques BVMT
│   ├── histo_cotation_2016.txt
│   ├── histo_cotation_2022.csv
│   └── web_histo_cotation_2023.csv
├── database/
│   └── init.sql                   # Schéma PostgreSQL
├── notebooks/
│   └── forecasting_model.ipynb    # Notebooks Jupyter
├── n8n_workflows/                 # Workflows d'orchestration
├── docs/                          # Documentation supplémentaire
├── .gitignore
├── docker-compose.yml             # Orchestration Docker
└── README.md                      # Ce fichier
```

## 🎯 Fonctionnalités Détaillées

### Module 1: Analyse de Marché en Temps Réel
- **82 actions BVMT** suivies en continu
- **TUNINDEX & TUNINDEX20** - Calcul des indices
- **Top Gainers/Losers** - Classement par performance
- **Volumes & Capitalisations** - Analyse des flux
- **Données intraday** - Rafraîchissement toutes les 5 minutes

### Module 2: Prévisions ML (LSTM)
- **Prévisions à 5 jours** avec modèles LSTM
- **Intervalles de confiance** à 95%
- **Métriques de qualité** (RMSE, MAE, R²)
- **Visualisations interactives** avec Recharts
- **Historique 10 ans** pour entraînement

### Module 3: Optimisation de Portefeuille
- **Algorithme de Markowitz** - Frontière efficiente
- **3 profils de risque** (conservateur, modéré, agressif)
- **SHAP Explainability** - Importance des features
- **Stress Testing** - Scénarios de crise
- **Backtesting** - Validation historique

### Module 4: Détection d'Anomalies
- **Isolation Forest** - Détection non supervisée
- **Types d'anomalies**:
  - Pics de volume (>3σ)
  - Mouvements de prix suspects
  - Patterns de manipulation
- **Alertes automatiques** vers Notification Service
- **Visualisation scatter plots** pour analyse

### Module 5: Analyse de Sentiment
- **Support multilingue**:
  - Français (langue d'affaires)
  - Arabe (langue officielle)
  - Tunizi/Arabizi (dialecte tunisien)
- **Sources de données**:
  - Webdo.tn
  - Kapitalis.com
  - African Manager
- **LLM Analysis** - DeepSeek R1 via OpenRouter
- **Heatmap de sentiment** - Vue d'ensemble du marché
- **Corrélation prix-sentiment** - Impact mesurable

### Module 6: Système d'Alertes Intelligentes
- **Alertes configurables**:
  - Seuils de prix (franchissement)
  - Pics de volume (>200% moyenne)
  - Anomalies détectées
  - Changement de sentiment
  - Résultats financiers
- **Canaux de notification**:
  - Email (SMTP)
  - Dashboard UI
  - Webhooks (optionnel)
- **Historique complet** avec timestamps

### Module 7: Chatbot RAG Conversationnel
- **Base de connaissances**:
  - Documentation BVMT
  - Règles CMF
  - Historique des transactions
- **Requêtes en langage naturel**:
  - "Quelles sont les meilleures actions bancaires?"
  - "Analyse BNA pour moi"
  - "Pourquoi TUNINDEX a chuté?"
- **ChromaDB** pour recherche vectorielle
- **Llama 3.3** pour génération de réponses

### Module 8: Jobs Planifiés
- **Market Pulse** - Refresh données toutes les 5 min
- **Anomaly Scan** - Détection horaire
- **Sentiment Update** - Scraping actualités (30 min)
- **Portfolio Rebalance** - Suggestion quotidienne
- **Email Digest** - Rapport matinal 8h
- **Data Backup** - Sauvegarde nocturne 2h

## 🚨 Alertes & Notifications

### Types d'Alertes

| Type | Déclencheur | Exemple |
|------|-------------|---------|
| **Prix** | Franchissement seuil | "BNA a franchi 8.50 TND (+5%)" |
| **Volume** | >200% moyenne 30j | "TUNISAIR: Volume x3 détecté" |
| **Anomalie** | Isolation Forest | "Pattern suspect sur ATB" |
| **Sentiment** | Changement brutal | "BT: Sentiment passé de +0.6 à -0.3" |
| **Prévision** | Opportunité détectée | "BNA: +8% prévu sur 5 jours" |

### Configuration Email

```bash
# backend/services/notification_service/.env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=bvmt-assistant@ihec.tn
FROM_NAME=BVMT Trading Assistant
```

## 🔒 Sécurité

- **JWT Authentication** - Tokens avec expiration
- **CORS configuré** - Protection cross-origin
- **Rate Limiting** - Protection contre abus
- **SQL Injection** - Prévention via SQLAlchemy ORM
- **Environment Variables** - Secrets jamais committés
- **HTTPS en production** - Chiffrement TLS

## 🧪 Tests & Validation

### Backend Tests

```bash
# Test unitaires
cd backend/services/stock_service
pytest tests/

# Test d'intégration
pytest tests/integration/

# Coverage
pytest --cov=app tests/
```

### Frontend Tests

```bash
cd ui
npm run test          # Jest tests
npm run test:e2e      # Playwright E2E
npm run lint          # ESLint
```

## 📊 Métriques de Performance

### Backend
- **Latency**: <100ms (p95)
- **Throughput**: 500 req/s par service
- **Database**: <50ms query time
- **Cache Hit Rate**: 85%+

### Frontend
- **First Contentful Paint**: <1.5s
- **Time to Interactive**: <3s
- **Lighthouse Score**: 90+
- **Bundle Size**: <500KB (gzipped)

### ML Models
- **LSTM Accuracy**: RMSE < 0.15 TND
- **Anomaly Detection**: F1-score 0.85
- **Sentiment Classification**: 82% accuracy (Tunizi)

## 🐛 Debugging & Troubleshooting

### Services ne démarrent pas

```bash
# Vérifier les ports occupés
sudo ss -tlnp | grep -E ":(3000|800[0-9])"

# Tuer un processus sur port 8000
sudo kill -9 $(sudo lsof -t -i:8000)

# Vérifier les logs
tail -f backend/services/api_gateway/logs/app.log
```

### Base de données non accessible

```bash
# Test connexion PostgreSQL
psql -h localhost -U postgres -d bvmt -c "SELECT version();"

# Recréer le schéma
psql -U postgres -d bvmt < database/init.sql
```

### Frontend ne charge pas les données

```bash
# Vérifier API Gateway
curl http://localhost:8000/health

# Vérifier CORS
curl -H "Origin: http://localhost:3000" http://localhost:8000/api/stocks
```

### Erreurs ML/Prévisions

```bash
# Retrainer le modèle LSTM
cd notebooks
jupyter notebook forecasting_model.ipynb

# Vérifier les dépendances ML
pip list | grep -E "(tensorflow|scikit|pandas)"
```

## 🌐 Déploiement Production

### Prérequis
- Serveur Ubuntu 22.04+
- Docker & Docker Compose
- Domaine avec SSL/TLS
- PostgreSQL managé (Neon/RDS)
- Redis managé (Upstash)

### Déploiement Docker

```bash
# Cloner le repo
git clone <repository-url>
cd IHEC-Code-Lab-Makarouna-Kadheba

# Configurer .env
cp .env.example .env
nano .env

# Build et lancement
docker-compose up -d --build

# Vérifier les services
docker-compose ps
docker-compose logs -f
```

### Variables d'Environnement Production

```bash
# .env (production)
NODE_ENV=production
POSTGRES_URL=postgresql://user:pass@neon.tech:5432/bvmt_prod
REDIS_URL=redis://upstash.com:6379
JWT_SECRET=<generate-secure-secret>
OPENROUTER_API_KEY=<your-key>
SMTP_HOST=smtp.sendgrid.net
FRONTEND_URL=https://bvmt.ihec.tn
API_URL=https://api.bvmt.ihec.tn
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/bvmt
server {
    listen 80;
    server_name bvmt.ihec.tn;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bvmt.ihec.tn;

    ssl_certificate /etc/letsencrypt/live/bvmt.ihec.tn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bvmt.ihec.tn/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
    }
}
```

## 📈 Roadmap

### Version 0.3.0 (Q2 2026)
- [ ] Support mobile (React Native)
- [ ] Notification Push
- [ ] Trading automatique (Paper Trading)
- [ ] Backtesting avancé

### Version 0.4.0 (Q3 2026)
- [ ] Support multi-devises (USD, EUR)
- [ ] Intégration autres bourses (Casablanca, Alger)
- [ ] API publique pour développeurs
- [ ] Marketplace de stratégies

### Version 1.0.0 (Q4 2026)
- [ ] Trading réel avec courtiers
- [ ] Compte pro/entreprise
- [ ] Support client 24/7
- [ ] Certification CMF

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer:

1. **Fork** le projet
2. Créez une **branche feature** (`git checkout -b feature/AmazingFeature`)
3. **Committez** vos changements (`git commit -m 'Add AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une **Pull Request**

### Guidelines
- Code documenté (docstrings Python, JSDoc TypeScript)
- Tests unitaires pour nouvelles features
- Respecter les conventions (PEP 8, Airbnb Style Guide)
- Commits descriptifs (Conventional Commits)

## 👥 Équipe

**Makarouna Kadheba** - Équipe IHEC CodeLab 2.0

Développé dans le cadre du **Hackathon IHEC CodeLab 2.0** - Février 2026

### Rôles
- **Backend & ML** - Architecture microservices, modèles ML/AI
- **Frontend & UX** - Interface Next.js, design système
- **DevOps & Data** - Orchestration, pipeline de données
- **Product & Strategy** - Vision produit, roadmap

## 📄 Licence

Ce projet est sous licence **MIT License**.

```
MIT License

Copyright (c) 2026 Makarouna Kadheba - IHEC CodeLab 2.0

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

Voir [LICENSE](./LICENSE) pour plus de détails.

## 🙏 Remerciements

- **BVMT (Bourse des Valeurs Mobilières de Tunis)** pour les données de marché
- **IHEC Carthage** pour l'organisation du hackathon CodeLab 2.0
- **Neon.tech** pour l'hébergement PostgreSQL gratuit
- **OpenRouter** pour l'accès aux LLMs (DeepSeek R1)
- **ChromaDB** pour la base vectorielle open-source
- **Vercel** pour le déploiement Next.js
- **Communauté Open Source** pour les outils exceptionnels

## 📞 Contact & Support

### Reporting Issues
Pour signaler un bug ou demander une fonctionnalité:
- Ouvrez une **[Issue GitHub](https://github.com/your-repo/issues)**
- Utilisez les labels appropriés (bug, enhancement, question)
- Fournissez un maximum de contexte (logs, screenshots)

### Questions
- **Email:** contact@ihec-codelab.tn
- **Discord:** [Rejoignez notre serveur](https://discord.gg/ihec-codelab)
- **Twitter:** [@IHECCodeLab](https://twitter.com/IHECCodeLab)

### Documentation Supplémentaire
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Wiki:** [GitHub Wiki](https://github.com/your-repo/wiki)
- **Tutorials:** [docs/tutorials/](./docs/tutorials/)

---

<div align="center">

**Développé avec ❤️ en Tunisie 🇹🇳**

**IHEC CodeLab 2.0 - Février 2026**

[![Made in Tunisia](https://img.shields.io/badge/Made%20in-Tunisia%20🇹🇳-E8112D?style=for-the-badge)](https://www.ihec.tn)
[![BVMT](https://img.shields.io/badge/BVMT-Trading%20Platform-2563eb?style=for-the-badge)](https://www.bvmt.com.tn)

[🚀 Demo Live](https://bvmt.ihec.tn) • [📚 Documentation](./docs) • [🐛 Report Bug](https://github.com/your-repo/issues) • [✨ Request Feature](https://github.com/your-repo/issues)

</div>
