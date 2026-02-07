"""
Test Script for BVMT Sentiment Analysis API
Run this script to test all API endpoints
"""

import requests
import json
from typing import Dict


BASE_URL = "http://localhost:8000"


def print_response(endpoint: str, response: requests.Response):
    """Pretty print API response."""
    print(f"\n{'='*70}")
    print(f"Endpoint: {endpoint}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print(f"{'='*70}")


def test_root():
    """Test root endpoint."""
    response = requests.get(f"{BASE_URL}/")
    print_response("GET /", response)


def test_ping():
    """Test ping endpoint."""
    response = requests.get(f"{BASE_URL}/ping")
    print_response("GET /ping", response)


def test_health():
    """Test health check endpoint."""
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print_response("GET /api/v1/health", response)


def test_tickers():
    """Test tickers list endpoint."""
    response = requests.get(f"{BASE_URL}/api/v1/tickers")
    print_response("GET /api/v1/tickers", response)


def test_analyze_french():
    """Test sentiment analysis with French text."""
    payload = {
        "text": "Les résultats financiers de SFBT sont excellents ce trimestre. Les revenus ont augmenté de 25%.",
        "ticker": "SFBT"
    }
    response = requests.post(f"{BASE_URL}/api/v1/analyze", json=payload)
    print_response("POST /api/v1/analyze (French)", response)


def test_analyze_french_negative():
    """Test sentiment analysis with negative French text."""
    payload = {
        "text": "Les actions de SAH ont chuté drastiquement. La situation financière est préoccupante.",
        "ticker": "SAH"
    }
    response = requests.post(f"{BASE_URL}/api/v1/analyze", json=payload)
    print_response("POST /api/v1/analyze (French - Negative)", response)


def test_analyze_arabic():
    """Test sentiment analysis with Arabic text."""
    payload = {
        "text": "النتائج المالية ممتازة والأرباح في تزايد مستمر",
    }
    response = requests.post(f"{BASE_URL}/api/v1/analyze", json=payload)
    print_response("POST /api/v1/analyze (Arabic)", response)


def test_analyze_without_ticker():
    """Test sentiment analysis without ticker."""
    payload = {
        "text": "Le marché boursier tunisien montre des signes de reprise positive."
    }
    response = requests.post(f"{BASE_URL}/api/v1/analyze", json=payload)
    print_response("POST /api/v1/analyze (No Ticker)", response)


def run_all_tests():
    """Run all API tests."""
    print("\n" + "="*70)
    print("BVMT SENTIMENT ANALYSIS API - TEST SUITE")
    print("="*70)
    
    try:
        test_root()
        test_ping()
        test_health()
        test_tickers()
        test_analyze_french()
        test_analyze_french_negative()
        test_analyze_arabic()
        test_analyze_without_ticker()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS COMPLETED")
        print("="*70 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the API.")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    run_all_tests()