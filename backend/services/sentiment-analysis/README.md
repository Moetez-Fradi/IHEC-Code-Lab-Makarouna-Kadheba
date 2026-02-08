# 📰 Sentiment Analysis Service

> **NLP-powered sentiment analysis for BVMT stocks with Tunizi/Arabizi support**

## 📋 Overview

The Sentiment Analysis Service monitors financial news and social media to analyze sentiment about BVMT-listed companies. It uses LLM(Gemini ) to handle multilingual content including French, Arabic, and Tunisian dialect (Tunizi/Arabizi).

## 🚀 Configuration

### Port
- **8005** (Production)

### Environment Variables

Create `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bvmt
# Or use SQLite for lightweight deployment
DATABASE_URL=sqlite:///./sentiment.db

# LLM Configuration
OPENROUTER_API_KEY=your-openrouter-api-key
LLM_MODEL=deepseek/deepseek-r1-distill-llama-70b
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500

# Scraping Configuration
ENABLE_SCRAPING=true
SCRAPE_INTERVAL=1800  # 30 minutes
USER_AGENT=Mozilla/5.0 (compatible; BVMTBot/1.0)

# News Sources
SOURCE_WEBDO=https://www.webdo.tn/category/economie
SOURCE_KAPITALIS=https://kapitalis.com/tunisie/economie
SOURCE_AFRICAN_MANAGER=https://africanmanager.com/category/economie

# Social Media (optional)
ENABLE_TWITTER=false
ENABLE_FACEBOOK=false

# Sentiment Settings
SENTIMENT_THRESHOLD_POSITIVE=0.6
SENTIMENT_THRESHOLD_NEGATIVE=-0.6
```

## 📦 Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Key Dependencies

```
fastapi==0.109.0
beautifulsoup4==4.12.3
requests==2.31.0
openai==1.12.0  # For OpenRouter compatibility
sqlalchemy==2.0.25
aiohttp==3.9.3
uvicorn==0.27.0
```

## ▶️ Launch

```bash
# Development mode
python app/main.py

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8005 --workers 2
```

## 🛠️ API Endpoints

### 1. Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "sentiment-analysis",
  "llm_available": true
}
```

### 2. Trigger News Scraping

```bash
POST /api/sentiment/scrape
```

**Body:**
```json
{
  "sources": ["webdo", "kapitalis", "african_manager"],
  "force_refresh": false
}
```

**Response:**
```json
{
  "status": "success",
  "articles_scraped": 45,
  "articles_analyzed": 38,
  "companies_mentioned": 12,
  "scrape_time_seconds": 15.3
}
```

### 3. Get Daily Sentiment Data

```bash
GET /api/sentiment/sentiments/daily
```

**Query Parameters:**
- `date` (optional): Specific date (YYYY-MM-DD)
- `symbol` (optional): Filter by stock symbol

**Response:**
```json
{
  "date": "2026-02-08",
  "sentiments": [
    {
      "symbol": "BNA",
      "name": "Banque Nationale Agricole",
      "sentiment_score": 0.65,
      "sentiment_label": "positive",
      "articles_count": 8,
      "positive_count": 6,
      "negative_count": 1,
      "neutral_count": 1,
      "confidence": 0.82
    },
    {
      "symbol": "TUNISAIR",
      "name": "Tunisair",
      "sentiment_score": -0.45,
      "sentiment_label": "negative",
      "articles_count": 5,
      "positive_count": 1,
      "negative_count": 4,
      "neutral_count": 0,
      "confidence": 0.75
    }
  ]
}
```

### 4. Get Sentiment Heatmap Data

```bash
GET /api/sentiment/heatmap
```

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `symbols` (optional): Comma-separated stock symbols

**Response:**
```json
{
  "data": [
    {
      "date": "2026-02-08",
      "BNA": 0.65,
      "BT": 0.42,
      "ATB": 0.35,
      "TUNISAIR": -0.45
    }
  ],
  "stocks": ["BNA", "BT", "ATB", "TUNISAIR"]
}
```

### 5. Get Stock-Specific Sentiment

```bash
GET /api/sentiment/{symbol}
```

**Example:**
```bash
curl http://localhost:8005/api/sentiment/BNA
```

**Response:**
```json
{
  "symbol": "BNA",
  "name": "Banque Nationale Agricole",
  "current_sentiment": {
    "score": 0.65,
    "label": "positive",
    "confidence": 0.82,
    "updated_at": "2026-02-08T10:30:00Z"
  },
  "trend": {
    "7_day_avg": 0.58,
    "30_day_avg": 0.52,
    "direction": "improving"
  },
  "recent_articles": [
    {
      "title": "BNA annonce des bénéfices record pour 2025",
      "source": "Webdo",
      "date": "2026-02-08",
      "sentiment": 0.85,
      "url": "https://webdo.tn/..."
    }
  ]
}
```

### 6. Get Articles

```bash
GET /api/sentiment/articles
```

**Query Parameters:**
- `symbol` (optional): Filter by stock symbol
- `source` (optional): Filter by news source
- `sentiment` (optional): Filter by sentiment (positive/negative/neutral)
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "articles": [
    {
      "id": 1234,
      "title": "BNA: Des résultats en hausse de 12%",
      "content": "La Banque Nationale Agricole a annoncé...",
      "source": "Webdo",
      "url": "https://webdo.tn/article/123",
      "published_at": "2026-02-08T09:00:00Z",
      "scraped_at": "2026-02-08T09:15:00Z",
      "sentiment_score": 0.75,
      "sentiment_label": "positive",
      "companies_mentioned": ["BNA"],
      "language": "fr"
    }
  ],
  "total": 145,
  "page": 1
}
```

