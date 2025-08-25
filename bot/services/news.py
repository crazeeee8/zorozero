import logging
import aiohttp
from typing import List
from ..config import settings
from ..state import STATE
from ..utils import async_backoff

# This function can be defined once in a shared http_client.py to avoid repetition
async def _ensure_session() -> aiohttp.ClientSession:
    if STATE.session and not STATE.session.closed:
        return STATE.session
    timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
    STATE.session = aiohttp.ClientSession(timeout=timeout)
    return STATE.session

async def _fetch_cryptopanic_news() -> List[dict]:
    """Fetches the raw news data from the CryptoPanic API."""
    if not settings.CRYPTOPANIC_API_KEY:
        return []

    session = await _ensure_session()
    url = "https://cryptopanic.com/api/v1/posts/"
    params = {"auth_token": settings.CRYPTOPANIC_API_KEY, "currencies": "BTC", "public": "true"}

    async def _get():
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("results", [])

    try:
        return await async_backoff(_get, label="cryptopanic.get")
    except Exception as e:
        logging.error(f"CryptoPanic API failed: {e}")
        return []

def _format_sentiment(article: dict) -> str:
    """Formats a sentiment emoji and tag based on votes."""
    votes = article.get('votes', {})
    positive_votes = votes.get('positive', 0)
    negative_votes = votes.get('negative', 0)

    if positive_votes > negative_votes:
        return "🟢 [Bullish]"
    if negative_votes > positive_votes:
        return "🔴 [Bearish]"
    return "⚪️ [Neutral]"

async def get_daily_news() -> List[str]:
    """
    Fetches news, filters out seen articles, and formats them for Discord.
    Returns a list of formatted message strings.
    """
    articles = await _fetch_cryptopanic_news()
    if not articles:
        return []

    messages = []
    new_articles_count = 0

    for article in articles:
        article_id = str(article.get("id", ""))
        if not article_id or article_id in STATE.seen_news_ids:
            continue
            
        if new_articles_count >= 5: # Limit to 5 new articles per day
            break

        title = article.get("title")
        url = article.get("url")
        sentiment = _format_sentiment(article)
        
        messages.append(f"**{sentiment}**: {title}\n<{url}>")
        
        STATE.seen_news_ids.add(article_id)
        new_articles_count += 1
        
    if new_articles_count > 0:
        messages.insert(0, f"--- 📰 Daily Crypto News Summary ---")

    return messages