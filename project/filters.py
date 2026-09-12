"""Relevance and event categories for Trends & Brands."""


EVENT_KEYWORDS = {
    "collaboration": ("collaboration", "collab", "partnership", "partners with", "коллаборац", "партнерств", "сотрудничеств", "совместн"),
    "rebrand": ("rebrand", "brand identity", "visual identity", "new identity", "new logo", "редизайн", "ребрендинг", "айдентик", "новый логотип", "фирменный стиль"),
    "campaign": ("campaign", "brand platform", "ad campaign", "activation", "кампан", "рекламн", "активац", "спецпроект"),
    "product_launch": ("launches", "launched", "unveils", "unveiled", "debuts", "introduces", "new product", "запустил", "запустила", "запустили", "представил", "представила", "представили", "выпустил", "выпустила", "новый продукт", "новую линейку", "вышел в новую категорию"),
    "consumer_trend": ("consumer trend", "consumer behavior", "consumer behaviour", "shopping trend", "shoppers", "customers increasingly", "потребительск", "покупатели стали", "покупатели назвали", "россияне стали", "спрос вырос", "спрос снизился", "популярность выросла", "предпочитают", "выбирают", "отношение покупателей"),
    "research": ("research", "survey", "study finds", "report finds", "исследован", "опрос", "аналитик", "статистик", "каждый третий", "половина покупателей", "три четверти"),
    "retail_innovation": ("store concept", "retail innovation", "new format", "flagship", "concept store", "новый формат", "флагман", "концепт-стор", "магазин нового формата", "онлайн-супермаркет"),
    "market_shift": ("acquires", "acquisition", "merger", "exits market", "enters market", "expands into", "market share", "приобрел", "приобрела", "покупает", "слияни", "вышел на рынок", "выходит на рынок", "покинул рынок", "доля рынка", "сменил владельца"),
}

SUBJECT_KEYWORDS = (
    "brand", "retail", "consumer", "shopper", "campaign", "product", "store",
    "commerce", "marketing", "packaging", "logo", "fashion", "beauty", "food",
    "бренд", "ретейл", "ритейл", "покупател", "потребител", "средний чек", "маркетинг",
    "реклам", "магазин", "маркетплейс", "упаковк", "логотип", "товар",
    "продукт", "мода", "косметик",
)

NOISE_KEYWORDS = (
    "ваканси", "сотрудник", "персонал", "специальност", "молодые специалист",
    "выбирают работу", "зарплат", "рынок труда",
    "назначен", "назначена", "возглавил", "возглавила", "конференц",
    "вебинар", "форум состоится", "премия объявила", "подать заявку",
    "рейтинг агентств", "дайджест", "как увеличить", "how to ", "tips for ",
    "opinion:", "awards shortlist", "job opening",
    "обзор", "главные события", "итоги недели", "roundup", "weekly recap",
)

STRONG_CATEGORIES = {"collaboration", "rebrand", "consumer_trend"}


def is_relevant(news_item):
    """Keep concrete brand actions and meaningful consumer trend signals."""
    title = news_item.get("title", "").casefold()
    text = f"{title} {news_item.get('description', '')}".casefold()
    title_topics = [
        category for category, keywords in EVENT_KEYWORDS.items()
        if any(keyword in title for keyword in keywords)
    ]
    matched_topics = title_topics or [
        category for category, keywords in EVENT_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]
    news_item["matched_topics"] = matched_topics
    news_item["event_category"] = matched_topics[0] if matched_topics else None
    news_item.setdefault("event_locations", [])

    if not matched_topics or any(keyword in text for keyword in NOISE_KEYWORDS):
        return False
    has_subject = any(keyword in title for keyword in SUBJECT_KEYWORDS)
    return has_subject or bool(STRONG_CATEGORIES.intersection(matched_topics))
