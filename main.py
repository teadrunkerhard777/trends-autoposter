"""One understandable collection-to-publication pipeline."""

from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import FeatureNotFound
from bs4.exceptions import ParserRejectedMarkup
from requests import RequestException

from article.fetcher import (
    clean_article_text,
    extract_article_image_url,
    extract_article_text,
    fetch_article_html,
)
from collectors.html_collector import collect_html
from collectors.rss_collector import collect_rss
from collectors.static_collector import collect_static
from config import (
    DRY_RUN,
    DIVERSITY_SETTINGS,
    EVENT_DEDUP_SETTINGS,
    MAX_NEWS_PER_RUN,
    MEDIA_MODE,
    MIN_PUBLICATION_SCORE,
    NEWS_LOOKBACK_DAYS,
    PEXELS_API_KEY,
    PEXELS_VIDEO_ENABLED,
    POST_MODE,
    SOURCES,
    VIDEO_CANVAS_SIZE,
    VIDEO_DURATION_SECONDS,
    VIDEO_PUBLICATION_HOURS,
    VIDEO_STYLE,
    VIDEO_TIMEZONE,
)
from core.environment import configure_ssl
from core.run_lock import AlreadyRunningError, single_instance_lock
from processing.deduplicator import remove_duplicates
from processing.diversity import select_diverse
from processing.filters import (
    add_scores,
    filter_by_date,
    filter_by_minimum_score,
    filter_relevant,
    sort_by_score,
)
from project.filters import is_publishable, is_relevant
from generation.pexels import (
    PexelsError,
    download_stock_video,
    search_pexels_video,
)
from generation.video import (
    VideoRenderError,
    render_stock_video,
    render_video_card,
)
from project.formatter import (
    format_photo_caption,
    format_post,
    format_stock_video_caption,
    format_video_card,
)
from project.scoring import calculate_score
from project.sources import SOURCE_EXTRACTORS, SOURCE_STOP_MARKERS
from project.video import pexels_query
from publishing.telegram import (
    ImageDownloadError,
    download_image_temp,
    send_telegram_photo,
    send_telegram_post,
    send_telegram_video,
)
from storage.history import (
    add_to_history,
    has_video_slot,
    is_published,
    is_published_as_video,
    load_history,
    save_history,
)


COLLECTORS = {
    "rss": collect_rss,
    "html": collect_html,
    "static": collect_static,
}


def collect_enabled_news(sources=SOURCES):
    """Collect enabled sources while isolating unsupported types."""

    active = [source for source in sources if source.get("enabled", True)]
    all_news = []
    print(f"Enabled sources: {len(active)}")

    for source in active:
        collector = COLLECTORS.get(source.get("type"))

        if collector is None:
            print(f"Source warning ({source.get('name')}): unknown type")
            continue

        items = collector(source)
        print(f"Source: {source['name']} — {len(items)} items")
        all_news.extend(items)

    return all_news


def load_article_data(news_items, sources=None):
    """Fetch each page once, then derive text and image from the same HTML."""

    source_configs = _source_configs_by_name(sources)

    for item in news_items:
        if "article_text" in item and "image_url" in item:
            continue

        item.setdefault("article_text", "")
        item.setdefault("image_url", None)

        try:
            source_config = source_configs.get(item.get("source"))
            html = fetch_article_html(
                item["url"],
                source_config=source_config,
            )
            extracted = extract_article_text(
                html,
                source=item.get("source"),
                source_extractors=SOURCE_EXTRACTORS,
            )
            item["article_text"] = clean_article_text(
                extracted,
                source=item.get("source"),
                source_stop_markers=SOURCE_STOP_MARKERS,
            )
            item["image_url"] = extract_article_image_url(html, item["url"])
        except (RequestException, FeatureNotFound, ParserRejectedMarkup) as error:
            print(
                f"Article warning ({item.get('source')}): "
                f"{type(error).__name__}"
            )


