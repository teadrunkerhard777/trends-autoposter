"""Viral consumer-brand relevance rules and event categories."""

import re


BRAND_KEYWORDS = {
    "apple": ("apple", "iphone", "айфон"),
    "samsung": ("samsung", "самсунг"),
    "google": ("google", "android", "гугл"),
    "microsoft": ("microsoft", "windows", "майкрософт"),
    "sony": ("sony", "playstation", "сони", "плейстейшн"),
    "xbox": ("xbox",),
    "nintendo": ("nintendo", "нинтендо"),
    "netflix": ("netflix", "нетфликс"),
    "disney": ("disney", "дисней"),
    "marvel": ("marvel", "марвел", "мстител"),
    "warner_bros": ("warner bros", "warner brothers", "уорнер"),
    "hbo": ("hbo",),
    "spotify": ("spotify", "спотифай"),
    "tiktok": ("tiktok", "тикток", "tik tok"),
    "telegram": ("telegram", "телеграм"),
    "vk": ("вконтакте", "vk ", " vk", "вк "),
    "yandex": ("яндекс", "yandex"),
    "sber": ("сбер", "sber"),
    "tbank": ("т-банк", "тинькофф", "t-bank"),
    "ozon": ("ozon", "озон"),
    "wildberries": ("wildberries", "вайлдберриз"),
    "avito": ("авито", "avito"),
    "mts": ("мтс", "mts"),
    "beeline": ("билайн", "beeline"),
    "megafon": ("мегафон", "megafon"),
    "vkusno_i_tochka": ("вкусно — и точка", "вкусно и точка"),
    "burger_king": ("burger king", "бургер кинг"),
    "rostics": ("rostic", "ростикс"),
    "dodo": ("додо пицца", "dodo pizza"),
    "vkusvill": ("вкусвилл", "vkusvill"),
    "magnit": ("магнит",),
    "pyaterochka": ("пятерочк", "пятёрочк"),
    "lenta": ("«лента»", "лента запуст", "лента выпуст"),
    "ikea": ("ikea", "икеа"),
    "nike": ("nike", "найк"),
    "adidas": ("adidas", "адидас"),
    "puma": ("puma", "пума"),
    "crocs": ("crocs", "крокс"),
    "uniqlo": ("uniqlo", "юникло"),
    "zara": ("zara", "зара"),
    "gucci": ("gucci", "гуччи"),
    "dior": ("dior", "диор"),
    "chanel": ("chanel", "шанель"),
    "prada": ("prada", "прада"),
    "balenciaga": ("balenciaga", "баленсиага"),
    "coca_cola": ("coca-cola", "coca cola", "кока-кол"),
    "pepsi": ("pepsi", "пепси"),
    "starbucks": ("starbucks", "старбакс"),
    "red_bull": ("red bull", "ред булл"),
    "lays": ("lay’s", "lay's", "lays", "лейс"),
    "pringles": ("pringles", "принглс"),
    "oreo": ("oreo", "орео"),
    "kitkat": ("kitkat", "kit kat", "киткат"),
    "nutella": ("nutella", "нутелл"),
    "snickers": ("snickers", "сникерс"),
    "twix": ("twix", "твикс"),
    "mcdonalds": ("mcdonald", "макдоналд"),
    "kfc": ("kfc",),
    "lego": ("lego", "лего"),
    "barbie": ("barbie", "барби"),
    "roblox": ("roblox", "роблокс"),
    "minecraft": ("minecraft", "майнкрафт"),
    "gta": ("gta ", "gta vi", "гта "),
    "tesla": ("tesla", "тесла"),
    "bmw": ("bmw", "бмв"),
    "mercedes": ("mercedes", "мерседес"),
    "porsche": ("porsche", "порше"),
    "toyota": ("toyota", "тойота"),
    "lada": ("lada", "лада", "автоваз"),
    "moskvich": ("москвич",),
    "amazon": ("amazon", "амазон"),
    "aliexpress": ("aliexpress", "алиэкспресс"),
}

