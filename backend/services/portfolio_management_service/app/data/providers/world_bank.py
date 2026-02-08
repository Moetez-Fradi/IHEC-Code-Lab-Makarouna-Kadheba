"""
World Bank Open Data provider for Tunisian macro indicators.

API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
No API key required.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://api.worldbank.org/v2/country/TUN/indicator"

INDICATORS: dict[str, str] = {
    "gdp_growth":       "NY.GDP.MKTP.KD.ZG",
    "inflation":        "FP.CPI.TOTL.ZG",
    "unemployment":     "SL.UEM.TOTL.ZS",
    "exchange_rate":    "PA.NUS.FCRF",
    "current_account":  "BN.CAB.XOKA.GD.ZS",
    "reserves":         "FI.RES.TOTL.CD",
    "gdp_usd":         "NY.GDP.MKTP.CD",
}


def fetch_indicator(
    code: str,
    start_year: int = 2015,
    end_year: int = 2025,
) -> dict[str, float | None]:
    """Return ``{year: value}`` for a single World Bank indicator."""
    url = f"{_BASE}/{code}"
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 100,
    }
    resp = httpx.get(url, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    if len(payload) < 2 or payload[1] is None:
        return {}

    return {
        entry["date"]: entry["value"]
        for entry in payload[1]
        if entry["value"] is not None
    }


def fetch_all(start_year: int = 2015, end_year: int = 2025) -> dict:
    """Fetch every indicator defined in *INDICATORS*."""
    result: dict[str, dict] = {}
    for name, code in INDICATORS.items():
        try:
            result[name] = fetch_indicator(code, start_year, end_year)
        except Exception as exc:
            logger.warning("World Bank – %s failed: %s", name, exc)
            result[name] = {}
    return result
