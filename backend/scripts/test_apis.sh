#!/bin/bash
# Comprehensive API Testing Script

echo "=================================================================================="
echo "🔍 CARTHAGE ALPHA - API Testing Suite"
echo "=================================================================================="
echo

BASE_URL="http://localhost:8000"

echo "1. Testing Health Endpoint"
echo "-------------------------------------------------------------------"
curl -s $BASE_URL/health | jq .
echo
echo

echo "2. Testing GET /api/stocks (List all stocks)"
echo "-------------------------------------------------------------------"
curl -s $BASE_URL/api/stocks | jq '. | length'
echo "   First 3 stocks:"
curl -s $BASE_URL/api/stocks | jq '.[0:3]'
echo
echo

echo "3. Testing GET /api/stocks/{ticker} (Get specific stock)"
echo "-------------------------------------------------------------------"
TICKER=$(curl -s $BASE_URL/api/stocks | jq -r '.[0].ticker')
echo "   Testing ticker: $TICKER"
curl -s $BASE_URL/api/stocks/$TICKER | jq '.'
echo
echo

echo "4. Testing GET /api/stocks/{ticker}/history (Historical prices)"
echo "-------------------------------------------------------------------"
curl -s "$BASE_URL/api/stocks/$TICKER/history?limit=5" | jq '.[-5:]'
echo
echo

echo "5. Testing GET /api/market/overview (Market overview)"
echo "-------------------------------------------------------------------"
curl -s $BASE_URL/api/market/overview | jq '.'
echo
echo

echo "6. Testing GET /api/sectors (Sector breakdown)"
echo "-------------------------------------------------------------------"
curl -s $BASE_URL/api/sectors | jq '.'
echo
echo

echo "7. Testing GET /api/predictions/{ticker} (ML predictions - placeholder)"
echo "-------------------------------------------------------------------"
curl -s $BASE_URL/api/predictions/$TICKER | jq '.'
echo
echo

echo "8. Testing GET /api/sentiment/{ticker} (Sentiment - placeholder)"
echo "-------------------------------------------------------------------"
curl -s $BASE_URL/api/sentiment/$TICKER | jq '.'
echo
echo

echo "9. Testing GET /api/anomalies (Anomalies list)"
echo "-------------------------------------------------------------------"
curl -s $BASE_URL/api/anomalies | jq '.'
echo
echo

echo "10. Testing POST /api/portfolio/optimize (Portfolio optimization)"
echo "-------------------------------------------------------------------"
curl -s -X POST $BASE_URL/api/portfolio/optimize \
  -H "Content-Type: application/json" \
  -d '{"risk_profile": "moderate", "amount": 10000}' | jq '.'
echo
echo

echo "=================================================================================="
echo "✅ API Testing Complete!"
echo "=================================================================================="
