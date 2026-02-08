"""
IMF DataMapper provider for Tunisian macro indicators.

API docs: https://www.imf.org/external/datamapper/api/v1/
No API key required.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://www.imf.org/external/datamapper/api/v1"

INDICATORS: dict[str, str] = {
    "gdp_growth":       "NGDP_RPCH",
    "inflation":        "PCPIPCH",
    "govt_debt_pct":    "GGXWDG_NGDP",
    "current_account":  "BCA_NGDPD",
    "unemployment":     "LUR",
}


def _year_range(start: int, end: int) -> str:
    return ",".join(str(y) for y in range(start, end + 1))


def fetch_indicator(
    code: str,
    country: str = "TUN",
    start_year: int = 2015,
    end_year: int = 2025,
) -> dict[str, float]:
    """Return ``{year: value}`` for one IMF indicator."""
    url = f"{_BASE}/{code}/{country}"
    params = {"periods": _year_range(start_year, end_year)}
    resp = httpx.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    try:
        return data["values"][code][country]
    except (KeyError, TypeError):
        return {}


def fetch_all(start_year: int = 2015, end_year: int = 2025) -> dict:
    """Fetch every indicator defined in *INDICATORS*."""
    result: dict[str, dict] = {}
    for name, code in INDICATORS.items():
        try:
            result[name] = fetch_indicator(code, start_year=start_year, end_year=end_year)
        except Exception as exc:
            logger.warning("IMF – %s failed: %s", name, exc)
            result[name] = {}
    return result
