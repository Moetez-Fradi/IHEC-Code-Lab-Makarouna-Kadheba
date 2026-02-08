"""
Quick test for Perplexity API integration
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PERPLEXITY_API_KEY"] = "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"

from app.services.perplexity_search import search_social_media_for_ticker


async def main():
    print("🔍 Testing Perplexity API...")
    print("Searching for SFBT...")
    
    try:
        posts = await search_social_media_for_ticker("SFBT", max_posts=3)
        print(f"\n✅ Found {len(posts)} posts:")
        for i, post in enumerate(posts, 1):
            print(f"\n{i}. [{post.platform}]")
            print(f"   {post.content[:150]}...")
            if post.url:
                print(f"   URL: {post.url}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
