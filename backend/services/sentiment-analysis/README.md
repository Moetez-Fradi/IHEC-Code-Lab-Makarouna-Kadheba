# 🏦 BVMT Sentiment Analysis Module

A lightweight, hackathon-ready sentiment analysis system for the **Tunis Stock Exchange (BVMT)** built with FastAPI and OpenRouter LLM integration.

## 🚀 Features

- **Multilingual Support**: Handles French, Arabic, and Tunisian dialect seamlessly
- **Real-time Scraping**: Monitors 3 Tunisian financial news sources
- **LLM Analysis**: Uses DeepSeek R1 Chimera via OpenRouter (free tier)
- **Ticker Detection**: Automatically identifies mentioned Tunisian companies
- **Daily Aggregation**: Computes sentiment scores per ticker
- **Markdown Reports**: Generate downloadable per-company sentiment reports
- **SQLite Storage**: Lightweight database with async support

## 📁 Project Structure

```
/app
├── main.py            # FastAPI entry point
├── config.py          # Settings (OpenRouter Key, Ticker List)  
├── database.py        # SQLite setup & ORM models
├── services/
│   ├── scraper.py     # News scraping from 3 Tunisian sources
│   ├── llm.py         # OpenRouter/DeepSeek integration
│   └── aggregator.py  # Daily sentiment score calculation
└── routers/
    └── sentiment.py   # API endpoints (scrape, articles, daily, report)
```

## 🏃‍♂️ Quick Start

### 1. Setup Environment

```bash
# Clone and navigate
cd backend/services/sentiment-analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `.env` file with your OpenRouter API key:

```bash
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