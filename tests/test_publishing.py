from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

from generation.pexels import PexelsVideo, TemporaryStockVideo
from generation.pexels import PexelsError
from generation.pixabay import PixabayVideo, TemporaryPixabayVideo
from generation.video import TemporaryVideo
from main import publish_selected_news
from publishing.telegram import (
    IMAGE_DOWNLOAD_USER_AGENT,
    MAX_IMAGE_SIZE_BYTES,
    ImageDownloadError,
    TelegramSendResult,
    TemporaryImage,
    download_image_temp,
    send_telegram_photo,
)


def news(image_url=None):
    return {
        "title": "Python release",
        "url": "https://example.test/story",
        "source": "Example",
        "published_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "description": "Python software release",
        "article_text": "Python software release body",
        "image_url": image_url,
        "matched_topics": ["python"],
        "event_category": "python",
    }


def fail_if_called(*args, **kwargs):
    raise AssertionError("external function must not be called")


def test_dry_run_never_publishes_or_changes_history():
    history = []
    changed = publish_selected_news(
        [news("https://img.test/photo.jpg")],
        history,
        True,
        "single",
        send_post=fail_if_called,
        send_photo=fail_if_called,
        download_image=fail_if_called,
        add_history=fail_if_called,
    )

    assert changed is False
    assert history == []


def test_history_changes_once_after_confirmed_text_success():
    history = []
    additions = []

    def add(item, target, settings):
        additions.append(item["url"])
        target.append({"url": item["url"]})

    changed = publish_selected_news(
        [news()],
        history,
        False,
        "single",
        send_post=lambda text: TelegramSendResult(True),
        add_history=add,
    )

    assert changed is True
    assert additions == ["https://example.test/story"]
    assert len(history) == 1


def test_successful_remote_photo_does_not_call_text_fallback():
    history = []
    changed = publish_selected_news(
        [news("https://img.test/photo.jpg")],
        history,
        False,
        "single",
        send_post=fail_if_called,
        send_photo=lambda *args, **kwargs: TelegramSendResult(True),
    )

    assert changed is True
    assert len(history) == 1


def test_required_image_failure_never_falls_back_to_text_or_history():
    history = []
    changed = publish_selected_news(
        [news("https://img.test/photo.jpg")],
        history,
        False,
        "single",
        send_post=fail_if_called,
        send_photo=lambda *args, **kwargs: TelegramSendResult(
            False, "HTTP 400"
        ),
        require_image=True,
    )

    assert changed is False
    assert history == []


def test_video_slot_sends_native_video_and_records_slot(tmp_path):
    image_path = tmp_path / "photo.jpg"
    video_path = tmp_path / "clip.mp4"
    image_path.write_bytes(b"image")
    video_path.write_bytes(b"video")
    sent = []
    history = []

    changed = publish_selected_news(
        [news("https://img.test/photo.jpg")],
        history,
        False,
        "single",
        send_post=fail_if_called,
        send_photo=fail_if_called,
        send_video=lambda video, caption, **kwargs: (
            sent.append((video.read(), kwargs["filename"]))
            or TelegramSendResult(True)
        ),
        download_image=lambda *args, **kwargs: TemporaryImage(
            image_path, "image/jpeg", 5
        ),
        render_video=lambda *args, **kwargs: TemporaryVideo(video_path, 5),
        video_slot="2026-01-01-15",
    )

    assert changed is True
    assert sent == [(b"video", "clip.mp4")]
    assert history[0]["publication_media"] == "video"
    assert history[0]["video_slot"] == "2026-01-01-15"
    assert image_path.exists() is False
    assert video_path.exists() is False


def test_video_slot_prefers_credited_pexels_background(tmp_path):
    stock_path = tmp_path / "stock.mp4"
    rendered_path = tmp_path / "rendered.mp4"
    stock_path.write_bytes(b"stock")
    rendered_path.write_bytes(b"rendered")
    asset = PexelsVideo(
        file_url="https://video.test/portrait.mp4",
        page_url="https://www.pexels.com/video/123/",
        creator_name="Video Author",
        creator_url="https://www.pexels.com/@author",
        duration=12,
    )
    sent = []

    changed = publish_selected_news(
        [news("https://img.test/photo.jpg")],
        [],
        False,
        "single",
        send_post=fail_if_called,
        send_photo=fail_if_called,
        send_video=lambda video, caption, **kwargs: (
            sent.append((video.read(), caption)) or TelegramSendResult(True)
        ),
        download_image=fail_if_called,
        search_stock=lambda query, key, duration: asset,
        download_stock=lambda url: TemporaryStockVideo(stock_path, 5),
        render_stock=lambda *args: TemporaryVideo(rendered_path, 8),
        video_slot="2026-01-01-19",
        pexels_api_key="secret-key",
    )

    assert changed is True
    assert sent[0][0] == b"rendered"
    assert "Video Author" in sent[0][1]
    assert "Pexels" in sent[0][1]
    assert stock_path.exists() is False
    assert rendered_path.exists() is False


