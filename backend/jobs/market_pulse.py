"""
Market Pulse Job - News Scraping and Sentiment Analysis

Replaces the n8n Market Pulse workflow with Python code.
Runs on schedule to scrape news and analyze sentiment.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_settings
from core.database import get_db, engine
from sqlalchemy import text
from loguru import logger

settings = get_settings()


class MarketPulseJob:
    """Scrapes financial news and analyzes sentiment"""
    
    def __init__(self):
        self.news_sources = [
            "https://www.ilboursa.com/marches/actualites-boursieres",
            # Add more sources as needed
        ]
        self.telegram_enabled = False  # Set to True when configured
        
    def scrape_ilboursa_news(self, url):
        """Scrape news articles from IlBoursa"""
        try:
            logger.info(f"Scraping news from {url}")
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract articles (adjust selectors based on actual website structure)
            articles = []
            
            # Try to find article containers
            article_containers = soup.find_all('article') or soup.find_all('div', class_=['article', 'news-item', 'post'])
            
            for container in article_containers[:10]:  # Limit to 10 articles
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                content_elem = container.find(['p', 'div'], class_=['content', 'excerpt', 'description'])
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    content = content_elem.get_text(strip=True) if content_elem else ""
                    
                    articles.append({
                        'title': title,
                        'content': content,
                        'text': f"{title}. {content}"
                    })
            
            logger.info(f"Found {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping news: {e}")
            return []
    
    def analyze_sentiment(self, text):
        """
        Call backend sentiment analysis API
        TODO: Replace with actual ML model call when implemented
        """
        try:
            # For now, return dummy sentiment
            # When ML team implements, this will call the actual model
            
            # Placeholder logic (replace with actual API/model)
            sentiment_score = 0.0
            classification = "NEUTRAL"
            
            # Simple keyword-based sentiment (temporary)
            positive_words = ['hausse', 'gain', 'augmente', 'positif', 'croissance']
            negative_words = ['baisse', 'perte', 'chute', 'négatif', 'recul']
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                sentiment_score = 0.5 + (pos_count * 0.1)
                classification = "POSITIVE"
            elif neg_count > pos_count:
                sentiment_score = -0.5 - (neg_count * 0.1)
                classification = "NEGATIVE"
            
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            return {
                'score': sentiment_score,
                'classification': classification
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'score': 0.0, 'classification': 'NEUTRAL'}
    
    def store_sentiment(self, stock_id, sentiment_data, source='news'):
        """Store sentiment data in database"""
        try:
            with engine.connect() as conn:
                # Check if stock exists, if not use stock_id=1 as default
                result = conn.execute(text("SELECT id FROM stocks LIMIT 1"))
                default_stock = result.fetchone()
                stock_id = default_stock[0] if default_stock else 1
                
                # Insert sentiment
                conn.execute(text("""
                    INSERT INTO sentiments 
                    (stock_id, date, score, classification, news_score, source_count)
                    VALUES (:stock_id, :date, :score, :classification, :news_score, :source_count)
                """), {
                    'stock_id': stock_id,
                    'date': datetime.now(),
                    'score': sentiment_data['score'],
                    'classification': sentiment_data['classification'],
                    'news_score': sentiment_data['score'],
                    'source_count': 1
                })
                conn.commit()
                logger.info(f"Stored sentiment: {sentiment_data}")
                
        except Exception as e:
            logger.error(f"Error storing sentiment: {e}")
    
    def send_telegram_alert(self, ticker, sentiment_data):
        """Send Telegram alert for extreme sentiment"""
        if not self.telegram_enabled:
            logger.info(f"Telegram disabled. Would send alert for {ticker}: {sentiment_data}")
            return
        
        try:
            # TODO: Implement Telegram bot integration
            message = f"""
🚨 Extreme Sentiment Detected!

Stock: {ticker}
Sentiment: {sentiment_data['classification']}
Score: {sentiment_data['score']:.2f}

Check the dashboard for details.
            """
            logger.info(f"Telegram alert: {message}")
            
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
    
    def run(self):
        """Main job execution"""
        logger.info("=" * 60)
        logger.info("🔍 Market Pulse Job Started")
        logger.info("=" * 60)
        
        total_articles = 0
        extreme_sentiments = 0
        
        for source_url in self.news_sources:
            articles = self.scrape_ilboursa_news(source_url)
            
            for article in articles:
                # Analyze sentiment
                sentiment = self.analyze_sentiment(article['text'])
                
                # Store in database
                self.store_sentiment(stock_id=1, sentiment_data=sentiment)
                
                total_articles += 1
                
                # Check for extreme sentiment
                if abs(sentiment['score']) > 0.8:
                    extreme_sentiments += 1
                    self.send_telegram_alert("MARKET", sentiment)
        
        logger.info(f"✅ Processed {total_articles} articles")
        logger.info(f"⚠️  Found {extreme_sentiments} extreme sentiments")
        logger.info("=" * 60)


if __name__ == "__main__":
    job = MarketPulseJob()
    job.run()