EVENT_KEYWORDS = {
    "collaboration": (
        "collaboration", "collab", "partnership", "teams up", " × ",
        "коллаборац", "совместн", "заколлаб", "объединил",
    ),
    "product_launch": (
        "launches", "launched", "unveils", "debuts", "new product",
        "limited edition", "new flavor", "new flavour", "collection",
        "выпустил", "выпустила", "выпустили", "представил", "представила",
        "запустил", "запустила", "завезли", "появится", "новый вкус",
        "новую линейку", "лимитк", "дроп", "коллекци",
    ),
    "campaign": (
        "campaign", "activation", "brand platform", "рекламн", "кампан",
        "промо", "наружк", "ролик", "постер", "маскот",
    ),
    "rebrand": (
        "rebrand", "new identity", "brand identity", "new logo", "редизайн",
        "ребрендинг", "айдентик", "новый логотип", "фирменный стиль",
    ),
    "viral_event": (
        "viral", "goes viral", "meme", "controversy", "banned", "pulled",
        "вирусит", "завирус", "мем", "скандал", "запретили", "перестал",
        "исчез", "украли", "подал в суд", "отказался", "не работает",
    ),
}

EVENT_PRIORITY = (
    "viral_event", "collaboration", "rebrand", "campaign", "product_launch",
)

NOISE_KEYWORDS = (
    "назначен", "назначена", "возглавил", "директор по маркетингу",
    "ваканси", "сотрудник", "персонал", "рынок труда", "конференц",
    "вебинар", "форум", "премия", "рейтинг", "дайджест", "обзор",
    "исследован", "опрос", "аналитик", "статистик", "как увеличить",
    "как создать", "почему бренду", "интервью", "финансовый отчет",
    "quarterly results", "earnings", "appoints", "how to ", "opinion:",
    "most iconic", "best collaborations", "топ-", "в эфире", "стратегия на",
    "инвестиц", "финансирован", "привлекла капитал", "привлек капитал",
)

TRUSTED_PUBLISHERS = (
    "adindex", "sostav", "new retail", "retail.ru", "postium", "rb.ru",
    "рбк", "коммерсант", "тасс", "риа новости", "vc.ru", "iphones.ru",
    "rozetked", "the verge", "techcrunch", "mashable", "engadget",
    "marketing dive", "retail dive", "the drum", "design week", "adweek",
    "fast company", "hypebeast", "highsnobiety", "complex", "sneaker news",
    "food & wine", "delish", "people", "variety", "deadline", "ign",
    "gamespot", "polygon", "nintendo life", "playstation lifestyle",
)


def is_relevant(news_item):
    """Accept recognizable-brand stories with a concrete, shareable event."""
    title = news_item.get("title", "").casefold()
    description = news_item.get("description", "").casefold()
    text = f"{title} {description}"
    matched_brands = [
        brand for brand, keywords in BRAND_KEYWORDS.items()
        if any(_contains_keyword(text, keyword) for keyword in keywords)
    ]
    title_topics = [
        category for category in EVENT_PRIORITY
        for keywords in (EVENT_KEYWORDS[category],)
        if any(keyword in title for keyword in keywords)
    ]
    all_topics = [
        category for category in EVENT_PRIORITY
        for keywords in (EVENT_KEYWORDS[category],)
        if any(keyword in text for keyword in keywords)
    ]
    if "rebrand" in title_topics:
        primary_topic = "rebrand"
    else:
        primary_topic = all_topics[0] if all_topics else None
    matched_topics = (
        [primary_topic]
        + [topic for topic in all_topics if topic != primary_topic]
        if primary_topic
        else []
    )

    news_item["matched_brands"] = matched_brands
    news_item["matched_topics"] = matched_topics
    news_item["event_category"] = matched_topics[0] if matched_topics else None
    news_item.setdefault("event_locations", [])

    if any(keyword in text for keyword in NOISE_KEYWORDS):
        return False
    if news_item.get("source", "").endswith("Google News"):
        publisher = news_item.get("publisher", "").casefold()
        if not any(name in publisher for name in TRUSTED_PUBLISHERS):
            return False
    return bool(matched_brands and matched_topics)


def _contains_keyword(text, keyword):
    """Match a brand alias only at a word boundary to avoid stem collisions."""
    value = keyword.strip()
    return bool(re.search(rf"(?<!\w){re.escape(value)}", text))
