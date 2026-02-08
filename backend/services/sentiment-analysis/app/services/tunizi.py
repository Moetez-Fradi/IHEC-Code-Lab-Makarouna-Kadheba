"""
Tunizi/Arabizi Linguistic Processor for BVMT Financial Sentiment

This module provides the "K.O. feature" for the hackathon:
- Arabizi normalization (3→aa, 7→h, 9→q)
- Tunisian financial slang dictionary
- Code-switching detection (Arabic/French/Tunizi mix)
- Entity mapping (nicknames → tickers)

This is THE differentiator that no other team will have.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 1. ARABIZI NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════

# Arabizi → Latin/Arabic mapping
ARABIZI_MAP = {
    "2": "aa",  # Hamza (أ)
    "3": "aa",  # Ain (ع)
    "5": "kh",  # Kha (خ)
    "6": "t",   # Ta (ط)
    "7": "h",   # Ha (ح)
    "8": "gh",  # Ghain (غ)
    "9": "q",   # Qaf (ق)
}

def normalize_arabizi(text: str) -> str:
    """
    Convert Arabizi numbers to approximate Latin equivalents.
    
    Examples:
        "SFBT bech ti7 2main" → "SFBT bech tih aamain"
        "9aS3d ktir" → "qaSaad ktir"
    """
    normalized = text
    for digit, replacement in ARABIZI_MAP.items():
        normalized = normalized.replace(digit, replacement)
    return normalized


# ═══════════════════════════════════════════════════════════════════════════
# 2. TUNISIAN FINANCIAL SLANG DICTIONARY
# ═══════════════════════════════════════════════════════════════════════════

# Tunizi slang → (sentiment_weight, meaning)
TUNIZI_SLANG = {
    # Market terms
    "bouse": (0.0, "bourse (stock market)"),
    "bourse": (0.0, "stock market"),
    
    # Bullish terms (positive)
    "tla3": (0.7, "rising/going up"),
    "tla3et": (0.7, "it went up"),
    "ti6la3": (0.6, "it will go up"),
    "to the moon": (0.9, "extremely bullish"),
    "khdhit": (0.5, "I bought/took position"),
    "rbe7": (0.8, "profit/win"),
    "rbi7na": (0.9, "we won/profited"),
    "mazelt": (0.3, "still holding"),
    
    # Bearish terms (negative)
    "taya7": (-0.7, "falling/dropping"),
    "tay7a": (-0.7, "falling (feminine)"),
    "ti7": (-0.8, "drop/fall"),
    "ti7it": (-0.8, "it dropped"),
    "bech ti7": (-0.7, "will drop"),
    "bech taya7": (-0.7, "will fall"),
    "khsar": (-0.9, "loss"),
    "khsart": (-0.8, "I lost"),
    "khsarna": (-0.9, "we lost"),
    "marbou6a": (-0.6, "tied up/stuck"),
    "makch": (-0.5, "not good/bad"),
    
    # Neutral/descriptive
    "2main": (0.0, "tomorrow"),
    "lyoum": (0.0, "today"),
    "taw": (0.0, "now"),
    "chway": (0.0, "a little"),
    "bech": (0.0, "will/going to"),
    "ken": (0.0, "if"),
    
    # Strong emotions
    "yaasr": (0.6, "great/excellent"),
    "behi": (0.5, "good"),
    "wa3er": (0.7, "awesome"),
    "fa5er": (0.8, "proud/impressive"),
    "koulech marbou6": (-0.8, "everything tied up/stuck"),
    "cata": (-0.9, "catastrophe"),
    "msaybe": (-0.8, "disaster"),
}

# Company nicknames → ticker mapping
COMPANY_NICKNAMES = {
    # Beverages
    "la bière": "SFBT",
    "bière": "SFBT",
    "sfbt": "SFBT",
    "frigori": "SFBT",
    
    # Dairy
    "délice": "DELICE",
    "delice": "DELICE",
    "vitalait": "DELICE",
    
    # Banking
    "la banque verte": "BNA",
    "banque verte": "BNA",
    "bna": "BNA",
    "biat": "BIAT",
    "amen": "AMEN",
    "attijari": "ATTIJARI",
    
    # Industrial
    "poulina": "POULINA",
    "groupe poulina": "POULINA",
    "carthage": "CARTHAGE",
    "ciment": "CARTHAGE",
    
    # Telecom
    "telnet": "TELNET",
    "orange": "ORANGE",
    "tunisie telecom": "TT",
    
    # Others
    "eurocycles": "EURO-CYCLES",
    "tunisair": "TUNISAIR",
    "sotetel": "SOTETEL",
}


# ═══════════════════════════════════════════════════════════════════════════
# 3. FINANCIAL KEYWORDS (French/Arabic/Tunizi)
# ═══════════════════════════════════════════════════════════════════════════

# Strong sentiment keywords (override model score)
FINANCIAL_KEYWORDS = {
    # Positive (French)
    "dividende": 0.8,
    "augmentation de capital": 0.7,
    "bénéfice record": 0.9,
    "rachat": 0.6,
    "partenariat stratégique": 0.7,
    "acquisition": 0.6,
    "croissance": 0.6,
    "performance": 0.5,
    "succès": 0.7,
    
    # Negative (French)
    "déficit": -0.8,
    "grève": -0.9,  # CRITICAL in Tunisia
    "profit warning": -0.8,
    "sanction cmf": -0.9,
    "redressement fiscal": -0.7,
    "perte": -0.7,
    "faillite": -1.0,
    "restructuration": -0.6,
    "licenciement": -0.7,
    
    # Arabic
    "أرباح": 0.7,  # profits
    "خسائر": -0.8,  # losses
    "إضراب": -0.9,  # strike
    "نمو": 0.6,  # growth
}


# ═══════════════════════════════════════════════════════════════════════════
# 4. CORE PROCESSING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def detect_language_mix(text: str) -> Dict[str, float]:
    """
    Detect code-switching: Arabic, French, Tunizi mix.
    
    Returns percentage of each type detected.
    """
    text_lower = text.lower()
    
    # Simple heuristic detection
    has_arabic = bool(re.search(r'[\u0600-\u06FF]', text))
    has_french = bool(re.search(r'[àâäéèêëïîôùûüÿæœç]', text_lower))
    has_arabizi = bool(re.search(r'\d', text))
    has_tunizi_slang = any(slang in text_lower for slang in TUNIZI_SLANG.keys())
    
    return {
        "arabic": 0.8 if has_arabic else 0.0,
        "french": 0.7 if has_french else 0.3,
        "arabizi": 0.9 if has_arabizi else 0.0,
        "tunizi_slang": 1.0 if has_tunizi_slang else 0.0,
    }


def extract_tunizi_sentiment(text: str) -> Tuple[float, list[str]]:
    """
    Extract sentiment from Tunizi slang and financial keywords.
    
    Returns:
        (sentiment_score, matched_keywords)
    """
    text_lower = text.lower()
    text_normalized = normalize_arabizi(text_lower)
    
    matched = []
    total_score = 0.0
    count = 0
    
    # Check Tunizi slang
    for slang, (weight, meaning) in TUNIZI_SLANG.items():
        if slang in text_normalized or slang in text_lower:
            matched.append(f"{slang} ({meaning})")
            total_score += weight
            count += 1
    
    # Check financial keywords
    for keyword, weight in FINANCIAL_KEYWORDS.items():
        if keyword in text_lower:
            matched.append(f"{keyword}")
            total_score += weight
            count += 1
    
    # Average score (or 0 if nothing matched)
    avg_score = total_score / count if count > 0 else 0.0
    
    return avg_score, matched


def extract_ticker_from_nicknames(text: str) -> str | None:
    """
    Map company nicknames to official tickers.
    
    Example:
        "La bière va monter" → "SFBT"
        "Délice dividende" → "DELICE"
    """
    text_lower = text.lower()
    
    for nickname, ticker in COMPANY_NICKNAMES.items():
        if nickname in text_lower:
            return ticker
    
    return None


def enhance_sentiment_with_tunizi(
    text: str,
    base_sentiment: str,
    base_score: float,
    base_ticker: str | None,
) -> Tuple[str, float, str | None, Dict]:
    """
    Main function: Enhance Gemini sentiment with Tunizi understanding.
    
    This is the K.O. feature that combines:
    1. Arabizi normalization
    2. Tunizi slang detection
    3. Code-switching awareness
    4. Financial keywords
    5. Nickname → ticker mapping
    
    Returns:
        (enhanced_sentiment, enhanced_score, enhanced_ticker, metadata)
    """
    # Step 1: Detect language mix
    lang_mix = detect_language_mix(text)
    
    # Step 2: Extract Tunizi sentiment
    tunizi_score, matched_keywords = extract_tunizi_sentiment(text)
    
    # Step 3: Try to extract ticker from nicknames
    nickname_ticker = extract_ticker_from_nicknames(text)
    
    # Step 4: Combine scores with weights
    # If Tunizi keywords found, give them 60% weight (rumor leads official news)
    if matched_keywords:
        alpha = 0.4  # weight for base (Gemini)
        beta = 0.6   # weight for Tunizi
        combined_score = alpha * base_score + beta * tunizi_score
    else:
        # No Tunizi detected, use base score
        combined_score = base_score
    
    # Clamp to [-1, 1]
    combined_score = max(-1.0, min(1.0, combined_score))
    
    # Step 5: Update sentiment label based on combined score
    if combined_score > 0.15:  # Lower threshold for detecting positive sentiment
        enhanced_sentiment = "positive"
    elif combined_score < -0.15:  # Lower threshold for detecting negative sentiment
        enhanced_sentiment = "negative"
    else:
        enhanced_sentiment = "neutral"
    
    # Step 6: Use nickname ticker if found
    enhanced_ticker = nickname_ticker or base_ticker
    
    # Step 7: Build metadata for explanation
    metadata = {
        "language_detection": lang_mix,
        "tunizi_keywords": matched_keywords,
        "tunizi_score": tunizi_score,
        "base_score": base_score,
        "combined_score": combined_score,
        "enhancement_applied": len(matched_keywords) > 0,
    }
    
    return enhanced_sentiment, combined_score, enhanced_ticker, metadata


# ═══════════════════════════════════════════════════════════════════════════
# 5. DEMO/TEST EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════

def demo():
    """
    Demo the K.O. feature with real Tunizi examples.
    """
    test_cases = [
        "SFBT bech ti7 2main, production marbou6a",
        "La bière va monter, dividende behi",
        "Poulina tla3et yaasr aujourd'hui",
        "Délice khsart bech nbi3",
        "Grève SNCFT cata koulech marbou6 fi transport",
    ]
    
    print("🇹🇳 TUNIZI NLP DEMO - K.O. Feature\n" + "="*60)
    
    for text in test_cases:
        print(f"\n📝 Input: {text}")
        
        # Simulate base sentiment (neutral)
        enhanced_sentiment, score, ticker, metadata = enhance_sentiment_with_tunizi(
            text=text,
            base_sentiment="neutral",
            base_score=0.0,
            base_ticker=None,
        )
        
        print(f"   Sentiment: {enhanced_sentiment.upper()} (score: {score:.2f})")
        if ticker:
            print(f"   Ticker: {ticker}")
        if metadata["tunizi_keywords"]:
            print(f"   Tunizi detected: {', '.join(metadata['tunizi_keywords'][:3])}")


if __name__ == "__main__":
    demo()
