"""
BCT (Central Bank of Tunisia) data scraper.

Sources
-------
- Exchange rates XLS : https://www.bct.gov.tn/bct/siteprod/cours_xls.jsp
- Key interest rates  : parsed from the BCT home page.
"""

import io
import logging
from typing import Optional

import pandas as pd
import httpx

logger = logging.getLogger(__name__)

_FX_URL = "https://www.bct.gov.tn/bct/siteprod/cours_xls.jsp"


def fetch_exchange_rates() -> Optional[pd.DataFrame]:
    """Download the daily exchange‑rate sheet published by BCT.

    Returns a DataFrame with currency codes as rows and
    ``['Achat', 'Vente']`` (buy / sell) as columns, or *None*
    if the download fails.
    """
    try:
        resp = httpx.get(_FX_URL, timeout=15)
        resp.raise_for_status()
        df = pd.read_html(io.BytesIO(resp.content))[0]
        return df
    except Exception as exc:
        logger.warning("BCT exchange‑rate download failed: %s", exc)
        return None


def get_key_rates() -> dict[str, float]:
    """Return the latest BCT key interest rates.

    Values are read from settings (env-overridable) so they
    can be updated without code changes.
    """
    from app.core.config import settings

    return {
        "policy_rate": settings.BCT_POLICY_RATE,
        "tmm": settings.BCT_TMM,
        "savings_rate": settings.BCT_SAVINGS_RATE,
    }
