"""Project-owned stock-video search choices for technology news."""

import hashlib

PEXELS_VIDEO_QUERIES = {
    "gadgets": ("modern smartphone technology close up", "consumer electronics device studio"),
    "ai": ("artificial intelligence data center", "robotics laboratory technology"),
    "science": ("scientist laboratory research", "microscope science experiment"),
    "space": ("space telescope stars", "rocket launch space exploration"),
    "cybersecurity": ("cybersecurity computer code", "data security server room"),
    "software": ("software developer computer screen", "mobile application technology"),
}

STOCK_TOPIC_QUERIES = (
    (
        ("игр", "playstation", "xbox", "nintendo", "gta"),
        ("video game controller neon", "gaming setup close up"),
    ),
    (
        ("смартфон", "телефон", "iphone", "гаджет", "технолог"),
        ("smartphone technology close up", "modern device screen detail"),
    ),
    (
        ("космос", "ракет", "спутник", "планет", "луна", "марс"),
        ("space telescope stars", "rocket launch space exploration"),
    ),
    (
        ("нейросет", "искусственн", "openai", "робот"),
        ("artificial intelligence data center", "robotics laboratory technology"),
    ),
)


def pexels_query(news_item):
    """Return a neutral visual query, never a claim about the news event."""
    text = " ".join((
        str(news_item.get("title", "")),
        str(news_item.get("description", "")),
        str(news_item.get("article_text", ""))[:600],
    )).casefold()
    queries = None
    for keywords, topic_queries in STOCK_TOPIC_QUERIES:
        if any(keyword in text for keyword in keywords):
            queries = topic_queries
            break

    category = news_item.get("event_category")
    if queries is None:
        queries = PEXELS_VIDEO_QUERIES.get(
            category,
            ("modern business lifestyle city technology",),
        )
    identity = f"{news_item.get('url', '')}|{news_item.get('title', '')}"
    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    return queries[int.from_bytes(digest[:2], "big") % len(queries)]
