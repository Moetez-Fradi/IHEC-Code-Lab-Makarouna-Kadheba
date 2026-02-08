#!/bin/bash
set -e

cd /home/fantazy/Downloads/hackathon\ ihec/IHEC-Code-Lab-Makarouna-Kadheba/backend/services

echo "🔧 Setting up Forecasting Service (Port 8008)..."
cd forecasting
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --quiet -r requirements.txt
else
    source venv/bin/activate
fi
PORT=8008 nohup python -m uvicorn main:app --host 0.0.0.0 --port 8008 > /tmp/forecasting.log 2>&1 &
echo "✅ Forecasting Service started on port 8008"
cd ..

echo ""
echo "🔧 Setting up Portfolio Management Service (Port 8007)..."
cd portfolio_management_service
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --quiet -r requirements.txt
else
    source venv/bin/activate
fi
nohup python main.py > /tmp/portfolio_management.log 2>&1 &
echo "✅ Portfolio Management Service started on port 8007"
cd ..

sleep 3
echo ""
echo "🎯 Services Status:"
echo "Port 8007 (Portfolio):" $(ss -tln | grep :8007 | wc -l) "listeners"
echo "Port 8008 (Forecasting):" $(ss -tln | grep :8008 | wc -l) "listeners"