### 7. Generate Report

```bash
GET /api/sentiment/report/{symbol}
```

**Query Parameters:**
- `start_date` (required): Start date
- `end_date` (required): End date
- `format` (optional): "json" or "markdown" (default: "json")

**Returns:** Markdown or JSON sentiment report

## 🧠 Sentiment Analysis Pipeline

### 1. Web Scraping

```python
# Target websites
sources = [
    "Webdo.tn",           # Business news
    "Kapitalis.com",      # Economic news
    "African Manager"     # Tunisian economy
]

# Scraping process
1. Fetch article lists from category pages
2. Extract article content (title, body, date)
3. Clean HTML and extract text
4. Store raw articles in database
```

### 2. Company Detection

```python
# BVMT ticker mapping
tickers = {
    "BNA": ["Banque Nationale Agricole", "BNA"],
    "BT": ["Banque de Tunisie", "BT"],
    "TUNISAIR": ["Tunisair", "Tunis Air"],
    # ... 82 companies total
}

# Detection logic
for company in tickers:
    if any(alias in article_text for alias in company.aliases):
        companies_mentioned.append(company.symbol)
```

### 3. LLM Sentiment Analysis

**Prompt Template:**

```
Analyze the sentiment of this financial news article about {company_name}.

Article:
{article_text}

Provide:
1. Sentiment score from -1 (very negative) to +1 (very positive)
2. Confidence level (0-1)
3. Key phrases that influenced the sentiment

Language: The article may be in French, Arabic, or Tunisian dialect.

Respond in JSON format:
{
  "sentiment_score": 0.75,
  "confidence": 0.85,
  "key_phrases": ["bénéfices record", "croissance forte"],
  "reasoning": "Article discusses positive financial results"
}
```

**LLM Model:** DeepSeek R1 Distill Llama 70B (via OpenRouter)

### 4. Daily Aggregation

```python
# Aggregate daily sentiment
for symbol in stocks:
    articles = get_articles_for_symbol(symbol, date)
    
    if len(articles) == 0:
        continue
    
    # Weighted average by confidence
    sentiment_score = sum(
        article.sentiment * article.confidence 
        for article in articles
    ) / sum(article.confidence for article in articles)
    
    # Count sentiment distribution
    positive_count = len([a for a in articles if a.sentiment > 0.6])
    negative_count = len([a for a in articles if a.sentiment < -0.6])
    neutral_count = len(articles) - positive_count - negative_count
    
    save_daily_sentiment(symbol, date, sentiment_score, ...)
```

## 🌐 Multilingual Support

### Supported Languages

1. **French** - Primary business language in Tunisia
2. **Arabic** - Official language
3. **Tunizi/Arabizi** - Tunisian dialect (Arabic written in Latin script)

### Example Texts

**French:**
```
"La BNA enregistre une hausse de 12% de ses bénéfices"
→ Sentiment: +0.75
```

**Arabic:**
```
"البنك الوطني الفلاحي يسجل نموا قويا"
→ Sentiment: +0.80
```

**Tunizi/Arabizi:**
```
"BNA 3mlet natej mle7 barcha, profits zedou 12%"
→ Sentiment: +0.70
```

## 🔧 Technologies

- **FastAPI** - Web framework
- **BeautifulSoup4** - HTML parsing
- **Requests/aiohttp** - HTTP clients
- **OpenRouter** - LLM API gateway
- **SQLAlchemy** - Database ORM
- **SQLite/PostgreSQL** - Data storage

## 📝 Project Structure

```
sentiment-analysis/
├── app/
│   ├── main.py               # FastAPI entry point
│   ├── config.py             # Configuration
│   ├── database.py           # Database models
│   ├── services/
│   │   ├── scraper.py        # News scraping
│   │   ├── llm.py            # OpenRouter/DeepSeek
│   │   └── aggregator.py     # Daily aggregation
│   └── routers/
│       └── sentiment.py      # API endpoints
├── requirements.txt
└── README.md
```

