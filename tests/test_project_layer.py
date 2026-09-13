from datetime import datetime, timezone

from bs4 import BeautifulSoup

from processing.filters import add_scores, filter_by_minimum_score, filter_relevant
from project.filters import is_relevant
from project.formatter import _select_punchline, format_photo_caption, format_post
from project.scoring import calculate_score
from project.settings import MIN_PUBLICATION_SCORE
from project.sources import (
    SOURCES,
    extract_new_retail_article,
    extract_retail_article,
)


def item(title, description="", source="Postium Коллаборации"):
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
    news = item("Apple назначила нового директора по маркетингу")

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


def test_filter_rejects_evergreen_branding_explainer():
    news = item("Айдентика: что делает бренд узнаваемым")

    assert is_relevant(news) is False


def test_brand_alias_does_not_match_inside_unrelated_word():
    news = item("Маркетплейс запустил стратегию продаж")

    assert is_relevant(news) is False
    assert news["matched_brands"] == []


def test_google_news_requires_a_trusted_original_publisher():
    untrusted = item(
        "Apple выпустила лимитированный iPhone",
        source="Знаменитые бренды — Google News",
    )
    untrusted["publisher"] = "Unknown Viral Site"
    trusted = item(
        "Apple выпустила лимитированный iPhone",
        source="Знаменитые бренды — Google News",
    )
    trusted["publisher"] = "The Verge"

    assert is_relevant(untrusted) is False
    assert is_relevant(trusted) is True


def test_title_category_takes_priority_over_description_side_topics():
    news = item(
        "Apple представила новый логотип",
        "Проект создан в коллаборации с агентством.",
    )

    assert is_relevant(news) is True
    assert news["event_category"] == "rebrand"


def test_collaboration_in_description_beats_generic_launch_word():
    news = item(
        "adidas выпустил новые кроссовки",
        "Это совместная версия с известным художником.",
    )

    assert is_relevant(news) is True
    assert news["event_category"] == "collaboration"


def test_scoring_rewards_direct_source_numbers_and_multiple_signals():
    news = item(
        "Apple и Nike впервые выпустили совместную лимитку",
        "Коллаборация поступит в продажу завтра.",
    )
    assert is_relevant(news) is True

    add_scores([news], calculate_score)

    assert news["score"] >= MIN_PUBLICATION_SCORE
    assert filter_by_minimum_score([news], MIN_PUBLICATION_SCORE) == [news]


def test_formatter_is_short_lively_and_html_safe():
    news = item("Apple <X> выпустила лимитку", "Смелее & ярче. Вторая деталь. Третья лишняя.")
    assert is_relevant(news) is True

    post = format_post(news)

    assert "Apple &lt;X&gt;" in post
    assert "Смелее &amp; ярче" in post
    assert "Третья лишняя" not in post
    assert "Берём?" not in post
    assert "Почему это важно" not in post
    assert "📅 2 января 2026" in post
    assert "📰 <b>Тренды и Бренды:</b> новинки" in post
    assert ">Читать источник</a>" in post
    assert "#Новинки" in post
    assert 'href="https://example.test/item"' in post


def test_formatter_reactions_are_stable_but_varied_between_stories():
    reactions = set()

    for number in range(30):
        news = item(f"Apple выпустила новинку номер {number}")
        news["url"] = f"https://example.test/item-{number}"
        news["event_category"] = "product_launch"
        reaction = _select_punchline(news, "product_launch")
        reactions.add(reaction)
        assert reaction == _select_punchline(news, "product_launch")

    assert len(reactions) >= 5
    assert "" in reactions
    assert "Берём?" not in reactions


def test_formatter_uses_real_google_news_publisher():
    news = item(
        "Nike unveils new identity - Design Week",
        source="Знаменитые бренды — Google News",
    )
    news["publisher"] = "Design Week"
    assert is_relevant(news) is True

    post = format_post(news)

    assert "Nike unveils new identity - Design Week" not in post
    assert ">Читать источник</a>" in post
    assert "Google News" not in post


def test_formatter_removes_direct_source_suffix_from_title():
    news = item("LEGO выпустила новый набор | New Retail", source="New Retail")
    news["matched_topics"] = ["product_launch"]
    news["event_category"] = "product_launch"

    post = format_post(news)

    assert "LEGO выпустила новый набор | New Retail" not in post
    assert "LEGO выпустила новый набор" in post


def test_photo_caption_stays_inside_safe_limit():
    news = item("Apple представила новый логотип", "слово " * 1000)
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


def test_retail_extractor_skips_subscription_outside_story():
    soup = BeautifulSoup(
        '<div class="subscribe">Получайте новости первыми</div>'
        '<div class="contain__description"><p>Факты новости.</p></div>',
        "html.parser",
    )

    assert extract_retail_article(soup) == "Факты новости."
