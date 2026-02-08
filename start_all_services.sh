#!/bin/bash
# 🚀 Start All Carthage Alpha Services
# Usage: bash start_all_services.sh

echo "🚀 Starting Carthage Alpha Services..."
echo "======================================"

# Export database URL for all services
export DATABASE_URL="postgresql://neondb_owner:npg_bog2kaSA1DNZ@ep-shy-breeze-ag2f4327-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    lsof -i:$1 > /dev/null 2>&1
    return $?
}

# Kill existing services on ports
echo "${YELLOW}Cleaning up existing services...${NC}"
for port in 8000 8001 8002 8004 8005 8007; do
    if check_port $port; then
        echo "  Killing process on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
done

cd backend/services

# Start API Gateway (8000)
echo ""
echo "${GREEN}Starting API Gateway (8000)...${NC}"
cd api_gateway
python3 app.py > /tmp/api_gateway.log 2>&1 &
echo "  PID: $!"
cd ..
sleep 2

# Start Stock Service (8001)
echo "${GREEN}Starting Stock Service (8001)...${NC}"
cd stock_service
python3 app.py > /tmp/stock_service.log 2>&1 &
echo "  PID: $!"
cd ..
sleep 2

# Start Forecasting Service (8002)
echo "${GREEN}Starting Forecasting Service (8002)...${NC}"
cd forecasting
python3 main.py > /tmp/forecasting.log 2>&1 &
echo "  PID: $!"
cd ..
sleep 2

# Start Anomaly Detection (8004)
echo "${GREEN}Starting Anomaly Detection (8004)...${NC}"
cd anomaly_detection
python3 main.py > /tmp/anomaly.log 2>&1 &
echo "  PID: $!"
cd ..
sleep 2

# Start Sentiment Analysis (8005)
echo "${GREEN}Starting Sentiment Analysis (8005)...${NC}"
cd sentiment-analysis
python3 -m app.main > /tmp/sentiment.log 2>&1 &
echo "  PID: $!"
cd ..
sleep 2

# Start Portfolio Management (8007)
echo "${GREEN}Starting Portfolio Management (8007)...${NC}"
cd portfolio_management_service
python3 main.py > /tmp/portfolio.log 2>&1 &
echo "  PID: $!"
cd ..
sleep 3

echo ""
echo "======================================"
echo "${GREEN}✅ All services started!${NC}"
echo ""
echo "Service Status:"
echo "------------------------------------"

# Check each service
for port in 8000:API-Gateway 8001:Stock 8002:Forecasting 8004:Anomaly 8005:Sentiment 8007:Portfolio; do
    IFS=':' read -r p name <<< "$port"
    if check_port $p; then
        echo "  ${GREEN}✓${NC} $name (port $p)"
    else
        echo "  ${RED}✗${NC} $name (port $p) - FAILED"
    fi
done

echo ""
echo "Test services with:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8002/health"
echo "  curl http://localhost:8005/health"
echo ""
echo "View logs:"
echo "  tail -f /tmp/*.log"
echo ""
echo "Stop all services:"
echo "  bash stop_all_services.sh"
echo ""