## 🐛 Debugging

```bash
# Test scraping
curl -X POST http://localhost:8005/api/sentiment/scrape

# Check daily sentiment
curl http://localhost:8005/api/sentiment/sentiments/daily

# View logs
tail -f logs/sentiment_analysis.log

# Test LLM connection
curl http://localhost:8005/health
```

## 📊 Performance

- **Scraping Speed**: ~3 articles/second
- **LLM Analysis**: ~2s per article
- **Daily Aggregation**: <5s for 82 stocks
- **Cache**: Articles cached for 30 minutes

## 💰 Cost Estimation

**Using DeepSeek R1 (OpenRouter Free Tier):**
- **Cost per article**: ~$0.001
- **Daily articles**: ~100-150
- **Monthly cost**: ~$3-5

---

**Maintained by:** Makarouna Kadheba - IHEC CodeLab 2.0
# Get free API key from: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

### 3. Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: **http://localhost:8000**

## 📊 API Endpoints

### Health Check
```bash
GET /health
```

### Trigger Scraping & Analysis
```bash
POST /trigger-scrape
```

### Get Daily Sentiment Scores
```bash
GET /sentiments/daily
```

### List Recent Articles
```bash
GET /articles?limit=20&source=IlBoursa&ticker=SFBT
```

### 📝 Generate Company Sentiment Report (Markdown)
```bash
GET /report/{company}
```
Returns a downloadable `.md` file with a full sentiment report for the given company. Accepts ticker symbols (`SFBT`, `BIAT`) or full company names (`Poulina Group Holding`, `Banque Internationale Arabe de Tunisie`).

---

## 🧪 API Testing Guide

### Test 1: Health Check

```bash
curl -X GET "http://localhost:8000/health" | jq
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "BVMT Sentiment Analysis"
}
```

### Test 2: View API Documentation

Open in browser: **http://localhost:8000/docs**

This opens the interactive Swagger UI for testing all endpoints.

### Test 3: Check Empty Database

```bash
curl -X GET "http://localhost:8000/articles" | jq
```

**Expected Response:**
```json
{
  "count": 0,
  "articles": []
}
```

### Test 4: Trigger Scraping Pipeline

```bash
curl -X POST "http://localhost:8000/trigger-scrape" | jq
```

**Expected Response:**
```json
{
  "status": "accepted", 
  "message": "Scrape & analysis pipeline queued. Check /articles shortly."
}
```

> ⏱️ **Note**: This runs in background. Wait 30-60 seconds for completion.

### Test 5: Check Scraped Articles

```bash
# Wait a minute, then check articles
curl -X GET "http://localhost:8000/articles?limit=10" | jq
```

**Expected Response:**
```json
{
  "count": 8,
  "articles": [
    {
      "id": 1,
      "source": "IlBoursa",
      "title": "BIAT annonce ses résultats du 4ème trimestre 2025",
      "url": "https://www.ilboursa.com/marches/actualites/...",
      "language": "fr",
      "sentiment": "positive",
      "score": 0.7,
      "ticker": "BIAT",
      "created_at": "2026-02-08T01:15:30"
    }
  ]
}
```

### Test 6: Get Daily Sentiment Aggregation

```bash
curl -X GET "http://localhost:8000/sentiments/daily" | jq
```

**Expected Response:**
```json
{
  "date": "2026-02-08",
  "tickers": [
    {
      "ticker": "BIAT",
      "avg_score": 0.65,
      "article_count": 3
    },
    {
      "ticker": "SFBT", 
      "avg_score": -0.2,
      "article_count": 1
    }
  ]
}
```

### Test 7: Filter by Source

```bash
# Get only IlBoursa articles
curl -X GET "http://localhost:8000/articles?source=IlBoursa&limit=5" | jq

# Get only Arabic articles from TunisieNumerique  
curl -X GET "http://localhost:8000/articles?source=TunisieNumerique&limit=5" | jq
```

### Test 8: Filter by Ticker

```bash
# Get articles mentioning BIAT bank
curl -X GET "http://localhost:8000/articles?ticker=BIAT&limit=5" | jq

# Get articles about Poulina Group
curl -X GET "http://localhost:8000/articles?ticker=POULINA&limit=5" | jq  
```

### Test 9: Generate Company Markdown Report

```bash
# By ticker symbol — downloads a .md file
curl -X GET "http://localhost:8000/report/BIAT" -o report_biat.md

# By full company name (URL-encoded spaces)
curl -X GET "http://localhost:8000/report/Poulina" -o report_poulina.md

# View the downloaded report
cat report_biat.md
```

