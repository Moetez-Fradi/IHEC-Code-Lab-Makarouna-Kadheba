import json
import re
import requests
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class OpenRouterService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        # On garde Llama 3, mais on augmente le timeout
        self.model = settings.OPENROUTER_MODEL 
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def analyze_sentiment(self, text: str, ticker: str = None) -> dict:
        logger.info(f"🤖 Envoi à OpenRouter ({self.model})...")

        system_prompt = """
        Tu es un expert financier à la Bourse de Tunis (BVMT).
        Analyse le sentiment du texte.
        
        RÈGLES STRICTES :
        1. Réponds UNIQUEMENT avec un objet JSON. RIEN D'AUTRE.
        2. Format:
        {
            "sentiment": "positive" | "negative" | "neutral",
            "confidence": 0.95,
            "language": "fr" | "ar" | "tn",
            "ticker_detected": "SYMBOLE" (ex: SFBT, BIAT, ou null)
        }
        """

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Texte: {text}\nContexte Ticker: {ticker}"}
            ],
            "temperature": 0.1
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": settings.PROJECT_NAME,
        }

        try:
            # AUGMENTATION DU TIMEOUT à 30 secondes (Llama est lent en gratuit)
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30 
            )
            
            # Si erreur HTTP (401, 500, etc.), on lève l'exception tout de suite
            if response.status_code != 200:
                logger.error(f"❌ Erreur HTTP OpenRouter: {response.status_code} - {response.text}")
                raise Exception(f"OpenRouter Error {response.status_code}")

            data = response.json()
            
            # Vérification structurelle
            if 'choices' not in data or not data['choices']:
                raise Exception("Réponse vide de l'API")

            content_str = data['choices'][0]['message']['content']
            logger.info(f"📥 Réponse brute reçue : {content_str[:100]}...")

            # NETTOYAGE JSON AGRESSIF
            # Trouve la première accolade '{' et la dernière '}'
            json_match = re.search(r"\{.*\}", content_str, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                result = json.loads(clean_json)
            else:
                # Si pas de JSON trouvé, on tente de parser le brut (au cas où)
                result = json.loads(content_str)

            # Ajout des scores fictifs si manquants (pour le front)
            if "scores" not in result:
                s = result.get("sentiment", "neutral")
                if s == "positive": scores = {"positive": 0.99, "neutral": 0.01, "negative": 0.0}
                elif s == "negative": scores = {"positive": 0.0, "neutral": 0.01, "negative": 0.99}
                else: scores = {"positive": 0.05, "neutral": 0.9, "negative": 0.05}
                result["scores"] = scores

            logger.info(f"✅ Succès : {result.get('sentiment')}")
            return result

        except Exception as e:
            logger.error(f"❌ CRASH LLM : {str(e)}")
            # Fallback
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "scores": {"positive": 0, "neutral": 1, "negative": 0},
                "language": "unknown",
                "ticker_detected": None,
                "error": str(e) # On renvoie l'erreur pour débugger
            }

llm_service = OpenRouterService()