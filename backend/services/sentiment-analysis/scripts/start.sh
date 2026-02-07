#!/bin/bash

# BVMT Sentiment Analysis - Startup Script
# This script sets up and starts the sentiment analysis service

set -e

echo "=========================================="
echo "BVMT Sentiment Analysis Service"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Start the service
echo ""
echo "=========================================="
echo "Starting BVMT Sentiment Analysis Service"
echo "=========================================="
echo ""

python main.py