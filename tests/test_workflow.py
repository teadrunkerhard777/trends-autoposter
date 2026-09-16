from pathlib import Path


WORKFLOW = Path(".github/workflows/autoposter.yml")
VIDEO_WORKFLOW = Path(".github/workflows/video-autoposter.yml")


def test_workflow_is_external_cron_ready_and_safe():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "schedule:" not in text
    assert "cancel-in-progress: false" in text
    assert 'AUTOPOSTER_DRY_RUN: "false"' in text
    assert 'AUTOPOSTER_MEDIA_MODE: "photo"' in text
    assert "TELEGRAM_BOT_TOKEN" in text
    assert "TELEGRAM_CHAT_ID" in text
    assert "git add storage/published.json" in text
    assert "git add ." not in text


def test_video_workflow_is_separate_external_cron_and_forces_video():
    regular = WORKFLOW.read_text(encoding="utf-8")
    video = VIDEO_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in video
    assert "schedule:" not in video
    assert 'AUTOPOSTER_MEDIA_MODE: "video"' in video
    assert "PEXELS_API_KEY" in video
    assert "PIXABAY_API_KEY" in video
    assert "actions/cache@v4" in video
    assert "PEXELS_API_KEY" not in regular
    assert "group: trends-brands-autoposter" in regular
    assert "group: trends-brands-autoposter" in video
    assert "cancel-in-progress: false" in video
    assert "git add storage/published.json" in video
    assert "git add ." not in video
