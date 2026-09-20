"""Ranking for notable gadgets, AI, science, and technology news."""

import re

CATEGORY_SCORES = {
    "gadgets": 5, "ai": 5, "space": 5, "science": 4,
    "cybersecurity": 4, "software": 3,
}
HIGH_INTEREST_SIGNALS = (
    "впервые", "рекорд", "прорыв", "революцион", "официально",
    "представил", "выпустил", "обнаружил", "доказал", "запустил",
    "бесплатно", "доступен", "массов", "человек", "пользовател",
)


def calculate_score(news_item):
    """Favor clear launches, discoveries, and broadly useful developments."""
    text = f"{news_item.get('title', '')} {news_item.get('description', '')}".casefold()
    topics = news_item.get("matched_topics", [])
    score = max((CATEGORY_SCORES.get(topic, 0) for topic in topics), default=0)
    score += min(2, sum(signal in text for signal in HIGH_INTEREST_SIGNALS))
    if re.search(r"\b\d+(?:[.,]\d+)?\s*(?:%|млн|млрд|гб|тб|нм|км|лет)\b", text):
        score += 1
    if len(topics) > 1:
        score += 1
    return score
