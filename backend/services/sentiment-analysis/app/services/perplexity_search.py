"""
Perplexity AI Search Integration for Social Media Scraping

Uses Perplexity's Sonar model to search and aggregate content from:
- Twitter/X (financial discussions about BVMT)
- r/tunisia Reddit (economic/stock discussions)
- Tunisian finance Facebook groups
- Tunisia-Sat forums (financial discussions)

This enhances sentiment analysis by capturing retail investor sentiment
from social media where Tunisians actually discuss stocks.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_MODEL = "sonar"  # Best for real-time search
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


# ═══════════════════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SocialMediaPost:
    """Represents a social media post about a stock."""
    platform: str  # twitter, reddit, facebook, tunisia-sat
    content: str
    ticker: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    engagement: int = 0  # likes, upvotes, etc.


@dataclass
class PerplexitySearchResult:
    """Result from Perplexity search."""
    query: str
    answer: str
    citations: List[str]
    posts: List[SocialMediaPost]


# ═══════════════════════════════════════════════════════════════════════════
# Search Queries for Different Sources
# ═══════════════════════════════════════════════════════════════════════════

def build_search_queries(ticker: str) -> List[str]:
    """
    Build targeted search queries for Perplexity to find social media discussions.
    
    Perplexity's Sonar model will search the web and return recent discussions.
    """
    company_names = {
        "SFBT": "SFBT OR 'Société Frigorifique et Brasserie' OR 'la bière'",
        "BIAT": "BIAT OR 'Banque Internationale Arabe'",
        "BNA": "BNA OR 'Banque Nationale Agricole' OR 'banque verte'",
        "POULINA": "Poulina OR 'Poulina Group Holding'",
        "DELICE": "Délice OR Delice OR 'Délice Holding'",
        "CARTHAGE": "Carthage OR 'Ciments de Carthage'",
    }
    
    company_query = company_names.get(ticker, ticker)
    
    return [
        # Twitter/X search
        f"site:twitter.com OR site:x.com {company_query} bourse tunisie stock",
        
        # Reddit search
        f"site:reddit.com/r/tunisia {company_query} bourse investissement",
        
        # Tunisia-Sat forums
        f"site:tunisia-sat.com/forums {company_query} bourse action investissement",
        
        # Facebook (public posts - limited but Perplexity can find some)
        f"site:facebook.com {company_query} bourse tunisie action",
        
        # General Tunisian financial forums
        f"{company_query} forum discussion bourse tunisie investissement",
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Perplexity API Integration
# ═══════════════════════════════════════════════════════════════════════════

async def search_with_perplexity(
    query: str,
    max_results: int = 5,
) -> Optional[dict]:
    """
    Search using Perplexity Sonar model.
    
    The Sonar model is optimized for real-time web search and returns
    up-to-date information with citations.
    """
    if not PERPLEXITY_API_KEY:
        logger.error("PERPLEXITY_API_KEY not set")
        return None
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a financial analyst assistant searching for recent discussions "
                    "about Tunisian stocks on social media. Focus on sentiment, opinions, "
                    "and predictions from retail investors. Extract key quotes and sentiments."
                )
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": ["perplexity.ai"],  # Use Perplexity's search
        "return_citations": True,
        "search_recency_filter": "month",  # Focus on recent content
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(
                PERPLEXITY_API_URL,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    
    except httpx.HTTPStatusError as e:
        logger.error(f"Perplexity API error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Perplexity search failed: {e}")
        return None


def parse_perplexity_response(response: dict, query: str) -> PerplexitySearchResult:
    """
    Parse Perplexity API response and extract social media posts.
    """
    if not response or "choices" not in response:
        return PerplexitySearchResult(
            query=query,
            answer="",
            citations=[],
            posts=[],
        )
    
    choice = response["choices"][0]
    message = choice.get("message", {})
    answer = message.get("content", "")
    
    # Extract citations (URLs where info was found)
    citations = []
    if "citations" in response:
        citations = response["citations"]
    
    # Parse answer to extract posts/quotes
    posts = []
    
    # Simple parsing: look for quoted text and platform mentions
    lines = answer.split("\n")
    current_post = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect platform
        platform = None
        if "twitter" in line.lower() or "x.com" in line.lower():
            platform = "twitter"
        elif "reddit" in line.lower():
            platform = "reddit"
        elif "facebook" in line.lower():
            platform = "facebook"
        elif "tunisia-sat" in line.lower():
            platform = "tunisia-sat"
        
        # If we found quoted text or platform mention, create a post
        if platform or '"' in line or "'" in line:
            # Extract content (remove quotes and platform mentions)
            content = line.replace("Twitter:", "").replace("Reddit:", "")
            content = content.replace("Facebook:", "").replace("Tunisia-Sat:", "")
            content = content.strip(' "\'')
            
            if len(content) > 20:  # Only keep substantial content
                posts.append(SocialMediaPost(
                    platform=platform or "unknown",
                    content=content,
                    ticker=None,  # Will be set by caller
                ))
    
    return PerplexitySearchResult(
        query=query,
        answer=answer,
        citations=citations,
        posts=posts,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Main Search Function
# ═══════════════════════════════════════════════════════════════════════════

async def search_social_media_for_ticker(
    ticker: str,
    max_posts: int = 10,
) -> List[SocialMediaPost]:
    """
    Search social media platforms for discussions about a specific ticker.
    
    Returns a list of social media posts with sentiment-relevant content.
    
    Args:
        ticker: Stock ticker (e.g., "SFBT", "BIAT")
        max_posts: Maximum number of posts to return
    
    Returns:
        List of SocialMediaPost objects
    """
    if not PERPLEXITY_API_KEY:
        logger.warning("Perplexity API key not configured - skipping social media search")
        return []
    
    all_posts = []
    queries = build_search_queries(ticker)
    
    logger.info(f"Searching social media for {ticker} using Perplexity...")
    
    # Search each query
    for query in queries[:3]:  # Limit to first 3 queries to avoid rate limits
        try:
            response = await search_with_perplexity(query, max_results=5)
            if response:
                result = parse_perplexity_response(response, query)
                
                # Add ticker to posts
                for post in result.posts:
                    post.ticker = ticker
                
                all_posts.extend(result.posts)
                
                logger.info(
                    f"Found {len(result.posts)} posts for query: {query[:50]}..."
                )
        
        except Exception as e:
            logger.error(f"Error searching with query '{query[:50]}...': {e}")
            continue
    
    # Deduplicate by content similarity
    unique_posts = []
    seen_content = set()
    
    for post in all_posts:
        # Use first 100 chars as fingerprint
        fingerprint = post.content[:100].lower()
        if fingerprint not in seen_content:
            seen_content.add(fingerprint)
            unique_posts.append(post)
            
            if len(unique_posts) >= max_posts:
                break
    
    logger.info(f"Returning {len(unique_posts)} unique social media posts for {ticker}")
    
    return unique_posts


# ═══════════════════════════════════════════════════════════════════════════
# Batch Search
# ═══════════════════════════════════════════════════════════════════════════

async def search_social_media_batch(
    tickers: List[str],
    max_posts_per_ticker: int = 5,
) -> dict[str, List[SocialMediaPost]]:
    """
    Search social media for multiple tickers.
    
    Returns a dictionary mapping ticker → list of posts.
    """
    results = {}
    
    for ticker in tickers:
        posts = await search_social_media_for_ticker(ticker, max_posts_per_ticker)
        results[ticker] = posts
    
    return results


# ═══════════════════════════════════════════════════════════════════════════
# Demo/Test
# ═══════════════════════════════════════════════════════════════════════════

async def demo():
    """Demo Perplexity social media search."""
    print("🔍 PERPLEXITY SOCIAL MEDIA SEARCH DEMO")
    print("=" * 80)
    
    if not PERPLEXITY_API_KEY:
        print("❌ PERPLEXITY_API_KEY not set!")
        print("   Set it in .env file:")
        print("   PERPLEXITY_API_KEY=pplx-xxxxx")
        return
    
    # Test with SFBT
    print("\n📊 Searching for SFBT discussions on social media...")
    posts = await search_social_media_for_ticker("SFBT", max_posts=5)
    
    print(f"\n✅ Found {len(posts)} posts:\n")
    
    for i, post in enumerate(posts, 1):
        print(f"{i}. [{post.platform.upper()}]")
        print(f"   {post.content[:150]}...")
        if post.url:
            print(f"   URL: {post.url}")
        print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
