from datetime import datetime, timezone

from processing.filters import add_scores, filter_by_minimum_score, filter_relevant
from project.filters import is_publishable, is_relevant
from project.formatter import format_photo_caption, format_post, format_stock_video_caption, format_video_card
from project.scoring import calculate_score
from project.settings import MIN_PUBLICATION_SCORE
from project.sources import SOURCES
from project.video import pexels_query


def item(title, description="", source="3DNews"):
    return {"title": title, "description": description, "url": "https://example.test/item", "source": source, "published_at": datetime(2026, 1, 2, tzinfo=timezone.utc)}


def test_project_has_six_direct_russian_technology_sources():
    assert len(SOURCES) == 6
    assert all(source["enabled"] for source in SOURCES)
    assert {source["type"] for source in SOURCES} == {"rss"}
    assert all("news.google.com" not in source["url"] for source in SOURCES)


def test_filter_accepts_concrete_technology_news_and_rejects_unrelated_story():
    accepted = item("Samsung представила новый складной смартфон")
    rejected = item("Городской совет обсудил правила парковки")
    assert filter_relevant([accepted, rejected], is_relevant) == [accepted]
    assert accepted["event_category"] == "gadgets"


def test_filter_categorizes_ai_science_space_and_security():
    examples = {
        "ai": "OpenAI представила новую нейросеть для работы с видео",
        "science": "Учёные обнаружили новый вид древнего животного",
        "space": "NASA запустило космический телескоп к далёкой планете",
        "cybersecurity": "Исследователи обнаружили уязвимость в менеджере паролей",
    }
    for category, title in examples.items():
        news = item(title)
        assert is_relevant(news) is True
        assert news["event_category"] == category


def test_filter_rejects_discounts_roundups_guides_and_rumors():
    titles = (
        "На смартфоны Samsung появились большие скидки",
        "Топ-10 лучших ноутбуков для дома",
        "Как выбрать новый телевизор: подробная инструкция",
        "Инсайдер рассказал, каким может выйти новый iPhone",
    )
    assert all(is_relevant(item(title)) is False for title in titles)


def test_publishable_post_requires_substantial_text_and_image():
    complete = item("Apple представила новый смартфон")
    complete["article_text"] = "Содержательный текст о характеристиках устройства. " * 4
    complete["image_url"] = "https://cdn.example.test/device.jpg"
    assert is_publishable(complete) is True
    assert is_publishable(complete | {"article_text": "Коротко."}) is False
    assert is_publishable(complete | {"image_url": None}) is False


def test_scoring_promotes_a_clear_gadget_launch():
    news = item("Apple официально представила новый смартфон", "Устройство впервые получило камеру с разрешением 200 Мп.")
    assert is_relevant(news) is True
    add_scores([news], calculate_score)
    assert news["score"] >= MIN_PUBLICATION_SCORE
    assert filter_by_minimum_score([news], MIN_PUBLICATION_SCORE) == [news]


def test_formatter_is_short_factual_and_has_topic_footer():
    news = item(
        "Samsung <X> представила смартфон",
        "Первый абзац про новый экран & камеру. Ещё один факт.\n\n"
        "Второй абзац о характеристиках устройства.\n\n"
        "Третий абзац о цене смартфона.\n\n"
        "Четвёртый абзац о начале продаж.\n\n"
        "Пятый лишний абзац.",
    )
    assert is_relevant(news) is True
    post = format_post(news)
    assert "Samsung &lt;X&gt;" in post
    assert post.startswith("🔵 <b>Samsung &lt;X&gt;")
    assert "экран &amp; камеру" in post
    assert "Четвёртый абзац" in post
    assert "Пятый лишний" not in post
    assert "Уже в списке желаний" not in post
    assert "📅 2 января 2026" in post
    assert "гаджеты" in post
    assert "📰 3DNews: гаджеты" in post
    assert "#гаджеты" in post
    assert ">Читать источник</a>" in post


def test_photo_caption_stays_inside_safe_limit():
    news = item("Apple представила новый смартфон", "слово " * 1000)
    news["event_category"] = "gadgets"
    assert len(format_photo_caption(news)) <= 1000


def test_video_query_and_card_follow_technology_topic():
    news = item("OpenAI представила новую нейросеть для видео")
    news["event_category"] = "ai"
    card = format_video_card(news)
    assert "artificial intelligence" in pexels_query(news) or "robotics" in pexels_query(news)
    assert card["eyebrow"] == "ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ"


def test_stock_video_caption_keeps_body_and_credit():
    class Asset:
        creator_name = "Author"
        creator_url = "https://example.test/author"
        page_url = "https://example.test/video"
        provider_name = "Stock"

    news = item("NASA запустило новый космический телескоп", "Аппарат изучит далёкие планеты.")
    news["article_text"] = news["description"]
    news["event_category"] = "space"
    caption = format_stock_video_caption(news, Asset())
    assert not caption.startswith("<b>")
    assert "Аппарат изучит" in caption
    assert "Author" in caption
