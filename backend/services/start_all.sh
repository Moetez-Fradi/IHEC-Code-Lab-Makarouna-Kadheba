#!/bin/bash
echo "🚀 Starting all microservices..."

# API Gateway (8000)
cd api_gateway
source venv/bin/activate
uvicorn app:app --port 8000 > /tmp/api_gateway.log 2>&1 &
echo "✅ API Gateway started (port 8000)"
cd ..

# Stock Service (8001)
cd stock_service
source venv/bin/activate
uvicorn app:app --port 8001 > /tmp/stock_service.log 2>&1 &
echo "✅ Stock Service started (port 8001)"
cd ..

# Market Service (8002)
cd market_service
source venv/bin/activate
uvicorn app:app --port 8002 > /tmp/market_service.log 2>&1 &
echo "✅ Market Service started (port 8002)"
cd ..

# Notification Service (8003)
cd notification_service
source venv/bin/activate
uvicorn app:app --port 8003 > /tmp/notification_service.log 2>&1 &
echo "✅ Notification Service started (port 8003)"
cd ..

# Anomaly Detection (8004)
cd anomaly_detection
source venv/bin/activate
uvicorn app:app --port 8004 > /tmp/anomaly_detection.log 2>&1 &
echo "✅ Anomaly Detection started (port 8004)"
cd ..

# Sentiment Analysis (8005)
cd sentiment-analysis
source venv/bin/activate
uvicorn app.main:app --port 8005 > /tmp/sentiment_analysis.log 2>&1 &
echo "✅ Sentiment Analysis started (port 8005)"
cd ..

# Portfolio Service (8007)
cd portfolio_service
source venv/bin/activate
uvicorn app:app --port 8007 > /tmp/portfolio_service.log 2>&1 &
echo "✅ Portfolio Service started (port 8007)"
cd ..

sleep 3
echo "✨ All services started!"
echo "📊 Check logs in /tmp/*.log"
