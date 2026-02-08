"""
Aggregate macro data from every provider into one flat dict
that the rest of the service can consume.
"""

import logging

from app.data.providers import bct, imf, world_bank

logger = logging.getLogger(__name__)


def _latest(series: dict) -> float | None:
    """Return the most recent non-null value from a ``{year: val}`` dict."""
    for year in sorted(series, reverse=True):
        if series[year] is not None:
            return float(series[year])
    return None


def fetch_macro_snapshot() -> dict[str, float]:
    """Build a single dict of the latest Tunisian macro figures.

    Tries World Bank first, fills gaps with IMF, and always
    adds BCT interest rates / exchange data.
    """
    wb = world_bank.fetch_all()
    imf_data = imf.fetch_all()

    snapshot: dict[str, float] = {}

    # GDP growth – prefer World Bank, fallback IMF
    snapshot["gdp_growth"] = (
        _latest(wb.get("gdp_growth", {}))
        or _latest(imf_data.get("gdp_growth", {}))
        or 0.0
    )

    snapshot["inflation"] = (
        _latest(wb.get("inflation", {}))
        or _latest(imf_data.get("inflation", {}))
        or 0.0
    )

    snapshot["unemployment"] = (
        _latest(wb.get("unemployment", {}))
        or _latest(imf_data.get("unemployment", {}))
        or 0.0
    )

    snapshot["exchange_rate_usd"] = _latest(wb.get("exchange_rate", {})) or 3.1  # TND/USD approx fallback
    snapshot["current_account"] = (
        _latest(wb.get("current_account", {}))
        or _latest(imf_data.get("current_account", {}))
        or 0.0
    )
    snapshot["reserves_usd"] = _latest(wb.get("reserves", {})) or 0.0
    snapshot["govt_debt_pct"] = _latest(imf_data.get("govt_debt_pct", {})) or 0.0

    # BCT rates
    rates = bct.get_key_rates()
    snapshot["policy_rate"] = rates["policy_rate"]
    snapshot["tmm"] = rates["tmm"]

    logger.info("Macro snapshot: %s", snapshot)
    return snapshot
