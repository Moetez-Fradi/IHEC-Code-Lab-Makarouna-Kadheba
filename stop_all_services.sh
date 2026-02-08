#!/bin/bash
# 🛑 Stop All Carthage Alpha Services

echo "🛑 Stopping all Carthage Alpha services..."

# Stop processes on service ports
for port in 8000 8001 8002 8004 8005 8007; do
    if lsof -i:$port > /dev/null 2>&1; then
        echo "  Stopping service on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null
    fi
done

echo "✅ All services stopped"