def publish_selected_news(
    selected_news,
    history,
    dry_run,
    post_mode,
    send_post=send_telegram_post,
    send_photo=send_telegram_photo,
    send_video=send_telegram_video,
    download_image=download_image_temp,
    render_video=render_video_card,
    search_stock=search_pexels_video,
    download_stock=download_stock_video,
    render_stock=render_stock_video,
    add_history=add_to_history,
    event_settings=EVENT_DEDUP_SETTINGS,
    sources=None,
    video_slot=None,
    pexels_api_key=None,
):
    """Publish each selected item once and update history on confirmation."""

    history_changed = False
    source_configs = _source_configs_by_name(sources)

    for item in selected_news:
        post = format_post(item)
        caption = format_photo_caption(item)
        image_url = item.get("image_url")

        if dry_run:
            print("[DRY RUN] Telegram was not called")
            print(f"Media: {'video' if video_slot and image_url else 'photo/text'}")
            if video_slot:
                print(f"Video slot: {video_slot}")
            print(f"Image URL: {image_url or 'NOT FOUND'}")
            print(caption if image_url else post)
            continue

        if post_mode != "single":
            print(f"Unsupported POST_MODE: {post_mode}")
            continue

        succeeded = False
        uncertain = False

        if video_slot and image_url:
            temporary_image = None
            temporary_stock = None
            temporary_video = None
            video_caption = caption

            try:
                if PEXELS_VIDEO_ENABLED and pexels_api_key:
                    try:
                        asset = search_stock(
                            pexels_query(item),
                            pexels_api_key,
                            VIDEO_DURATION_SECONDS,
                        )
                        temporary_stock = download_stock(asset.file_url)
                        temporary_video = render_stock(
                            temporary_stock.path,
                            format_video_card(item),
                            VIDEO_STYLE,
                            VIDEO_CANVAS_SIZE,
                            VIDEO_DURATION_SECONDS,
                        )
                        video_caption = format_stock_video_caption(item, asset)
                    except (PexelsError, VideoRenderError, OSError) as error:
                        print(f"Pexels fallback warning: {type(error).__name__}")

                if temporary_video is None:
                    source_config = source_configs.get(item.get("source"))
                    temporary_image = download_image(
                        image_url,
                        source_config=source_config,
                    )
                    temporary_video = render_video(
                        temporary_image.path,
                        format_video_card(item),
                        VIDEO_STYLE,
                        VIDEO_CANVAS_SIZE,
                        VIDEO_DURATION_SECONDS,
                    )

                with temporary_video.path.open("rb") as video_file:
                    video_result = send_video(
                        video_file,
                        video_caption,
                        filename=temporary_video.path.name,
                    )

                succeeded = bool(video_result)
                uncertain = getattr(video_result, "uncertain", False)
                if succeeded:
                    item["publication_media"] = "video"
                    item["video_slot"] = video_slot
            except (ImageDownloadError, VideoRenderError, OSError) as error:
                print(f"Video fallback warning: {type(error).__name__}")
            finally:
                if temporary_video and temporary_video.path.exists():
                    temporary_video.path.unlink()
                if temporary_stock and temporary_stock.path.exists():
                    temporary_stock.path.unlink()
                if temporary_image and temporary_image.path.exists():
                    temporary_image.path.unlink()

        if image_url and not succeeded and not uncertain:
            photo_result = send_photo(image_url, caption)
            succeeded = bool(photo_result)
            uncertain = getattr(photo_result, "uncertain", False)

            if (
                not succeeded
                and not uncertain
                and getattr(photo_result, "remote_fetch_failed", False)
            ):
                temporary_image = None

                try:
                    source_config = source_configs.get(item.get("source"))
                    temporary_image = download_image(
                        image_url,
                        source_config=source_config,
                    )

                    with temporary_image.path.open("rb") as image_file:
                        file_result = send_photo(
                            image_file,
                            caption,
                            filename=temporary_image.path.name,
                            mime_type=temporary_image.mime_type,
                        )

                    succeeded = bool(file_result)
                    uncertain = getattr(file_result, "uncertain", False)
                except (ImageDownloadError, OSError) as error:
                    print(f"Photo fallback warning: {type(error).__name__}")
                finally:
                    if temporary_image and temporary_image.path.exists():
                        temporary_image.path.unlink()

        if not succeeded and not uncertain:
            text_result = send_post(post)
            succeeded = bool(text_result)
            uncertain = getattr(text_result, "uncertain", False)

        # Uncertain delivery may already exist in Telegram: never duplicate it.
        if succeeded:
            item.setdefault("publication_media", "photo" if image_url else "text")
            add_history(item, history, event_settings)
            history_changed = True

    return history_changed


