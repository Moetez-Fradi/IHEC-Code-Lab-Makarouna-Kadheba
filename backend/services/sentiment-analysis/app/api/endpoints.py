from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

# --- CORRECTION : On importe le nouveau service LLM ---
from app.services.llm_service import llm_service
from app.services.ticker_service import ticker_service

# --- Définition des Schemas ---
class SentimentRequest(BaseModel):
    text: str
    ticker: Optional[str] = None

class SentimentResponse(BaseModel):
    sentiment: str
    confidence: float
    scores: Dict[str, float]
    language: str
    ticker: Optional[str] = None
    # ticker_keywords_found est optionnel maintenant car l'LLM ne le renvoie pas forcément
    ticker_keywords_found: List[str] = [] 

router = APIRouter()

@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(payload: SentimentRequest):
    """
    Endpoint principal d'analyse de sentiment via OpenRouter (LLM).
    """
    try:
        # 1. Analyse via OpenRouter (LLM)
        # L'LLM fait tout : détection langue + sentiment + extraction ticker
        ai_result = llm_service.analyze_sentiment(payload.text, payload.ticker)
        
        # 2. Validation / Fallback pour le Ticker
        # Si l'IA a trouvé un ticker, on le prend. 
        # Sinon, on utilise ton ancien service regex local pour être sûr.
        detected_ticker = ai_result.get("ticker_detected")
        keywords = []

        if not detected_ticker:
            detected_ticker, keywords = ticker_service.extract_ticker_from_text(
                payload.text, 
                payload.ticker
            )
        
        # 3. Construction de la réponse
        return SentimentResponse(
            sentiment=ai_result["sentiment"],
            confidence=ai_result.get("confidence", 0.0),
            scores=ai_result.get("scores", {}),
            language=ai_result.get("language", "unknown"),
            ticker=detected_ticker,
            ticker_keywords_found=keywords
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")