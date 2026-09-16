"""Project-owned stock-video search choices for Trends & Brands."""

import hashlib

PEXELS_VIDEO_QUERIES = {
    "collaboration": (
        "creative team collaboration modern city",
        "fashion creative partnership studio",
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
        "social media smartphone city people",
        "people filming phone urban lifestyle",
    ),
}


def pexels_query(news_item):
    """Return a neutral visual query, never a claim about the news event."""
    category = news_item.get("event_category")
    queries = PEXELS_VIDEO_QUERIES.get(
        category,
        ("modern business lifestyle city technology",),
    )
    identity = f"{news_item.get('url', '')}|{news_item.get('title', '')}"
    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    return queries[int.from_bytes(digest[:2], "big") % len(queries)]
