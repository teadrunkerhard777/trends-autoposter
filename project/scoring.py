"""Ranking for short, shareable stories about recognizable brands."""

import re


CATEGORY_SCORES = {
    "viral_event": 6,
    "collaboration": 5,
    "product_launch": 4,
    "campaign": 3,
    "rebrand": 3,
}

ICONIC_BRANDS = {
    "apple", "samsung", "netflix", "disney", "marvel", "nike", "adidas",
    "ikea", "coca_cola", "pepsi", "mcdonalds", "lego", "roblox", "gta",
}

MAJOR_BRANDS = {
    "sony", "xbox", "nintendo", "spotify", "telegram", "yandex", "sber",
    "tbank", "ozon", "wildberries", "vkusno_i_tochka", "burger_king",
    "vkusvill", "magnit", "pyaterochka", "gucci", "dior", "starbucks",
    "lays", "oreo", "kitkat", "nutella", "snickers", "twix", "tesla",
}

SHAREABLE_SIGNALS = (
    "first", "biggest", "strange", "unexpected", "viral", "limited edition",
    "впервые", "самый", "необыч", "странн", "вирус", "лимитк", "мем",
    "новый вкус", "украли", "запретили", "перестал работать",
)


def calculate_score(news_item):
    """Favor famous brands, unusual events, launches, and collaborations."""
    text = f"{news_item.get('title', '')} {news_item.get('description', '')}".casefold()
    topics = news_item.get("matched_topics", [])
    brands = set(news_item.get("matched_brands", []))
    score = max((CATEGORY_SCORES.get(topic, 0) for topic in topics), default=0)

    if brands & ICONIC_BRANDS:
        score += 4
    elif brands & MAJOR_BRANDS:
        score += 3
    else:
        score += 2

    if len(brands) > 1:
        score += 2
    if any(signal in text for signal in SHAREABLE_SIGNALS):
        score += 2
    if re.search(r"\b\d+(?:[.,]\d+)?\s*(?:%|млн|млрд|million|billion)\b", text):
        score += 1

    return score
