# API Usage Examples

## Python Examples

### Basic Sentiment Analysis

```python
import requests

# Analyze French text
response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={
        "text": "Les résultats de SFBT sont excellents ce trimestre",
        "ticker": "SFBT"
    }
)

result = response.json()
print(f"Sentiment: {result['sentiment']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Ticker: {result['ticker']}")
```

### Batch Processing

```python
import requests

texts = [
    {"text": "Les actions de SAH montent fortement", "ticker": "SAH"},
    {"text": "Résultats décevants pour le marché", "ticker": None},
    {"text": "SFBT annonce une croissance record", "ticker": "SFBT"},
]

for item in texts:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze",
        json=item
    )
    result = response.json()
    print(f"Text: {item['text'][:50]}...")
    print(f"Sentiment: {result['sentiment']} ({result['confidence']:.2%})")
    print("-" * 50)
```

### Error Handling

```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze",
        json={"text": "Sample text"},
        timeout=30
    )
    response.raise_for_status()
    result = response.json()
    print(result)
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## JavaScript/Node.js Examples

### Using Fetch API

```javascript
async function analyzeSentiment(text, ticker = null) {
    try {
        const response = await fetch('http://localhost:8000/api/v1/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text, ticker })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Sentiment:', result.sentiment);
        console.log('Confidence:', result.confidence);
        return result;
    } catch (error) {
        console.error('Error:', error);
    }
}

// Usage
analyzeSentiment("Les résultats sont excellents", "SFBT");
```

### Using Axios

```javascript
const axios = require('axios');

async function analyzeSentiment(text, ticker = null) {
    try {
        const response = await axios.post('http://localhost:8000/api/v1/analyze', {
            text: text,
            ticker: ticker
        });
        
        console.log('Result:', response.data);
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

// Usage
analyzeSentiment("Les résultats de SFBT sont excellents", "SFBT");
```

## cURL Examples

### Analyze Sentiment

```bash
# French text with ticker
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Les résultats financiers de SFBT sont excellents",
    "ticker": "SFBT"
  }'

# Arabic text
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "النتائج المالية ممتازة والأرباح في تزايد مستمر"
  }'

# Without ticker
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Le marché boursier montre des signes positifs"
  }'
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### List Tickers

```bash
curl http://localhost:8000/api/v1/tickers
```

## Postman Collection

### Setup

1. Open Postman
2. Create new collection "BVMT Sentiment Analysis"
3. Add environment variable: `base_url = http://localhost:8000`

### Requests

#### Analyze Sentiment (POST)

```
URL: {{base_url}}/api/v1/analyze
Method: POST
Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "text": "Les résultats de SFBT sont excellents",
  "ticker": "SFBT"
}
```

#### Health Check (GET)

```
URL: {{base_url}}/api/v1/health
Method: GET
```

## Response Examples

### Positive Sentiment

```json
{
  "sentiment": "positive",
  "confidence": 0.94,
  "scores": {
    "negative": 0.01,
    "neutral": 0.05,
    "positive": 0.94
  },
  "language": "french",
  "ticker": "SFBT",
  "ticker_keywords_found": ["SFBT"]
}
```

### Negative Sentiment

```json
{
  "sentiment": "negative",
  "confidence": 0.88,
  "scores": {
    "negative": 0.88,
    "neutral": 0.08,
    "positive": 0.04
  },
  "language": "french",
  "ticker": "SAH",
  "ticker_keywords_found": ["SAH", "Lilas"]
}
```

### Arabic Text

```json
{
  "sentiment": "positive",
  "confidence": 0.91,
  "scores": {
    "negative": 0.02,
    "neutral": 0.07,
    "positive": 0.91
  },
  "language": "arabic",
  "ticker": null,
  "ticker_keywords_found": []
}
```

## Integration Examples

### Flask App

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
SENTIMENT_API = "http://localhost:8000/api/v1/analyze"

@app.route('/process-news', methods=['POST'])
def process_news():
    data = request.json
    
    # Call sentiment API
    response = requests.post(SENTIMENT_API, json=data)
    sentiment_result = response.json()
    
    # Process and return
    return jsonify({
        "original_text": data["text"],
        "analysis": sentiment_result
    })

if __name__ == '__main__':
    app.run(port=5000)
```

### Streamlit Dashboard

```python
import streamlit as st
import requests

st.title("BVMT Sentiment Analyzer")

text = st.text_area("Enter text to analyze:")
ticker = st.selectbox("Select Ticker", ["None", "SFBT", "SAH"])

if st.button("Analyze"):
    if text:
        response = requests.post(
            "http://localhost:8000/api/v1/analyze",
            json={
                "text": text,
                "ticker": None if ticker == "None" else ticker
            }
        )
        result = response.json()
        
        st.subheader("Results")
        st.metric("Sentiment", result["sentiment"])
        st.metric("Confidence", f"{result['confidence']:.2%}")
        
        st.bar_chart({
            "Negative": result["scores"]["negative"],
            "Neutral": result["scores"]["neutral"],
            "Positive": result["scores"]["positive"]
        })
```