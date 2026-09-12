"""Telegram presentation for the Trends & Brands channel."""

from datetime import datetime
from html import escape

from generation.text import fit_text_to_html_limit


MESSAGE_LIMIT = 4000
PHOTO_CAPTION_LIMIT = 1000

CATEGORY_LABELS = {
    "collaboration": "коллаборация",
    "rebrand": "ребрендинг",
    "campaign": "кампания",
    "product_launch": "новыйпродукт",
    "consumer_trend": "тренды",
    "research": "исследование",
    "retail_innovation": "ритейл",
    "market_shift": "рынок",
}

CATEGORY_INSIGHTS = {
    "collaboration": "Коллаборации помогают брендам обмениваться аудиториями и быстро входить в новые культурные контексты.",
    "rebrand": "Изменение айдентики часто показывает, как бренд переосмысляет аудиторию, категорию или своё место на рынке.",
    "campaign": "Кампания показывает, за какие смыслы и способы привлечения внимания сейчас конкурируют бренды.",
    "product_launch": "Новый продукт может быть ранним сигналом изменения спроса или появления новой категории.",
    "consumer_trend": "Это заметный сигнал изменения потребительского поведения, за которым могут последовать другие бренды.",
    "research": "Данные помогают отличить устойчивое изменение поведения от единичного инфоповода.",
    "retail_innovation": "Новый формат торговли показывает, как меняются ожидания покупателей и сам покупательский опыт.",
    "market_shift": "Изменение на рынке может повлиять на конкуренцию, доступность брендов и привычки покупателей.",
}


def format_post(news_item):
    """Build one HTML-safe text message."""

    return _format(news_item, MESSAGE_LIMIT)


def format_photo_caption(news_item):
    """Build one shorter HTML-safe photo caption."""

    return _format(news_item, PHOTO_CAPTION_LIMIT)


def _format(news_item, limit):
    title = escape(news_item.get("title", "Untitled")[:500])
    source = escape(news_item.get("source", "Unknown source"))
    url = escape(news_item.get("url", ""), quote=True)
    date = _format_date(news_item.get("published_at"))
    topics = news_item.get("matched_topics", [])
    tags = " ".join(
        f"#{CATEGORY_LABELS.get(topic, topic).replace(' ', '')}"
        for topic in topics[:3]
    )
    footer = (
        f"📅 {date}\n"
        f"📰 {source}\n\n"
        f'🔗 <a href="{url}">Источник</a>'
    )

    if tags:
        footer = f"{footer}\n\n{tags}"

    header = f"⚡️ <b>{title}</b>"
    insight = CATEGORY_INSIGHTS.get(news_item.get("event_category"))
    insight_block = f"\n\n<b>Почему это важно:</b> {escape(insight)}" if insight else ""
    fixed_length = len(header) + len(insight_block) + len(footer) + 4
    body = (
        news_item.get("article_text")
        or news_item.get("description", "")
    )
    body = fit_text_to_html_limit(body, max(0, limit - fixed_length))

    if body:
        return f"{header}\n\n{escape(body)}{insight_block}\n\n{footer}"

    return f"{header}{insight_block}\n\n{footer}"


def _format_date(value):
    if not isinstance(value, datetime):
        return "дата не указана"

    return value.strftime("%d.%m.%Y")
