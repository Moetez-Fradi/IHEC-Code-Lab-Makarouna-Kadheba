#!/bin/bash
echo "=== 🚀 SYSTEM-WIDE MICROSERVICE CHECK ==="
echo "Date: $(date)"

check_service() {
    NAME=$1
    PORT=$2
    ENDPOINT=$3
    EXPECTED=$4
    
    echo -n "Checking $NAME (:$PORT)... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT$ENDPOINT)
    
    if [ "$HTTP_CODE" == "200" ]; then
        echo "✅ OK ($HTTP_CODE)"
        return 0
    else
        echo "❌ FAILED ($HTTP_CODE)"
        return 1
    fi
}

check_content() {
    NAME=$1
    PORT=$2
    ENDPOINT=$3
    JQ_FILTER=$4
    
    echo -n "   -> Verifying $NAME logic... "
    OUTPUT=$(curl -s http://localhost:$PORT$ENDPOINT)
    VAL=$(echo "$OUTPUT" | jq -r "$JQ_FILTER" 2>/dev/null)
    
    if [ -n "$VAL" ] && [ "$VAL" != "null" ]; then
        echo "✅ Data: $VAL"
    else
        echo "⚠️  WARN: No data or error (jq_filter: $JQ_FILTER)"
        echo "      Raw: ${OUTPUT:0:100}..."
    fi
}

# 1. API Gateway
check_service "API Gateway" 8000 "/health"
check_service "API Gateway" 8000 "/api/stocks" # Proxied

# 2. Stock Service
check_service "Stock Service" 8001 "/health"
check_content "Stock Service" 8001 "/stocks" ".[0].ticker"

# 3. Market Service
check_service "Market Service" 8002 "/health"
check_content "Market Service" 8002 "/overview" ".tunindex_value"

# 4. Notification Service
check_service "Notification" 8003 "/health"
check_content "Notification" 8003 "/test" ".status"

# 5. Anomaly Detection
check_service "Anomaly Det" 8004 "/health"
check_content "Anomaly Det" 8004 "/anomalies?code=ADWYA&start=2023-01-01&end=2023-12-31" ".code"

# 6. Sentiment Analysis
check_service "Sentiment" 8005 "/health" # Built-in via FastAPI?
# Sentiment router might not have /health, checking /docs or /articles
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8005/docs)
if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Sentiment Service (:$8005) is UP (Docs reachable)"
else
    echo "❌ Sentiment Service (:$8005) FAILED ($HTTP_CODE)"
fi

echo "=== 🏁 CHECK COMPLETE ==="
