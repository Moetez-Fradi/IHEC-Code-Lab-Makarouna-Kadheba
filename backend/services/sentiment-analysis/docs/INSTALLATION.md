# 📖 Complete Installation & Setup Guide

This guide walks you through every step of installing and running the BVMT Sentiment Analysis service.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Step-by-Step Installation](#step-by-step-installation)
4. [Configuration](#configuration)
5. [Running the Service](#running-the-service)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **CPU**: Any modern processor (Intel/AMD x64, Apple Silicon)
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 5GB free space
- **Python**: 3.9 or higher
- **Internet**: Required for initial model download

### Operating System
- ✅ Linux (Ubuntu 20.04+, Debian 10+, CentOS 8+)
- ✅ macOS (10.15+)
- ✅ Windows (10/11)

### Software Dependencies
- Python 3.9+
- pip (Python package manager)
- git (optional, for cloning)

---

## Installation Methods

Choose one of the following methods:

| Method | Difficulty | Setup Time | Best For |
|--------|-----------|------------|----------|
| **Automated Script** | ⭐ Easy | 5 min | Quick start |
| **Manual Installation** | ⭐⭐ Medium | 10 min | Learning/Customization |
| **Docker** | ⭐⭐⭐ Advanced | 5 min | Production |

---

## Step-by-Step Installation

### Method 1: Automated Script (Recommended for Beginners)

#### For Linux/macOS:

```bash
# 1. Navigate to project directory
cd bvmt-sentiment-analysis

# 2. Make script executable
chmod +x scripts/start.sh

# 3. Run the script
./scripts/start.sh
```

The script will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create .env configuration
- ✅ Start the service

**Expected Output:**
```
==========================================
BVMT Sentiment Analysis Service
==========================================

Creating virtual environment...
Activating virtual environment...
Installing dependencies...
Successfully installed fastapi-0.109.0 ...

==========================================
Starting BVMT Sentiment Analysis Service
==========================================

INFO: Loading French model: bardsai/finance-sentiment-fr-base
INFO: ✓ French model loaded and quantized successfully
INFO: Loading Arabic model: aubmindlab/bert-base-arabertv2
INFO: ✓ Arabic model loaded and quantized successfully
INFO: ALL MODELS LOADED - SERVICE READY FOR INFERENCE
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

### Method 2: Manual Installation (Step-by-Step)

#### Step 1: Verify Python Installation

```bash
# Check Python version (must be 3.9+)
python3 --version
# or
python --version
```

**Expected output:** `Python 3.9.x` or higher

If Python is not installed:
- **Ubuntu/Debian**: `sudo apt install python3 python3-pip python3-venv`
- **macOS**: `brew install python@3.9`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

#### Step 2: Navigate to Project Directory

```bash
cd bvmt-sentiment-analysis
```

#### Step 3: Create Virtual Environment

**Why?** Isolates project dependencies from system Python.

```bash
python3 -m venv venv
```

**Expected output:**
```
Creating virtual environment...
```

**Troubleshooting:**
- If `venv` module not found: `sudo apt install python3-venv` (Ubuntu/Debian)

#### Step 4: Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Verification:**
Your prompt should change to show `(venv)`:
```
(venv) user@machine:~/bvmt-sentiment-analysis$
```

#### Step 5: Upgrade pip

```bash
pip install --upgrade pip
```

**Expected output:**
```
Successfully installed pip-24.0
```

#### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Collecting fastapi==0.109.0
Downloading fastapi-0.109.0-py3-none-any.whl (92 kB)
...
Successfully installed fastapi-0.109.0 torch-2.1.2 transformers-4.36.2 ...
```

**This will install:**
- FastAPI (web framework)
- PyTorch (ML framework)
- Transformers (Hugging Face models)
- Other dependencies

**Installation time:** 2-5 minutes depending on internet speed

#### Step 7: Create Configuration File

```bash
cp .env.example .env
```

**Verify:**
```bash
cat .env
```

**You should see:**
```env
APP_NAME=BVMT Sentiment Analysis Service
VERSION=1.0.0
DEBUG=False
LOG_LEVEL=INFO
...
```

#### Step 8: Start the Service

```bash
python main.py
```

**First-time startup sequence:**

```
==========================================
Starting BVMT Sentiment Analysis Service v1.0.0
==========================================
INFO: Application startup: Loading models...
======================================================================
INITIALIZING CPU-OPTIMIZED SENTIMENT ANALYSIS MODELS
======================================================================
INFO: Loading French model: bardsai/finance-sentiment-fr-base
Downloading (…)okenizer_config.json: 100%|████████| 48/48 [00:00<00:00, 1.2kB/s]
Downloading (…)lve/main/config.json: 100%|████████| 743/743 [00:00<00:00, 2.1kB/s]
Downloading (…)/main/pytorch_model.bin: 100%|█| 436M/436M [02:15<00:00, 3.2MB/s]
INFO: Applying dynamic quantization to French model (INT8)...
INFO: ✓ French model loaded and quantized successfully
INFO: Loading Arabic model: aubmindlab/bert-base-arabertv2
Downloading (…)lve/main/config.json: 100%|████████| 691/691 [00:00<00:00, 1.9kB/s]
Downloading (…)/main/pytorch_model.bin: 100%|█| 543M/543M [02:45<00:00, 3.3MB/s]
INFO: Applying dynamic quantization to Arabic model (INT8)...
INFO: ✓ Arabic model loaded and quantized successfully
======================================================================
ALL MODELS LOADED - SERVICE READY FOR INFERENCE
======================================================================
INFO: ✓ Application startup complete
INFO: Started server process [12345]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Note:** First-time model download takes 3-10 minutes. Subsequent runs are much faster (30-60 seconds).

---

### Method 3: Docker Installation

#### Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)

#### Quick Start

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker ps
```

#### Manual Docker Build

```bash
# Build image
docker build -t bvmt-sentiment-api .

# Run container
docker run -d \
  -p 8000:8000 \
  --name bvmt-sentiment \
  -e USE_QUANTIZATION=True \
  bvmt-sentiment-api

# View logs
docker logs -f bvmt-sentiment

# Stop container
docker stop bvmt-sentiment

# Remove container
docker rm bvmt-sentiment
```

---

## Configuration

### Environment Variables

Edit `.env` file to customize:

```env
# Server settings
HOST=0.0.0.0          # Listen on all interfaces
PORT=8000              # Service port

# Application settings
DEBUG=False            # Set to True for development
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR

# Model settings
USE_QUANTIZATION=True  # CPU optimization (recommended)
MAX_SEQUENCE_LENGTH=512

# Force CPU usage
CUDA_VISIBLE_DEVICES=  # Leave empty to disable GPU
```

### Custom Ticker Configuration

To add more tickers, edit `app/core/config.py`:

```python
TICKER_KEYWORDS: dict = {
    "SFBT": ["SFBT", "Boissons"],
    "SAH": ["Lilas", "SAH"],
    "YOUR_TICKER": ["Keyword1", "Keyword2"]  # Add here
}
```

---

## Running the Service

### Development Mode

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Start with auto-reload
uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode

```bash
# Using main.py
python main.py

# Or with Gunicorn (install first)
pip install gunicorn
gunicorn app.api.app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Background Service (Linux)

Create systemd service file `/etc/systemd/system/bvmt-sentiment.service`:

```ini
[Unit]
Description=BVMT Sentiment Analysis Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/bvmt-sentiment-analysis
Environment="PATH=/path/to/bvmt-sentiment-analysis/venv/bin"
ExecStart=/path/to/bvmt-sentiment-analysis/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl start bvmt-sentiment
sudo systemctl enable bvmt-sentiment
sudo systemctl status bvmt-sentiment
```

---

## Verification

### 1. Check Service is Running

**Browser:** Open http://localhost:8000

**Command line:**
```bash
curl http://localhost:8000
```

**Expected response:**
```json
{
  "service": "BVMT Sentiment Analysis Service",
  "version": "1.0.0",
  "optimization": "CPU-Quantized (INT8)",
  "supported_languages": ["French", "Arabic"],
  "supported_tickers": ["SFBT", "SAH"]
}
```

### 2. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "french_model": "bardsai/finance-sentiment-fr-base",
  "arabic_model": "aubmindlab/bert-base-arabertv2",
  "cpu_optimized": true,
  "version": "1.0.0"
}
```

### 3. Test Sentiment Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Les résultats sont excellents", "ticker": "SFBT"}'
```

**Expected response:**
```json
{
  "sentiment": "positive",
  "confidence": 0.92,
  "scores": {
    "negative": 0.02,
    "neutral": 0.06,
    "positive": 0.92
  },
  "language": "french",
  "ticker": "SFBT",
  "ticker_keywords_found": ["SFBT"]
}
```

### 4. Run Test Suite

```bash
# Ensure service is running, then:
python tests/test_api.py
```

**Expected output:**
```
======================================================================
BVMT SENTIMENT ANALYSIS API - TEST SUITE
======================================================================

======================================================================
Endpoint: GET /
Status Code: 200
...
======================================================================
✓ ALL TESTS COMPLETED
======================================================================
```

---

## Troubleshooting

### Common Issues

#### 1. Python Version Error

**Error:** `Python 3.9 or higher required`

**Solution:**
```bash
# Check version
python3 --version

# Install Python 3.9+
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.9

# macOS:
brew install python@3.9
```

#### 2. pip Not Found

**Error:** `pip: command not found`

**Solution:**
```bash
# Ubuntu/Debian:
sudo apt install python3-pip

# macOS:
python3 -m ensurepip --upgrade

# Windows:
# Reinstall Python with "Add to PATH" option checked
```

#### 3. Virtual Environment Activation Fails (Windows PowerShell)

**Error:** `cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
venv\Scripts\Activate.ps1
```

#### 4. Dependency Installation Fails

**Error:** `Failed building wheel for torch`

**Solution:**
```bash
# Update pip
pip install --upgrade pip setuptools wheel

# Retry installation
pip install -r requirements.txt
```

#### 5. Out of Memory During Model Loading

**Error:** `RuntimeError: [enforce fail at alloc_cpu.cpp:...]`

**Solution:**
- Ensure quantization is enabled: `USE_QUANTIZATION=True` in `.env`
- Close other applications
- Minimum 4GB RAM required (8GB recommended)

#### 6. Port Already in Use

**Error:** `[Errno 48] Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Or change port in .env
PORT=8001
```

#### 7. Models Not Loading

**Error:** Service starts but models don't load

**Solution:**
```bash
# Clear cache
rm -rf ~/.cache/huggingface/

# Check internet connection
ping huggingface.co

# Retry
python main.py
```

#### 8. Import Errors

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Next Steps

✅ Service is running → Explore the [API Documentation](http://localhost:8000/docs)
✅ Want to integrate? → Check [API Examples](API_EXAMPLES.md)
✅ Need help? → Read the full [README](../README.md)

---

**Congratulations!** 🎉 Your BVMT Sentiment Analysis service is ready to use.