def test_video_slot_uses_pixabay_when_pexels_has_no_result(tmp_path):
    stock_path = tmp_path / "pixabay.mp4"
    rendered_path = tmp_path / "rendered.mp4"
    stock_path.write_bytes(b"stock")
    rendered_path.write_bytes(b"rendered")
    asset = PixabayVideo(
        file_url="https://cdn.test/portrait.mp4",
        page_url="https://pixabay.com/videos/id-456/",
        creator_name="Pixabay Author",
        creator_url="https://pixabay.com/users/author-42/",
        duration=12,
    )
    sent = []

    changed = publish_selected_news(
        [news("https://img.test/photo.jpg")],
        [],
        False,
        "single",
        send_post=fail_if_called,
        send_photo=fail_if_called,
        send_video=lambda video, caption, **kwargs: (
            sent.append((video.read(), caption)) or TelegramSendResult(True)
        ),
        download_image=fail_if_called,
        search_stock=lambda *args: (_ for _ in ()).throw(
            PexelsError("no result")
        ),
        search_pixabay=lambda *args: asset,
        download_pixabay=lambda url: TemporaryPixabayVideo(stock_path, 5),
        render_stock=lambda *args: TemporaryVideo(rendered_path, 8),
        video_slot="2026-01-01-21",
        pexels_api_key="pexels-key",
        pixabay_api_key="pixabay-key",
    )

    assert changed is True
    assert sent[0][0] == b"rendered"
    assert "Pixabay Author" in sent[0][1]
    assert "Pixabay" in sent[0][1]
    assert stock_path.exists() is False
    assert rendered_path.exists() is False


def test_confirmed_remote_fetch_error_uses_temporary_file(tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"image")
    calls = []
    downloads = []
    source_config = {
        "name": "Example",
        "headers": {"User-Agent": "Source Browser"},
        "retries": 2,
    }

    def send_photo(photo, caption, **kwargs):
        calls.append(type(photo).__name__)

        if isinstance(photo, str):
            return TelegramSendResult(
                False,
                "failed to get HTTP URL content",
                remote_fetch_failed=True,
            )

        return TelegramSendResult(True)

    def download_image(url, source_config=None):
        downloads.append((url, source_config))
        return TemporaryImage(image_path, "image/jpeg", 5)

    changed = publish_selected_news(
        [news("https://img.test/photo.jpg")],
        [],
        False,
        "single",
        send_post=fail_if_called,
        send_photo=send_photo,
        download_image=download_image,
        sources=[source_config],
    )

    assert changed is True
    assert calls == ["str", "BufferedReader"]
    assert downloads == [("https://img.test/photo.jpg", source_config)]
    assert image_path.exists() is False


class ImageResponse:
    def __init__(self, content_type="image/jpeg", chunks=None, size=None):
        self.headers = {"Content-Type": content_type}
        if size is not None:
            self.headers["Content-Length"] = str(size)
        self.chunks = [b"image"] if chunks is None else chunks
        self.closed = False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        return iter(self.chunks)

    def close(self):
        self.closed = True


def test_image_download_uses_source_headers(monkeypatch):
    response = ImageResponse()
    request = {}

    def get(url, **kwargs):
        request.update(url=url, **kwargs)
        return response

    monkeypatch.setattr("publishing.telegram.requests.get", get)
    result = download_image_temp(
        "https://img.test/photo.jpg",
        source_config={
            "headers": {
                "User-Agent": "Source Browser",
                "Referer": "https://example.test/",
            },
            "retries": 0,
        },
    )

    try:
        assert request["headers"] == {
            "User-Agent": "Source Browser",
            "Referer": "https://example.test/",
        }
        assert request["stream"] is True
        assert response.closed is True
    finally:
        result.path.unlink()


def test_image_download_retries_temporary_ssl_error(monkeypatch):
    response = ImageResponse()
    calls = []

    def get(*args, **kwargs):
        calls.append(kwargs["headers"])
        if len(calls) == 1:
            raise requests.exceptions.SSLError("temporary")
        return response

    monkeypatch.setattr("publishing.telegram.requests.get", get)
    monkeypatch.setattr("publishing.telegram.time.sleep", lambda delay: None)
    result = download_image_temp(
        "https://img.test/photo.jpg",
        source_config={"retries": 1},
    )

    try:
        assert len(calls) == 2
        assert calls[0]["User-Agent"] == IMAGE_DOWNLOAD_USER_AGENT
    finally:
        result.path.unlink()


def test_image_download_raises_after_retries_are_exhausted(monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise requests.ConnectionError("temporary")

    monkeypatch.setattr("publishing.telegram.requests.get", fail)
    monkeypatch.setattr("publishing.telegram.time.sleep", lambda delay: None)

    with pytest.raises(ImageDownloadError, match="ConnectionError"):
        download_image_temp(
            "https://img.test/photo.jpg",
            source_config={"retries": 2},
        )

    assert len(calls) == 3


def test_image_download_rejects_non_image_content_type(monkeypatch):
    response = ImageResponse(content_type="text/html")
    monkeypatch.setattr(
        "publishing.telegram.requests.get",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(ImageDownloadError, match="invalid Content-Type"):
        download_image_temp("https://img.test/photo.jpg")

    assert response.closed is True


def test_image_download_rejects_declared_oversized_file(monkeypatch):
    response = ImageResponse(size=MAX_IMAGE_SIZE_BYTES + 1)
    monkeypatch.setattr(
        "publishing.telegram.requests.get",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(ImageDownloadError, match="exceeds 10 MiB"):
        download_image_temp("https://img.test/photo.jpg")

    assert response.closed is True


def test_read_timeout_result_does_not_retry_or_fallback():
    history = []
    changed = publish_selected_news(
        [news("https://img.test/photo.jpg")],
        history,
        False,
        "single",
        send_post=fail_if_called,
        send_photo=lambda *args, **kwargs: TelegramSendResult(
            False, "ReadTimeout", uncertain=True
        ),
        download_image=fail_if_called,
    )

    assert changed is False
    assert history == []


def test_sender_marks_real_read_timeout_uncertain_without_retry(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-chat")
    calls = []

    def timeout(*args, **kwargs):
        calls.append(1)
        raise requests.ReadTimeout

    monkeypatch.setattr("publishing.telegram.requests.post", timeout)
    result = send_telegram_photo(
        "https://img.test/photo.jpg",
        "caption",
    )

    assert result.uncertain is True
    assert len(calls) == 1
