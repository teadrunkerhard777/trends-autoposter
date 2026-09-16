from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image

from generation.video import render_stock_video, render_video_card
from main import resolve_video_slot


ZONE = ZoneInfo("Asia/Yekaterinburg")


def test_auto_video_slots_are_daytime_and_evening_only():
    assert resolve_video_slot("auto", [], datetime(2026, 9, 16, 13, tzinfo=ZONE)) == (
        "2026-09-16-13"
    )
    assert resolve_video_slot("auto", [], datetime(2026, 9, 16, 21, tzinfo=ZONE)) == (
        "2026-09-16-21"
    )
    assert resolve_video_slot("auto", [], datetime(2026, 9, 16, 11, tzinfo=ZONE)) is None


def test_used_video_slot_is_not_selected_again():
    history = [{
        "publication_media": "video",
        "video_slot": "2026-09-16-13",
    }]
    now = datetime(2026, 9, 16, 13, 30, tzinfo=ZONE)

    assert resolve_video_slot("auto", history, now) is None


def test_video_renderer_creates_streamable_mp4(tmp_path):
    image_path = tmp_path / "source.jpg"
    Image.new("RGB", (480, 360), "#2f5bd3").save(image_path)

    result = render_video_card(
        image_path,
        {
            "brand": "ТРЕНДЫ И БРЕНДЫ",
            "eyebrow": "НОВИНКИ",
            "title": "Яркий тестовый ролик для Telegram",
        },
        {
            "accent": "#FFD54A",
            "background": "#101319",
            "foreground": "#FFFFFF",
            "muted": "#D5D9E2",
        },
        (320, 400),
        1,
    )

    try:
        assert result.size_bytes > 1000
        assert b"ftyp" in result.path.read_bytes()[:64]
    finally:
        result.path.unlink()


def test_stock_video_renderer_adds_card_to_existing_motion(tmp_path):
    image_path = tmp_path / "source.jpg"
    Image.new("RGB", (320, 400), "#318f67").save(image_path)
    source = render_video_card(
        image_path,
        {"brand": "TEST", "eyebrow": "NEWS", "title": "Moving source"},
        {
            "accent": "#FFD54A", "background": "#101319",
            "foreground": "#FFFFFF", "muted": "#D5D9E2",
        },
        (320, 400),
        1,
    )
    result = None
    try:
        result = render_stock_video(
            source.path,
            {"brand": "TEST", "eyebrow": "NEWS", "title": "Stock overlay"},
            {
                "accent": "#FFD54A", "background": "#101319",
                "foreground": "#FFFFFF", "muted": "#D5D9E2",
            },
            (320, 400),
            1,
        )
        assert result.size_bytes > 1000
        assert b"ftyp" in result.path.read_bytes()[:64]
    finally:
        source.path.unlink()
        if result:
            result.path.unlink()
