from datetime import datetime, timezone

from storage.history import (
    add_to_history,
    has_video_slot,
    is_published,
    is_published_as_video,
    load_history,
    save_history,
)


def news(url="https://example.test/story"):
    return {
        "title": "Python package release",
        "url": url,
        "source": "Example",
        "published_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "description": "package release testing runner plugin benchmark community",
        "event_category": "python",
    }


def test_empty_history_round_trip(tmp_path):
    path = tmp_path / "published.json"
    save_history([], path)
    assert load_history(path) == []


def test_new_history_entry_contains_compact_fingerprint():
    history = []
    add_to_history(news(), history)

    assert history[0]["event_fingerprint"]["categories"] == ["python"]
    assert "article_text" not in history[0]


def test_legacy_history_without_fingerprint_remains_url_compatible():
    item = news()
    assert is_published(item, [{"url": item["url"]}]) is True
    assert is_published(item, [{"url": "https://other.test"}]) is False


def test_confirmed_video_slot_is_recorded_and_detected():
    item = news()
    item["publication_media"] = "video"
    item["video_slot"] = "2026-01-01-15"
    history = []

    add_to_history(item, history)

    assert has_video_slot(history, "2026-01-01-15") is True
    assert has_video_slot(history, "2026-01-01-19") is False


def test_video_dedup_ignores_photo_history_but_blocks_video_history():
    item = news()
    photo_entry = {"url": item["url"], "publication_media": "photo"}
    video_entry = {"url": item["url"], "publication_media": "video"}

    assert is_published_as_video(item, [photo_entry]) is False
    assert is_published_as_video(item, [video_entry]) is True
