"""Relevance rules for a Russian consumer technology and science channel."""

import re

TOPIC_KEYWORDS = {
    "gadgets": (
        "смартфон", "телефон", "iphone", "айфон", "android", "планшет",
        "ноутбук", "компьютер", "процессор", "видеокарт", "наушник",
        "телевизор", "монитор", "камер", "часы", "браслет", "гаджет",
        "робот-пылесос", "дрон", "консоль", "playstation", "xbox",
    ),
    "ai": (
        "искусственн", "нейросет", "нейронн", "ии ", " ии", "chatgpt",
        "openai", "gemini", "claude", "deepseek", "машинн обучение",
        "языковая модель", "генеративн", "робот", "беспилотн",
    ),
    "science": (
        "ученые", "учёные", "исследовател", "открыли", "обнаружили",
        "эксперимент", "исследование", "физик", "химик", "биолог",
        "медицин", "геном", "археолог", "динозавр", "квантов",
    ),
    "space": (
        "космос", "космическ", "ракет", "спутник", "астроном",
        "планет", "марс", "луна", "звезд", "звёзд", "телескоп",
        "nasa", "spacex", "роскосмос", "астероид", "галактик",
    ),
    "cybersecurity": (
        "уязвимост", "взлом", "хакер", "кибератак", "вирус", "шифровальщик",
        "утечк", "парол", "фишинг", "вредонос", "безопасност", "эксплойт",
    ),
    "software": (
        "приложени", "операционная система", "windows", "linux", "macos",
        "ios ", "обновлен", "обновлён", "браузер", "telegram", "whatsapp",
        "сервис", "программ", "игр", "steam",
    ),
}
TOPIC_PRIORITY = ("cybersecurity", "gadgets", "ai", "space", "science", "software")
NEWS_SIGNALS = (
    "представил", "анонсировал", "выпустил", "запустил", "показал",
    "создал", "разработал", "открыл", "обнаружил", "научил", "обновил",
    "появил", "стал доступ", "начал", "испытал", "установил рекорд",
    "запретил", "взломал", "утечк", "подтвердил", "удалось",
)
NOISE_KEYWORDS = (
    "скидк", "распродаж", "промокод", "купить дешевле", "цены снижены",
    "подборка", "топ-", "лучшие товары", "обзор", "тестируем", "сравнение",
    "инструкция", "как выбрать", "как установить", "гайд", "мнение",
    "слух", "инсайдер", "может выйти", "ожидается", "вероятно",
    "ваканси", "назначен", "конференция состоится", "итоги недели",
)


def is_relevant(news_item):
    """Accept a concrete Russian-language technology or science event."""
    title = news_item.get("title", "").casefold()
    description = news_item.get("description", "").casefold()
    text = f"{title} {description}"
    matched_topics = [
        topic for topic in TOPIC_PRIORITY
        if any(keyword in text for keyword in TOPIC_KEYWORDS[topic])
    ]
    news_item["matched_topics"] = matched_topics
    news_item["matched_brands"] = []
    news_item["event_category"] = matched_topics[0] if matched_topics else None
    news_item.setdefault("event_locations", [])

    if not re.search(r"[а-яё]", title):
        return False
    if any(keyword in text for keyword in NOISE_KEYWORDS):
        return False
    if not any(signal in text for signal in NEWS_SIGNALS):
        return False
    return bool(matched_topics)


def is_publishable(news_item):
    """Require enough source material and an editorial image for the post."""
    article_text = " ".join(news_item.get("article_text", "").split())
    return len(article_text) >= 100 and bool(news_item.get("image_url"))
