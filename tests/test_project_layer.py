from datetime import datetime, timezone

from processing.filters import add_scores, filter_by_minimum_score, filter_relevant
from project.filters import is_relevant
from project.formatter import format_photo_caption, format_post
from project.scoring import calculate_score


def item(title, description=""):
    return {
        "title": title,
        "description": description,
        "url": "https://example.test/item?a=1&b=2",
        "source": "Тест & источник",
        "published_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
    }


def test_filter_accepts_auto_moto_and_motorsport_but_rejects_celebrity_car():
    auto = item("Toyota представила новый кроссовер")
    moto = item("BMW обновила линейку мотоциклов")
    race = item("Пилот выиграл Гран-при Формулы-1")
    celebrity = item("Музыкант показал редкую машину из своей коллекции", "Певец рассказал подписчикам о покупке.")

    assert filter_relevant([auto, moto, race, celebrity], is_relevant) == [auto, moto, race]
    assert auto["event_category"] == "new_models"
    assert moto["event_category"] == "motorcycles"
    assert race["event_category"] == "motorsport"
    assert celebrity["matched_topics"] == []


def test_filter_rejects_unrelated_accident_news():
    assert not is_relevant(item("В ДТП с автомобилем погиб пешеход"))


def test_scoring_keeps_routine_racing_below_major_event():
    routine = item("Пилот рассказал о настройках перед этапом Формулы-1")
    major = item("Пилот выиграл Гран-при и возглавил чемпионат Формулы-1")
    for news in (routine, major):
        is_relevant(news)
    add_scores([routine, major], calculate_score)

    assert routine["score"] < 5
    assert major["score"] >= 5
    assert filter_by_minimum_score([routine, major], 5) == [major]


def test_formatter_escapes_html_and_uses_editorial_tags():
    news = item("Toyota <показала> кроссовер", "Быстрее & экономичнее")
    is_relevant(news)
    post = format_post(news)

    assert "Toyota &lt;показала&gt;" in post
    assert "Быстрее &amp; экономичнее" in post
    assert "#АвтоМотоНовости #Новинки" in post
    assert "Тест &amp; источник" in post
    assert 'href="https://example.test/item?a=1&amp;b=2"' in post


def test_formatter_removes_service_paragraphs_and_prefers_article_text():
    news = item("Honda представила новый мотоцикл", "Короткое описание")
    news.update({
        "event_category": "motorcycles",
        "article_text": "Honda раскрыла характеристики.\n\nФото: пресс-служба\n\nМодель поступит в продажу весной.",
    })
    post = format_post(news)

    assert "Honda раскрыла характеристики." in post
    assert "Модель поступит в продажу весной." in post
    assert "Фото: пресс-служба" not in post
    assert "#Мото" in post


def test_photo_caption_stays_inside_safe_limit():
    news = item("BMW представила новый автомобиль", "word & " * 1000)
    is_relevant(news)
    assert len(format_photo_caption(news)) <= 1000