def _source_configs_by_name(sources=None):
    """Index source HTTP settings by the source name stored on each item."""

    return {
        source.get("name"): source
        for source in (SOURCES if sources is None else sources)
        if source.get("name")
    }


def resolve_video_slot(media_mode, history, now=None):
    """Choose one daily local video slot, respecting confirmed history."""
    local_now = now or datetime.now(ZoneInfo(VIDEO_TIMEZONE))

    if local_now.tzinfo is None:
        local_now = local_now.replace(tzinfo=ZoneInfo(VIDEO_TIMEZONE))
    else:
        local_now = local_now.astimezone(ZoneInfo(VIDEO_TIMEZONE))

    if media_mode == "photo":
        return None
    if media_mode == "auto" and local_now.hour not in VIDEO_PUBLICATION_HOURS:
        return None

    slot_hour = local_now.hour
    slot = f"{local_now.date().isoformat()}-{slot_hour:02d}"
    return None if has_video_slot(history, slot) else slot


def run():
    configure_ssl()
    all_news = collect_enabled_news()
    fresh_news = filter_by_date(all_news, NEWS_LOOKBACK_DAYS)
    relevant_news = filter_relevant(fresh_news, is_relevant)
    add_scores(relevant_news, calculate_score)
    scored_news = filter_by_minimum_score(
        relevant_news,
        MIN_PUBLICATION_SCORE,
    )
    ranked_news = sort_by_score(scored_news)

    # Generic event fingerprints use article facts, so loading precedes dedup.
    load_article_data(ranked_news)
    publishable_news = [item for item in ranked_news if is_publishable(item)]
    unique_news = remove_duplicates(
        publishable_news,
        EVENT_DEDUP_SETTINGS,
        debug=DRY_RUN,
    )
    history = load_history()
    video_slot = resolve_video_slot(MEDIA_MODE, history)

    if DRY_RUN:
        new_news = unique_news.copy()
    elif MEDIA_MODE == "video":
        new_news = [
            item for item in unique_news
            if not is_published_as_video(item, history, EVENT_DEDUP_SETTINGS)
        ]
    else:
        new_news = [
            item for item in unique_news
            if not is_published(item, history, EVENT_DEDUP_SETTINGS)
        ]

    selected_news = select_diverse(
        new_news,
        MAX_NEWS_PER_RUN,
        DIVERSITY_SETTINGS,
    )
    print(f"Collected: {len(all_news)}")
    print(f"Fresh: {len(fresh_news)}")
    print(f"Relevant: {len(relevant_news)}")
    print(f"Minimum score: {len(scored_news)}")
    print(f"Publishable: {len(publishable_news)}")
    print(f"Unique: {len(unique_news)}")
    print(f"New: {len(new_news)}")
    print(f"Selected: {len(selected_news)}")
    print(f"Publication media: {'video' if video_slot else 'photo/text'}")

    history_changed = publish_selected_news(
        selected_news,
        history,
        DRY_RUN,
        POST_MODE,
        video_slot=video_slot,
        pexels_api_key=PEXELS_API_KEY,
    )

    if not DRY_RUN and history_changed:
        save_history(history)

    return selected_news


if __name__ == "__main__":
    try:
        with single_instance_lock("trends-brands-autoposter.lock"):
            run()
    except AlreadyRunningError:
        print("Autoposter is already running; this run was stopped.")
