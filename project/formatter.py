"""Short Telegram presentation for viral stories about famous brands."""

import hashlib
import re
from datetime import datetime
from html import escape

from project.settings import CHANNEL_TITLE

from generation.text import fit_text_to_html_limit


MESSAGE_LIMIT = 4000
PHOTO_CAPTION_LIMIT = 1000
STOCK_VIDEO_CAPTION_LIMIT = 760
EXCERPT_LIMIT = 560

PUNCHLINES = {
    "collaboration": (
        "Вот это союз.",
        "Неожиданная пара.",
        "Коллаб, который мы заслужили.",
        "Хотим или листаем дальше?",
        "Кто бы мог подумать.",
        "",
        "",
    ),
    "product_launch": (
        "Уже в списке желаний.",
        "Проверим в деле.",
        "Очередь занимать?",
        "Нам это надо?",
        "Выглядит убедительно.",
        "",
        "",
    ),
    "campaign": (
        "Заметили. И запомнили.",
        "Маркетологи не зря старались.",
        "Сработало?",
        "Мимо такого не пройти.",
        "Смело.",
        "",
        "",
    ),
    "rebrand": (
        "Старый логотип вышел из чата.",
        "Привыкнем?",
        "Было лучше?",
        "Новый образ принят.",
        "Смело.",
        "",
        "",
    ),
    "viral_event": (
        "Интернет уже всё решил.",
        "Ну конечно.",
        "Сценаристы отдыхают.",
        "Этого никто не заказывал.",
        "Дальше — больше.",
        "Совпадение? Не думаем.",
        "",
        "",
    ),
}

CATEGORY_FOOTERS = {
    "collaboration": ("коллаборации", "#Коллаборации"),
    "product_launch": ("новинки", "#Новинки"),
    "campaign": ("реклама", "#Реклама"),
    "rebrand": ("ребрендинг", "#Ребрендинг"),
    "viral_event": ("инфоповоды", "#Инфоповоды"),
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
    title = _display_title(news_item.get("title", "Без заголовка"), publisher)
    category = news_item.get("event_category")
    topic, _ = CATEGORY_FOOTERS.get(category, ("главное", "#Бренды"))
    return {
        "eyebrow": topic.upper(),
        "title": title[:180],
        "brand": CHANNEL_TITLE.upper(),
        "tagline": "Коротко о главном",
    }


def format_stock_video_caption(news_item, asset):
    """Add API attribution without crowding the Telegram video caption."""
    caption = _format(news_item, STOCK_VIDEO_CAPTION_LIMIT)
    creator = escape(asset.creator_name)
    creator_url = escape(asset.creator_url, quote=True)
    page_url = escape(asset.page_url, quote=True)
    credit = (
        f'🎬 Видео: <a href="{creator_url}">{creator}</a> / '
        f'<a href="{page_url}">Pexels</a>'
    )
    return f"{caption}\n\n{credit}"


def _format(news_item, limit):
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
    punchline = _select_punchline(news_item, category)
    topic, hashtag = CATEGORY_FOOTERS.get(category, ("бренды", "#Бренды"))
    footer = (
        f"📅 {date}\n"
        f"📰 <b>{CHANNEL_TITLE}:</b> {topic}\n\n"
        f'🔗 <a href="{url}">Читать источник</a>\n\n'
        f"{hashtag}"
    )
    header = f"<b>{title}</b>"
    fixed_length = len(header) + len(punchline) + len(footer) + 8
    body = news_item.get("article_text") or news_item.get("description", "")
    body = _short_excerpt(body, raw_title)
    body = fit_text_to_html_limit(
        body,
        min(EXCERPT_LIMIT, max(0, limit - fixed_length)),
    )

    parts = [header]
    if body:
        parts.append(escape(body))
    if punchline:
        parts.append(escape(punchline))
    parts.append(footer)
    return "\n\n".join(parts)


def _select_punchline(news_item, category):
    """Choose a stable varied reaction, including intentionally silent posts."""

    variants = PUNCHLINES.get(category, ("",))
    identity = f"{news_item.get('url', '')}\n{news_item.get('title', '')}"
    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    return variants[int.from_bytes(digest[:4], "big") % len(variants)]


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
    return source.removesuffix(" — Google News")


def _display_title(title, source):
    display_source = _display_source(source)
    for separator in (" - ", " | "):
        suffix = f"{separator}{display_source}"
        if title.endswith(suffix):
            return title[:-len(suffix)]
    return title
