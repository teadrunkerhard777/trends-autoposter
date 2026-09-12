"""Ranking rules for the auto and motorcycle channel."""


TOPIC_SCORES = {
    "safety_recalls": 7, "motorcycles": 5, "market": 5, "industry": 4,
    "new_models": 4, "technology": 3, "ownership": 3, "motorsport": 2,
}

MAJOR_MOTORSPORT_SIGNALS = (
    "победил", "выиграл", "чемпион", "титул", "подиум", "авария",
    "дисквалифиц", "штраф", "отмен", "календар", "контракт",
    "официально", "рекорд", "завершил карьер", "дебютирует",
)

IMPORTANCE_BONUSES = {
    "official": (2, ("официально", "объявил", "подтвердил")),
    "russia": (2, ("в россии", "россиян", "российск")),
    "recall": (2, ("отзывает", "отзывн", "опасн", "дефект")),
    "production": (1, ("производств", "конвейер", "завод", "сборк")),
}

LOW_VALUE_PENALTIES = {
    "rumor": (3, ("слух", "может представить", "предположительно")),
    "auction": (2, ("выставили на продажу", "продадут на аукционе")),
    "ranking": (2, ("топ-", "назвали лучшие", "назвали худшие")),
    "celebrity": (4, ("знаменитост", "певец", "певица", "блогер")),
}


def calculate_score(news_item):
    """Rank relevant stories by usefulness and event importance."""

    title = str(news_item.get("title", "")).casefold()
    text = f"{title} {news_item.get('description', '')}".casefold()
    topics = news_item.get("matched_topics", [])
    score = sum(TOPIC_SCORES.get(topic, 0) for topic in topics)
    score += sum(points for points, keywords in IMPORTANCE_BONUSES.values() if any(keyword in text for keyword in keywords))
    score -= sum(points for points, keywords in LOW_VALUE_PENALTIES.values() if any(keyword in text for keyword in keywords))
    if "motorsport" in topics and any(signal in title for signal in MAJOR_MOTORSPORT_SIGNALS):
        score += 4
    return max(0, score)
