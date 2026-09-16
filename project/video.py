"""Project-owned stock-video search choices for Trends & Brands."""

import hashlib

PEXELS_VIDEO_QUERIES = {
    "collaboration": (
        "product packaging creative studio close up",
        "two products colorful background close up",
    ),
    "product_launch": (
        "new product technology retail close up",
        "modern product unboxing colorful studio",
    ),
    "campaign": (
        "advertising production colorful studio",
        "creative marketing photo shoot",
    ),
    "rebrand": (
        "graphic design branding creative studio",
        "designer working typography color palette",
    ),
    "viral_event": (
        "social media smartphone screen close up",
        "phone camera urban lights close up",
    ),
}

STOCK_TOPIC_QUERIES = (
    (
        ("пицц", "чипс", "ресторан", "бургер", "еда", "напит", "кофе"),
        ("pizza close up restaurant food", "chips snack food close up"),
    ),
    (
        ("кроссов", "одежд", "мод", "fashion", "adidas", "nike"),
        ("fashion sneakers close up studio", "streetwear clothing detail"),
    ),
    (
        ("игр", "playstation", "xbox", "nintendo", "gta"),
        ("video game controller neon", "gaming setup close up"),
    ),
    (
        ("смартфон", "телефон", "iphone", "гаджет", "технолог"),
        ("smartphone technology close up", "modern device screen detail"),
    ),
    (
        ("космет", "макияж", "beauty", "парфюм"),
        ("beauty cosmetics product close up", "perfume makeup studio"),
    ),
    (
        ("автомоб", "машин", "tesla", "mercedes", "bmw"),
        ("modern car detail city", "electric car close up"),
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
