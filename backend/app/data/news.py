"""
news.py — NewsAPI fetch + VADER sentiment scoring per ticker.
Returns sentiment scores in range [-1, 1].
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import nltk

logger = logging.getLogger(__name__)

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

from nltk.sentiment.vader import SentimentIntensityAnalyzer

_vader = None


def get_vader():
    global _vader
    if _vader is None:
        _vader = SentimentIntensityAnalyzer()
    return _vader


TICKER_KEYWORDS = {
    "NVDA": ["NVIDIA", "NVDA", "nvidia gpu", "AI chips"],
    "MSFT": ["Microsoft", "MSFT", "Azure", "Copilot"],
    "GOOGL": ["Google", "Alphabet", "GOOGL", "Gemini AI"],
    "GLD": ["gold price", "gold ETF", "bullion", "GLD"],
    "USO": ["oil price", "crude oil", "USO ETF", "WTI"],
}


def score_text(text: str) -> float:
    """Score a single text with VADER. Returns compound score [-1, 1]."""
    sid = get_vader()
    scores = sid.polarity_scores(text)
    return round(scores["compound"], 4)


def fetch_news_sentiment(ticker: str, api_key: Optional[str] = None) -> dict:
    """
    Fetch last 24h headlines for ticker and return sentiment summary.
    Falls back to mock data if no API key.
    """
    api_key = api_key or os.getenv("NEWSAPI_KEY", "")
    headlines = []
    scores = []

    if api_key:
        try:
            from newsapi import NewsApiClient
            client = NewsApiClient(api_key=api_key)
            keywords = TICKER_KEYWORDS.get(ticker, [ticker])
            query = " OR ".join(keywords)
            from_time = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")

            response = client.get_everything(
                q=query,
                from_param=from_time,
                language="en",
                sort_by="relevancy",
                page_size=10,
            )
            articles = response.get("articles", [])
            for art in articles:
                title = art.get("title", "") or ""
                desc = art.get("description", "") or ""
                combined = f"{title}. {desc}"
                headlines.append(title)
                scores.append(score_text(combined))
        except Exception as e:
            logger.warning(f"NewsAPI error for {ticker}: {e}. Using mock data.")

    if not scores:
        import hashlib
        seed = int(hashlib.md5(f"{ticker}{datetime.utcnow().hour}".encode()).hexdigest()[:8], 16)
        import random
        rng = random.Random(seed)
        scores = [rng.uniform(-0.6, 0.9) for _ in range(5)]
        mock_headlines = {
            "NVDA": ["NVIDIA reports record AI chip demand", "GPU shortages ease as supply ramps", "NVDA beats earnings expectations"],
            "MSFT": ["Microsoft Azure growth accelerates", "Copilot integration drives enterprise adoption", "MSFT cloud margin expands"],
            "GOOGL": ["Google Gemini gains market share", "Alphabet ad revenue rebounds", "GOOGL search dominance continues"],
            "GLD": ["Gold rallies on Fed uncertainty", "Safe haven demand pushes gold higher", "Inflation fears lift bullion"],
            "USO": ["Oil prices volatile on OPEC+ news", "Crude demand outlook mixed", "USO reflects WTI consolidation"],
        }
        headlines = mock_headlines.get(ticker, [f"{ticker} news headline"])

    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0
    return {
        "ticker": ticker,
        "sentiment_score": avg_score,
        "headline_count": len(scores),
        "top_headlines": headlines[:3],
        "score_label": "POSITIVE" if avg_score > 0.05 else "NEGATIVE" if avg_score < -0.05 else "NEUTRAL",
        "timestamp": datetime.utcnow().isoformat(),
    }


def fetch_all_sentiment(api_key: Optional[str] = None) -> dict:
    """Fetch sentiment for all 5 assets."""
    from .fetcher import ASSETS
    results = {}
    for ticker in ASSETS:
        results[ticker] = fetch_news_sentiment(ticker, api_key)
        logger.info(f"Sentiment {ticker}: {results[ticker]['sentiment_score']:.3f} ({results[ticker]['score_label']})")
    return results
