# Forecasting Service — Module 1 (Prévision: prix & liquidité)

End-to-end probabilistic forecasting for BVMT securities covering **price quantiles**, **liquidity regime**, **transfer learning**, **synthetic augmentation**, **explainability**, and **execution triggers**.

## Architecture

```
forecasting/
├── .gitignore               # Python / model / data ignores
├── .dockerignore            # Docker build exclusions
├── .env.example             # Environment variable template
├── Dockerfile               # Container image
├── requirements.txt         # All dependencies (prod + test)
├── README.md
├── __init__.py
├── main.py                  # FastAPI app entrypoint
├── routes.py                # API router (5 endpoints)
├── schemas.py               # Pydantic request / response models
├── service.py               # Orchestrator wiring all sub-modules
├── explainers.py            # SHAP + confidence intervals
├── execution_trigger.py     # Combined price+liquidity signal engine
├── models/
│   ├── __init__.py
│   ├── quantile_forecaster.py   # Transformer/LSTM quantile regression
│   ├── liquidity_model.py       # Hybrid price-direction + liquidity
│   ├── transfer_learner.py      # Cross-market pre-train / fine-tune
│   └── synthetic_augmenter.py   # GAN / TS-VAE augmentation
└── tests/
    ├── __init__.py
    ├── conftest.py              # Shared fixtures
    ├── test_quantile_forecaster.py
    ├── test_liquidity_model.py
    ├── test_transfer_learner.py
    ├── test_synthetic_augmenter.py
    ├── test_explainers.py
    ├── test_execution_trigger.py
    ├── test_service.py
    ├── test_schemas.py
    └── test_api_routes.py
```

## Sub-module Mapping

| Spec Requirement | Module |
|---|---|
| Forecast probabiliste (p10/p50/p90, 1–5j) | `models/quantile_forecaster.py` |
| Hybrid price + microliquidity model | `models/liquidity_model.py` |
| Transfer learning cross-list / secteurs | `models/transfer_learner.py` |
| Augmentation synthétique (GANs/TS-VAE) | `models/synthetic_augmenter.py` |
| Forecast explainers (SHAP + CI) | `explainers.py` |
| Trigger d’exécution (timing) | `execution_trigger.py` |

## API Endpoints

### `POST /api/forecasting/forecast`
Multi-horizon quantile forecast (p10/p50/p90) + liquidity regime.

**Request:**
```json
{
  "security_id": "BIAT",
  "date": "2026-02-08",
  "ohlcv": {"open": 100, "high": 102, "low": 99, "close": 101, "volume": 5000},
  "order_book": {"spread": 0.5, "depth": 12000, "imbalance": 0.1},
  "horizon": 3,
  "history": [98, 99, 100, 101, 100, 99, 100, 101, 102, 101, ...]
}
```

**Response:** quantiles array (per day), liquidity/direction probs.

### `POST /api/forecasting/explain`
SHAP values, confidence intervals, top forecast drivers.

### `POST /api/forecasting/recommend`
Execution signal: `enter` / `exit` / `hold` / `defer` + timing.

### `POST /api/forecasting/augment`
Generate synthetic price series for illiquid securities.

**Request:**
```json
{
  "security_id": "SOTUMAG",
  "price_history": [45.2, 45.5, 44.8, ...],
  "n_synthetic": 10,
  "method": "vae"
}
```

### `POST /api/forecasting/transfer-learn`
Pre-train on cross-market corpus then fine-tune on a BVMT ticker.

**Request:**
```json
{
  "target_security_id": "SOTUMAG",
  "target_prices": [45.2, 45.5, ...],
  "source_corpus": {
    "BIAT": [100, 101, 102, ...],
    "BH":   [20, 20.5, 21, ...]
  }
}
```

## Setup

```bash
# Create venv & install everything
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy env template
cp .env.example .env
```

## Running the Service

```bash
uvicorn backend.services.forecasting.main:app --reload
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Running Tests

```bash
python -m pytest backend/services/forecasting/tests/ -v
```

## Docker

```bash
docker build -t forecasting-service .
docker run --rm -p 8000:8000 --env-file .env forecasting-service
```

## Production Notes

- All models currently use **numpy-only reference implementations** (GBM quantiles, heuristic classifiers, simple VAE/GAN stubs).
- To upgrade, replace the `_predict` / `fit` internals with PyTorch / TensorFlow models behind the same interface — **no API changes needed**.
- Add authentication, rate limiting, async workers, and persistent model storage as required.
