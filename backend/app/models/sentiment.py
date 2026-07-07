"""
sentiment.py — VADER wrapper for headline scoring.
Returns compound scores in [-1, 1].
"""
import nltk
import logging

logger = logging.getLogger(__name__)

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

from nltk.sentiment.vader import SentimentIntensityAnalyzer

_sia = None


def get_sia() -> SentimentIntensityAnalyzer:
    global _sia
    if _sia is None:
        _sia = SentimentIntensityAnalyzer()
    return _sia


def score_headline(text: str) -> float:
    """Score a single headline. Returns compound [-1, 1]."""
    scores = get_sia().polarity_scores(text)
    return round(scores["compound"], 4)


def score_headlines(headlines: list) -> float:
    """Average compound score over multiple headlines."""
    if not headlines:
        return 0.0
    scores = [score_headline(h) for h in headlines]
    return round(sum(scores) / len(scores), 4)


def interpret_sentiment(score: float) -> str:
    """Textual label for a compound score."""
    if score >= 0.5:
        return "STRONGLY POSITIVE"
    elif score >= 0.05:
        return "POSITIVE"
    elif score <= -0.5:
        return "STRONGLY NEGATIVE"
    elif score <= -0.05:
        return "NEGATIVE"
    return "NEUTRAL"
