# 📁 Project Structure

```
bvmt-sentiment-analysis/
│
├── 📄 main.py                      # Application entry point
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment template
├── 📄 .gitignore                   # Git ignore rules
├── 📄 Dockerfile                   # Docker image definition
├── 📄 docker-compose.yml           # Docker Compose config
├── 📄 README.md                    # Main documentation
│
├── 📁 app/                         # Main application package
│   ├── 📄 __init__.py
│   │
│   ├── 📁 api/                     # API layer
│   │   ├── 📄 __init__.py
│   │   ├── 📄 app.py               # FastAPI application setup
│   │   └── 📄 endpoints.py         # API route handlers
│   │
│   ├── 📁 core/                    # Core configuration
│   │   ├── 📄 __init__.py
│   │   ├── 📄 config.py            # Settings and configuration
│   │   └── 📄 logger.py            # Logging setup
│   │
│   ├── 📁 models/                  # Data models
│   │   ├── 📄 __init__.py
│   │   └── 📄 schemas.py           # Pydantic models
│   │
│   ├── 📁 services/                # Business logic
│   │   ├── 📄 __init__.py
│   │   ├── 📄 model_service.py     # ML model management
│   │   └── 📄 ticker_service.py    # Ticker extraction
│   │
│   └── 📁 utils/                   # Utility functions (empty)
│
├── 📁 tests/                       # Test suite
│   ├── 📄 __init__.py
│   └── 📄 test_api.py              # API endpoint tests
│
├── 📁 scripts/                     # Utility scripts
│   └── 📄 start.sh                 # Startup script (Linux/macOS)
│
└── 📁 docs/                        # Documentation
    ├── 📄 QUICKSTART.md            # Quick start guide
    ├── 📄 INSTALLATION.md          # Detailed installation
    └── 📄 API_EXAMPLES.md          # API usage examples
```

## File Descriptions

### Root Level

| File | Purpose |
|------|---------|
| `main.py` | Entry point that starts the Uvicorn server |
| `requirements.txt` | Lists all Python package dependencies |
| `.env.example` | Template for environment configuration |
| `.gitignore` | Specifies intentionally untracked files |
| `Dockerfile` | Instructions for building Docker image |
| `docker-compose.yml` | Multi-container Docker setup |
| `README.md` | Comprehensive project documentation |

### Application Package (`app/`)

#### API Layer (`app/api/`)
- **`app.py`**: FastAPI application instance with lifespan management, CORS, and route registration
- **`endpoints.py`**: API route handlers for `/analyze`, `/health`, `/tickers`

#### Core (`app/core/`)
- **`config.py`**: Centralized configuration using Pydantic Settings (reads from `.env`)
- **`logger.py`**: Logging configuration and setup utilities

#### Models (`app/models/`)
- **`schemas.py`**: Pydantic models for request validation and response serialization
  - `SentimentRequest`
  - `SentimentResponse`
  - `HealthResponse`
  - `ErrorResponse`

#### Services (`app/services/`)
- **`model_service.py`**: ML model registry (Singleton pattern)
  - Loads and quantizes models
  - Manages model inference
  - Language detection
- **`ticker_service.py`**: Ticker symbol extraction and matching

### Tests (`tests/`)
- **`test_api.py`**: Comprehensive API testing script with examples

### Scripts (`scripts/`)
- **`start.sh`**: Automated startup script for Linux/macOS

### Documentation (`docs/`)
- **`QUICKSTART.md`**: 5-minute quick start guide
- **`INSTALLATION.md`**: Detailed step-by-step installation
- **`API_EXAMPLES.md`**: Code examples in multiple languages

## Architecture Flow

```
┌─────────────────────────────────────────────────┐
│                   main.py                       │
│            (Application Entry)                  │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│              app/api/app.py                     │
│          (FastAPI Application)                  │
│                                                 │
│  • Lifespan Management (Model Loading)         │
│  • CORS Middleware                              │
│  • Route Registration                           │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│           app/api/endpoints.py                  │
│             (Route Handlers)                    │
│                                                 │
│  • POST /api/v1/analyze                         │
│  • GET  /api/v1/health                          │
│  • GET  /api/v1/tickers                         │
└────────────┬──────────────┬─────────────────────┘
             │              │
             ▼              ▼
┌────────────────────┐  ┌──────────────────────┐
│ model_service.py   │  │ ticker_service.py    │
│                    │  │                      │
│ • ModelRegistry    │  │ • extract_ticker()   │
│ • load_models()    │  │ • get_ticker_info()  │
│ • quantization     │  │                      │
│ • inference        │  │                      │
└────────────────────┘  └──────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│        Quantized ML Models (INT8)               │
│                                                 │
│  • French: bardsai/finance-sentiment-fr-base    │
│  • Arabic: aubmindlab/bert-base-arabertv2       │
└─────────────────────────────────────────────────┘
```

## Data Flow

```
1. HTTP Request → 2. FastAPI Router → 3. Endpoint Handler
                                              │
                                              ▼
                                    4. Extract Ticker
                                              │
                                              ▼
                                    5. Model Inference
                                              │
                                              ▼
                                    6. Format Response
                                              │
                                              ▼
                                    7. HTTP Response
```

## Key Design Patterns

### 1. Singleton Pattern
- **Where**: `ModelRegistry` in `model_service.py`
- **Why**: Load models once, share across all requests
- **Benefit**: Reduced memory usage, faster response times

### 2. Dependency Injection
- **Where**: Services injected into endpoints
- **Why**: Loose coupling, easier testing
- **Benefit**: Maintainable, testable code

### 3. Configuration Management
- **Where**: `config.py` with Pydantic Settings
- **Why**: Centralized, type-safe configuration
- **Benefit**: Environment-based settings, validation

### 4. Lifespan Events
- **Where**: FastAPI lifespan context manager
- **Why**: Initialize resources at startup
- **Benefit**: Models loaded before first request

## Directory Purposes

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `app/api/` | HTTP layer, routing | `app.py`, `endpoints.py` |
| `app/core/` | Configuration, logging | `config.py`, `logger.py` |
| `app/models/` | Data validation | `schemas.py` |
| `app/services/` | Business logic | `model_service.py`, `ticker_service.py` |
| `tests/` | Testing | `test_api.py` |
| `scripts/` | Automation | `start.sh` |
| `docs/` | Documentation | `*.md` files |

## Configuration Files

| File | Format | Purpose |
|------|--------|---------|
| `.env` | Environment | Runtime configuration |
| `requirements.txt` | Text | Python dependencies |
| `Dockerfile` | Docker | Container image |
| `docker-compose.yml` | YAML | Multi-container setup |

## Important Notes

### Model Storage
- Models are cached in: `~/.cache/huggingface/`
- First download: ~800MB
- Persistent across runs

### Virtual Environment
- Location: `./venv/`
- Not committed to git
- Created per installation

### Logs
- Console output by default
- Can be redirected to files
- Configurable via `LOG_LEVEL` in `.env`

## Extending the Project

### Adding New Endpoints
1. Add route handler in `app/api/endpoints.py`
2. Create Pydantic models in `app/models/schemas.py`
3. Implement logic in `app/services/`

### Adding New Models
1. Update `app/core/config.py` with model name
2. Modify `app/services/model_service.py` to load new model
3. Update quantization logic if needed

### Adding New Tickers
1. Update `TICKER_KEYWORDS` in `app/core/config.py`
2. No code changes needed (data-driven)

---

This structure follows Python best practices and FastAPI conventions for clean, maintainable, production-ready code.