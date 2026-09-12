from datetime import datetime, timezone

from bs4 import BeautifulSoup

from processing.filters import add_scores, filter_by_minimum_score, filter_relevant
from project.filters import is_relevant
from project.formatter import format_photo_caption, format_post
from project.scoring import calculate_score
from project.settings import MIN_PUBLICATION_SCORE
from project.sources import SOURCES, extract_new_retail_article


def item(title, description="", source="Sostav"):
    return {
        "title": title,
        "description": description,
        "url": "https://example.test/item",
        "source": source,
        "published_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
    }


def test_project_has_eight_enabled_real_sources():
    assert len(SOURCES) == 8
    assert all(source["enabled"] for source in SOURCES)
    assert {source["type"] for source in SOURCES} == {"rss"}
    assert all(source["url"].startswith("https://") for source in SOURCES)


def test_filter_accepts_brand_event_and_rejects_unrelated_news():
    accepted = item("Dior и A24 объявили о новой коллаборации")
    rejected = item("Городской совет обсудил правила парковки")

    assert filter_relevant([accepted, rejected], is_relevant) == [accepted]
    assert accepted["event_category"] == "collaboration"
    assert rejected["matched_topics"] == []


def test_filter_rejects_routine_appointment_even_with_brand_words():
    news = item("Российский бренд назначил нового директора по маркетингу")

    assert is_relevant(news) is False


def test_filter_rejects_multi_story_roundup():
    news = item(
        "Глобальная реклама: главные события недели",
        "Новые кампании и партнерства известных брендов.",
    )

    assert is_relevant(news) is False


def test_filter_rejects_workforce_demand_research():
    news = item(
        "Как изменился спрос на линейных сотрудников",
        "Исследование рынка труда и дефицитных специальностей.",
    )

    assert is_relevant(news) is False


def test_title_category_takes_priority_over_description_side_topics():
    news = item(
        "Бренд представил новый логотип",
        "Проект создан в партнерстве с агентством.",
    )

    assert is_relevant(news) is True
    assert news["event_category"] == "rebrand"


def test_scoring_rewards_direct_source_numbers_and_multiple_signals():
    news = item(
        "Впервые 75% покупателей выбирают новый формат магазина",
        "Исследование показывает изменение потребительского поведения.",
    )
    assert is_relevant(news) is True

    add_scores([news], calculate_score)

    assert news["score"] >= MIN_PUBLICATION_SCORE
    assert filter_by_minimum_score([news], MIN_PUBLICATION_SCORE) == [news]


def test_formatter_escapes_html_and_adds_editorial_context():
    news = item("Бренд <X> представил новый логотип", "Смелее & ярче")
    assert is_relevant(news) is True

    post = format_post(news)

    assert "Бренд &lt;X&gt;" in post
    assert "Смелее &amp; ярче" in post
    assert "<b>Почему это важно:</b>" in post
    assert "#ребрендинг" in post
    assert 'href="https://example.test/item"' in post


def test_photo_caption_stays_inside_safe_limit():
    news = item("Бренд представил новый логотип", "слово " * 1000)
    assert is_relevant(news) is True

    assert len(format_photo_caption(news)) <= 1000


def test_new_retail_extractor_keeps_only_article_body():
    soup = BeautifulSoup(
        '<nav><p>Меню</p></nav><div itemprop="articleBody">'
        '<div>Главный вывод.</div><p>Подробности исследования.</p>'
        '<noindex>Служебный блок</noindex></div>',
        "html.parser",
    )

    assert extract_new_retail_article(soup) == (
        "Главный вывод.\n\nПодробности исследования."
    )
