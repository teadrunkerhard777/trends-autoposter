"""Ranking for relevant Trends & Brands stories."""

import re


CATEGORY_SCORES = {
    "collaboration": 4, "rebrand": 4, "consumer_trend": 4,
    "retail_innovation": 3, "market_shift": 3, "product_launch": 2,
    "research": 2, "campaign": 2,
}
SOURCE_SCORES = {"Cossa": 2, "AdIndex": 2, "New Retail": 2, "Retail.ru": 2}
SIGNIFICANCE_KEYWORDS = (
    "first", "largest", "record", "global", "worldwide", "major", "впервые",
    "крупнейш", "рекорд", "глобальн", "по всему миру", "резко", "вдвое", "втрое",
)


def calculate_score(news_item):
    """Favor strong event types, direct sources, numbers, and scale."""
    text = f"{news_item.get('title', '')} {news_item.get('description', '')}".casefold()
    topics = news_item.get("matched_topics", [])
    score = max((CATEGORY_SCORES.get(topic, 0) for topic in topics), default=0)
    score += min(2, max(0, len(topics) - 1))
    score += SOURCE_SCORES.get(news_item.get("source"), 1)
    if re.search(r"\b\d+(?:[.,]\d+)?\s*(?:%|млн|млрд|million|billion)\b", text):
        score += 2
    if any(keyword in text for keyword in SIGNIFICANCE_KEYWORDS):
        score += 2
    return score
