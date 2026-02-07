# 🚀 Quick Start Guide

Get the BVMT Sentiment Analysis service running in **5 minutes**!

## Prerequisites Check

Before starting, ensure you have:

- [ ] Python 3.9+ installed (`python --version`)
- [ ] pip installed (`pip --version`)
- [ ] 4GB+ RAM available
- [ ] Internet connection (for first-time model download)

## Option 1: Automated Setup (Easiest) ⚡

```bash
# 1. Navigate to project directory
cd bvmt-sentiment-analysis

# 2. Run startup script
chmod +x scripts/start.sh
./scripts/start.sh

# That's it! The service will start automatically.
```

## Option 2: Manual Setup (5 Steps) 📝

### Step 1: Create Virtual Environment

```bash
python3 -m venv venv
```

### Step 2: Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
cp .env.example .env
```

### Step 5: Start the Service

```bash
python main.py
```

## Option 3: Docker (One Command) 🐳

```bash
docker-compose up -d
```

## Verify Installation ✅

### 1. Check Service is Running

Open your browser and visit: **http://localhost:8000**

You should see:
```json
{
  "service": "BVMT Sentiment Analysis Service",
  "version": "1.0.0",
  "optimization": "CPU-Quantized (INT8)",
  ...
}
```

### 2. Check Health Status

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "models_loaded": true,
  "cpu_optimized": true
}
```

### 3. Test Sentiment Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Les résultats sont excellents", "ticker": "SFBT"}'
```

Expected response:
```json
{
  "sentiment": "positive",
  "confidence": 0.92,
  "language": "french",
  "ticker": "SFBT"
}
```

## First-Time Setup Notes 📌

### Model Download

On first run, the service will download models (~800MB total):
- French model: ~400MB
- Arabic model: ~400MB

This happens automatically and takes 3-10 minutes depending on your internet speed.

**Progress indicators:**
```
Loading French model: bardsai/finance-sentiment-fr-base
Downloading tokenizer...
Downloading model...
✓ French model loaded and quantized successfully
```

### Startup Time

- **First run**: 3-10 minutes (model download + initialization)
- **Subsequent runs**: 30-60 seconds (model loading from cache)

## Common Issues & Fixes 🔧

### Issue: "Module not found"

**Fix:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"

**Fix:**
```bash
# Option 1: Kill the process
lsof -i :8000
kill -9 <PID>

# Option 2: Use different port
# Edit .env file:
PORT=8001
```

### Issue: "Out of memory"

**Fix:**
```bash
# Ensure quantization is enabled in .env:
USE_QUANTIZATION=True

# Close other applications to free RAM
```

### Issue: Service starts but models don't load

**Fix:**
```bash
# Check logs for errors
# Clear Hugging Face cache and retry
rm -rf ~/.cache/huggingface/transformers/
python main.py
```

## Next Steps 📚

1. **Explore API**: Visit http://localhost:8000/docs for interactive documentation
2. **Run Tests**: `python tests/test_api.py`
3. **Read Examples**: Check `docs/API_EXAMPLES.md`
4. **Customize**: Edit `.env` to configure settings

## Quick Command Reference 📋

```bash
# Start service
python main.py

# Run tests
python tests/test_api.py

# View API docs
open http://localhost:8000/docs

# Check health
curl http://localhost:8000/api/v1/health

# Analyze text
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here"}'

# Stop service
# Press Ctrl+C in terminal

# Deactivate virtual environment
deactivate
```

## Development Mode 🛠️

For development with auto-reload:

```bash
uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload
```

## Production Deployment 🚀

For production, use:

```bash
# With Docker
docker-compose up -d

# Or with Gunicorn (install first: pip install gunicorn)
gunicorn app.api.app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## Getting Help 💬

- Check `README.md` for detailed documentation
- Review `docs/API_EXAMPLES.md` for code examples
- Check logs for error messages
- Ensure all prerequisites are met

---

**Ready to analyze sentiment?** 🎉 Your service should be running at http://localhost:8000