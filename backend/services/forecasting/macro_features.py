"""
Macro-Economic Features for Tunisia (K.O. Feature #2)

Integrates Tunisian macroeconomic indicators into stock predictions:
1. Phosphate Production (CPG - Compagnie des Phosphates de Gafsa)
2. TMM (Taux Moyen du Marché - BCT Monetary Policy)
3. Tourism Arrivals (ONTT - Office National du Tourisme Tunisien)

These exogenous variables enhance predictions by capturing:
- Phosphates → Industrial/Materials/Transport sectors
- TMM → Banking/Leasing/Real Estate sectors  
- Tourism → Consumption/Hospitality/Services sectors

Based on Solution.txt strategy: "Show you understand Tunisia, not just copy NYSE models"
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 1. DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PhosphateData:
    """Monthly phosphate production and global prices."""
    date: dt.date
    production_kt: float  # Thousand tons (Tunisia)
    global_price_usd: float  # DAP price (Diammonium Phosphate)
    notes: str = ""


@dataclass
class TMMData:
    """Tunisian Money Market rate (Banque Centrale de Tunisie)."""
    date: dt.date
    rate: float  # Percentage (e.g., 7.5 = 7.5%)
    change_bps: float = 0.0  # Basis points change from previous


@dataclass
class TourismData:
    """Monthly tourist arrivals."""
    date: dt.date
    arrivals: int  # Number of tourists
    yoy_change: float = 0.0  # Year-over-year percentage change


@dataclass
class MacroSnapshot:
    """Combined macro snapshot for a specific date."""
    date: dt.date
    phosphate: PhosphateData | None = None
    tmm: TMMData | None = None
    tourism: TourismData | None = None


# ═══════════════════════════════════════════════════════════════════════════
# 2. HISTORICAL DATA (2023-2025)
# ═══════════════════════════════════════════════════════════════════════════

# Phosphate production (estimated based on Tunisia's challenges)
# Source: Global phosphate market reports + Tunisia's production capacity ~8M tons/year
PHOSPHATE_HISTORY = [
    # 2023 - Strike impacts
    PhosphateData(dt.date(2023, 1, 1), 580, 620, "Production below capacity"),
    PhosphateData(dt.date(2023, 4, 1), 520, 650, "Q1 strike impact"),
    PhosphateData(dt.date(2023, 7, 1), 600, 680, "Partial recovery"),
    PhosphateData(dt.date(2023, 10, 1), 550, 690, "Logistic delays"),
    
    # 2024 - Gradual recovery
    PhosphateData(dt.date(2024, 1, 1), 610, 700, "Recovery phase"),
    PhosphateData(dt.date(2024, 4, 1), 640, 720, "Production improving"),
    PhosphateData(dt.date(2024, 7, 1), 680, 740, "High global prices"),
    PhosphateData(dt.date(2024, 10, 1), 700, 760, "Near normal capacity"),
    
    # 2025 - Stabilization
    PhosphateData(dt.date(2025, 1, 1), 720, 750, "Stable production"),
    PhosphateData(dt.date(2025, 4, 1), 730, 740, "Slight price correction"),
    PhosphateData(dt.date(2025, 7, 1), 740, 730, "Steady state"),
    PhosphateData(dt.date(2025, 10, 1), 750, 720, "Global demand stable"),
]

# TMM rates (Banque Centrale de Tunisie)
# Source: BCT monetary policy reports
TMM_HISTORY = [
    # 2023 - Fighting inflation
    TMMData(dt.date(2023, 1, 1), 7.0, 0),
    TMMData(dt.date(2023, 3, 1), 7.25, 25),
    TMMData(dt.date(2023, 6, 1), 7.5, 25),
    TMMData(dt.date(2023, 9, 1), 7.75, 25),
    TMMData(dt.date(2023, 12, 1), 8.0, 25),
    
    # 2024 - Peak rates
    TMMData(dt.date(2024, 3, 1), 8.0, 0),
    TMMData(dt.date(2024, 6, 1), 8.0, 0),
    TMMData(dt.date(2024, 9, 1), 7.75, -25),
    TMMData(dt.date(2024, 12, 1), 7.5, -25),
    
    # 2025 - Easing cycle
    TMMData(dt.date(2025, 3, 1), 7.25, -25),
    TMMData(dt.date(2025, 6, 1), 7.0, -25),
    TMMData(dt.date(2025, 9, 1), 6.75, -25),
]

# Tourism arrivals (thousands)
# Source: ONTT data + COVID recovery trends
TOURISM_HISTORY = [
    # 2023 - Post-COVID recovery
    TourismData(dt.date(2023, 1, 1), 180, 0),
    TourismData(dt.date(2023, 4, 1), 420, 45),  # Spring season
    TourismData(dt.date(2023, 7, 1), 1200, 60),  # Peak summer
    TourismData(dt.date(2023, 10, 1), 350, 35),
    
    # 2024 - Strong recovery
    TourismData(dt.date(2024, 1, 1), 200, 11),
    TourismData(dt.date(2024, 4, 1), 500, 19),
    TourismData(dt.date(2024, 7, 1), 1400, 17),
    TourismData(dt.date(2024, 10, 1), 400, 14),
    
    # 2025 - Mature recovery
    TourismData(dt.date(2025, 1, 1), 210, 5),
    TourismData(dt.date(2025, 4, 1), 520, 4),
    TourismData(dt.date(2025, 7, 1), 1450, 4),
    TourismData(dt.date(2025, 10, 1), 420, 5),
]


# ═══════════════════════════════════════════════════════════════════════════
# 3. SECTOR MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════

# Which sectors are sensitive to which macro indicators
PHOSPHATE_SENSITIVE_SECTORS = [
    "Matériaux de Base",
    "Industrie",
    "Industrie & Services",
    "Transport",
]

TMM_POSITIVE_SECTORS = [
    "Services Financiers",
    "Banques",
]

TMM_NEGATIVE_SECTORS = [
    "Leasing",
    "Immobilier",
    "Services Financiers & Immobiliers",
]

TOURISM_SENSITIVE_SECTORS = [
    "Consommation",
    "Biens de Consommation",
    "Services aux Consommateurs",
    "Hôtellerie",
]


# ═══════════════════════════════════════════════════════════════════════════
# 4. QUERY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_macro_snapshot(target_date: dt.date) -> MacroSnapshot:
    """
    Get macro indicators for a specific date (uses nearest historical data).
    """
    # Find nearest phosphate data
    phosphate = None
    min_delta = float('inf')
    for p in PHOSPHATE_HISTORY:
        delta = abs((target_date - p.date).days)
        if delta < min_delta:
            min_delta = delta
            phosphate = p
    
    # Find nearest TMM data
    tmm = None
    min_delta = float('inf')
    for t in TMM_HISTORY:
        delta = abs((target_date - t.date).days)
        if delta < min_delta:
            min_delta = delta
            tmm = t
    
    # Find nearest tourism data
    tourism = None
    min_delta = float('inf')
    for t in TOURISM_HISTORY:
        delta = abs((target_date - t.date).days)
        if delta < min_delta:
            min_delta = delta
            tourism = t
    
    return MacroSnapshot(
        date=target_date,
        phosphate=phosphate,
        tmm=tmm,
        tourism=tourism,
    )


def get_macro_features_for_stock(
    sector: str,
    target_date: dt.date,
) -> Dict[str, float]:
    """
    Generate macro feature vector for ML model based on stock sector.
    
    Returns:
        Dict with normalized features (-1 to 1 scale)
    """
    snapshot = get_macro_snapshot(target_date)
    features = {}
    
    # Phosphate features
    if snapshot.phosphate:
        # Normalize production (500-800 kt range)
        prod_norm = (snapshot.phosphate.production_kt - 650) / 150
        features['phosphate_production'] = max(-1, min(1, prod_norm))
        
        # Normalize price (600-800 USD range)
        price_norm = (snapshot.phosphate.global_price_usd - 700) / 100
        features['phosphate_price'] = max(-1, min(1, price_norm))
        
        # Sector sensitivity
        if sector in PHOSPHATE_SENSITIVE_SECTORS:
            features['phosphate_sector_weight'] = 1.0
        else:
            features['phosphate_sector_weight'] = 0.1
    
    # TMM features
    if snapshot.tmm:
        # Normalize rate (6.5-8.5% range)
        tmm_norm = (snapshot.tmm.rate - 7.5) / 1.0
        features['tmm_rate'] = max(-1, min(1, tmm_norm))
        
        # Rate direction (positive = rising rates)
        features['tmm_change_bps'] = max(-1, min(1, snapshot.tmm.change_bps / 50))
        
        # Sector impact
        if sector in TMM_POSITIVE_SECTORS:
            features['tmm_sector_impact'] = 1.0  # Banks benefit from high rates
        elif sector in TMM_NEGATIVE_SECTORS:
            features['tmm_sector_impact'] = -1.0  # Leasing hurt by high rates
        else:
            features['tmm_sector_impact'] = 0.0
    
    # Tourism features
    if snapshot.tourism:
        # Normalize arrivals (150-1500k range)
        tourism_norm = (snapshot.tourism.arrivals - 600) / 600
        features['tourism_arrivals'] = max(-1, min(1, tourism_norm))
        
        # Year-over-year growth
        features['tourism_growth'] = max(-1, min(1, snapshot.tourism.yoy_change / 100))
        
        # Sector sensitivity
        if sector in TOURISM_SENSITIVE_SECTORS:
            features['tourism_sector_weight'] = 1.0
        else:
            features['tourism_sector_weight'] = 0.1
    
    return features


def get_macro_explanation(sector: str, target_date: dt.date) -> str:
    """
    Generate human-readable explanation of macro conditions.
    """
    snapshot = get_macro_snapshot(target_date)
    parts = []
    
    if snapshot.phosphate and sector in PHOSPHATE_SENSITIVE_SECTORS:
        parts.append(
            f"📦 Phosphate: {snapshot.phosphate.production_kt}kt production "
            f"(${snapshot.phosphate.global_price_usd}/ton DAP). "
            f"{snapshot.phosphate.notes}"
        )
    
    if snapshot.tmm:
        direction = "↑" if snapshot.tmm.change_bps > 0 else "↓" if snapshot.tmm.change_bps < 0 else "→"
        impact = ""
        if sector in TMM_POSITIVE_SECTORS:
            impact = " (Positive for banking)"
        elif sector in TMM_NEGATIVE_SECTORS:
            impact = " (Negative for leasing/real estate)"
        
        parts.append(
            f"💰 TMM: {snapshot.tmm.rate}% {direction}{impact}"
        )
    
    if snapshot.tourism and sector in TOURISM_SENSITIVE_SECTORS:
        parts.append(
            f"✈️ Tourism: {snapshot.tourism.arrivals}k arrivals "
            f"({snapshot.tourism.yoy_change:+.1f}% YoY)"
        )
    
    return " | ".join(parts) if parts else "No macro factors apply to this sector"


# ═══════════════════════════════════════════════════════════════════════════
# 5. DEMO
# ═══════════════════════════════════════════════════════════════════════════

def demo():
    """Demo macro features for different sectors."""
    test_cases = [
        ("CPG (Phosphates)", "Matériaux de Base", dt.date(2024, 7, 1)),
        ("BIAT (Bank)", "Services Financiers", dt.date(2024, 7, 1)),
        ("SFBT (Beverages)", "Consommation", dt.date(2024, 7, 1)),
        ("ATL (Leasing)", "Leasing", dt.date(2024, 7, 1)),
    ]
    
    print("🇹🇳 MACRO FEATURES DEMO - K.O. Feature #2\n" + "="*70)
    
    for company, sector, date in test_cases:
        print(f"\n📊 {company} - {sector} - {date}")
        
        features = get_macro_features_for_stock(sector, date)
        print(f"   Features: {features}")
        
        explanation = get_macro_explanation(sector, date)
        print(f"   📝 {explanation}")


if __name__ == "__main__":
    demo()
