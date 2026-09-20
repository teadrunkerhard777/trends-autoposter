"""Compact Telegram presentation for technology and science news."""

import re
from datetime import datetime
from html import escape

from project.settings import CHANNEL_TITLE

from generation.text import fit_text_to_html_limit


MESSAGE_LIMIT = 4000
PHOTO_CAPTION_LIMIT = 1000
STOCK_VIDEO_CAPTION_LIMIT = 760
EXCERPT_LIMIT = 560

CATEGORY_FOOTERS = {
    "gadgets": ("гаджеты", "#Гаджеты"),
    "ai": ("искусственный интеллект", "#ИИ"),
    "science": ("наука", "#Наука"),
    "space": ("космос", "#Космос"),
    "cybersecurity": ("кибербезопасность", "#Кибербезопасность"),
    "software": ("технологии", "#Технологии"),
}

MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)


def format_post(news_item):
    """Build one short HTML-safe text message."""
    return _format(news_item, MESSAGE_LIMIT)


def format_photo_caption(news_item):
    """Build one short caption that works with the story image."""
    return _format(news_item, PHOTO_CAPTION_LIMIT)


def format_video_card(news_item):
    """Return short plain-text copy to burn into a branded video card."""
    publisher = news_item.get("publisher") or _display_source(
        news_item.get("source", "")
    )
    category = news_item.get("event_category")
    title = _display_title(news_item.get("title", "Без заголовка"), publisher)
    title = _short_video_title(title, category)
    topic, _ = CATEGORY_FOOTERS.get(category, ("главное", "#Бренды"))
    return {
        "eyebrow": topic.upper(),
        "title": title,
        "brand": CHANNEL_TITLE.upper(),
    }


def format_stock_video_caption(news_item, asset):
    """Add API attribution without crowding the Telegram video caption."""
    caption = _format(news_item, STOCK_VIDEO_CAPTION_LIMIT, include_header=False)
    creator = escape(asset.creator_name)
    creator_url = escape(asset.creator_url, quote=True)
    page_url = escape(asset.page_url, quote=True)
    provider = escape(getattr(asset, "provider_name", "Pexels"))
    credit = (
        f'🎬 Видео: <a href="{creator_url}">{creator}</a> / '
        f'<a href="{page_url}">{provider}</a>'
    )
    return f"{caption}\n\n{credit}"


def _format(news_item, limit, include_header=True):
    source_name = news_item.get("source", "Неизвестный источник")
    publisher_name = news_item.get("publisher") or _display_source(source_name)
    raw_title = _display_title(
        news_item.get("title", "Без заголовка"),
        publisher_name,
    )
    title = escape(raw_title[:500])
    url = escape(news_item.get("url", ""), quote=True)
    date = _format_date(news_item.get("published_at"))
    category = news_item.get("event_category")
    topic, hashtag = CATEGORY_FOOTERS.get(category, ("технологии", "#Технологии"))
    footer = (
        f"📅 {date}\n"
        f"📰 <b>{CHANNEL_TITLE}:</b> {topic}\n\n"
        f'🔗 <a href="{url}">Читать источник</a>\n\n'
        f"{hashtag}"
    )
    header = f"<b>{title}</b>"
    fixed_length = (
        (len(header) if include_header else 0)
        + len(footer)
        + 8
    )
    body = news_item.get("article_text") or news_item.get("description", "")
    body = _short_excerpt(body, raw_title)
    body = fit_text_to_html_limit(
        body,
        min(EXCERPT_LIMIT, max(0, limit - fixed_length)),
    )

    parts = [header] if include_header else []
    if body:
        parts.append(escape(body))
    parts.append(footer)
    return "\n\n".join(parts)


def _short_video_title(title, category):
    """Keep overlay copy punchy and avoid repeating a full article headline."""
    normalized = " ".join(str(title).split())
    if len(normalized) <= 88:
        return normalized
    shortened = normalized[:85].rsplit(" ", 1)[0].rstrip(" ,:;—-")
    return f"{shortened}…"


def _short_excerpt(text, title):
    normalized = " ".join((text or "").split())
    if not normalized:
        return ""

    display_title = " ".join(title.split())
    if normalized.startswith(display_title):
        normalized = normalized[len(display_title):].strip(" -—|·")

    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    return " ".join(sentences[:2]).strip()


def _format_date(value):
    if not isinstance(value, datetime):
        return "дата не указана"
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"


def _display_source(source):
    return source


def _display_title(title, source):
    display_source = _display_source(source)
    for separator in (" - ", " | "):
        suffix = f"{separator}{display_source}"
        if title.endswith(suffix):
            return title[:-len(suffix)]
    return title