**Expected Output (report_biat.md):**
```markdown
# 📊 Sentiment Report — BIAT

**Generated:** 2026-02-08 01:30 UTC

---

## Summary

| Metric | Value |
|--------|-------|
| Total articles analysed | **3** |
| Average sentiment score | **+0.650** |
| Overall sentiment | 🟢 **POSITIVE** |
| 🟢 Positive articles | 2 |
| 🔴 Negative articles | 0 |
| 🟡 Neutral articles | 1 |

---

## Articles Detail

### 1. La BIAT et la BAD signent une convention...

- **Source:** Tustex
- **Date:** 2026-02-08 01:25
- **Language:** fr
- **Sentiment:** 🟢 positive (+0.80)
- **URL:** [https://www.tustex.com/...]
```

### Test 10: Report for Unknown Company

```bash
curl -X GET "http://localhost:8000/report/UNKNOWN" | jq
```

**Expected Response:**
```json
{
  "detail": "Unknown company 'UNKNOWN'. Use a known ticker (SFBT, BIAT, BNA, SAH, CARTHAGE, POULINA, DELICE, EURO-CYCLES, TELNET, TUNISAIR) or full company name."
}
```

---

## 🎯 Tunisian Stock Tickers

The system recognizes these major BVMT companies:

| Ticker | Company Name |
|--------|-------------|
| **SFBT** | Société Frigorifique et Brasserie de Tunis |
| **BIAT** | Banque Internationale Arabe de Tunisie |
| **BNA** | Banque Nationale Agricole |
| **SAH** | Société d'Articles Hygiéniques |
| **CARTHAGE** | Ciments de Carthage |
| **POULINA** | Poulina Group Holding |
| **DELICE** | Délice Holding |
| **EURO-CYCLES** | Euro-Cycles |
| **TELNET** | Telnet Holding |
| **TUNISAIR** | Tunisair |

## 📰 News Sources

1. **IlBoursa.com** (French) - Financial news & market updates
2. **Tustex.com** (French) - Stock market analysis  
3. **TunisieNumerique.com** (Arabic) - General economy coverage

## ⚡ Performance Tips

- **Rate Limiting**: OpenRouter free tier allows ~20 requests/minute
- **Background Processing**: Scraping runs asynchronously to avoid blocking
- **Caching**: Articles are deduplicated by title to avoid re-processing
- **Error Handling**: If one news source fails, others continue working

## 🛠️ Advanced Testing

### Test LLM Analysis Directly

```python
# Test the LLM service in Python console
from app.services.llm import analyze_sentiment
import asyncio

async def test_llm():
    result = await analyze_sentiment(
        title="BIAT Bank Reports Strong Q4 Profits",
        snippet="The bank announced record earnings...",
        language="fr"
    )
    print(f"Sentiment: {result.sentiment}")
    print(f"Score: {result.score}")  
    print(f"Ticker: {result.ticker}")

# Run test
asyncio.run(test_llm())
```

### Test Scraper Directly

```python
# Test scraping without LLM analysis
from app.services.scraper import scrape_all_sources
import asyncio

async def test_scraper():
    result = await scrape_all_sources()
    print(f"Articles found: {len(result.articles)}")
    print(f"Errors: {result.errors}")
    for article in result.articles[:3]:
        print(f"- {article.source}: {article.title[:60]}...")

asyncio.run(test_scraper())
```

### Load Testing

```bash
# Test multiple concurrent requests
for i in {1..5}; do
  curl -X POST "http://localhost:8000/trigger-scrape" &
done
wait
```

## 🔧 Troubleshooting

### Common Issues

1. **"greenlet library required"** 
   ```bash
   pip install greenlet
   ```

2. **"OpenRouter API key invalid"**
   - Check your `.env` file
   - Verify key at https://openrouter.ai/keys

3. **"No articles scraped"**
   - News sites may be temporarily down
   - Check logs for HTTP errors
   - Some sites block automated requests

4. **Slow LLM responses**
   - Free tier has rate limits
   - Consider upgrading OpenRouter plan for production

### Debug Mode

Enable verbose logging:
```bash
# In .env file
DEBUG=true
```

This shows detailed scraping and database operations.

---

## 📈 Production Deployment

For production use:

1. **Database**: Switch to PostgreSQL for better performance
2. **API Key**: Use paid OpenRouter tier for higher rate limits  
3. **Caching**: Add Redis for article caching
4. **Monitoring**: Add health checks and alerting
5. **Scaling**: Deploy with Docker + Kubernetes

## 🤝 Contributing

This is a hackathon project optimized for rapid development. For improvements:

1. Add more Tunisian news sources
2. Enhance company name → ticker matching
3. Add real-time WebSocket updates
4. Implement historical sentiment tracking

---

**🏆 Built for IHEC Code Lab Hackathon - Team Makarouna Kadheba**