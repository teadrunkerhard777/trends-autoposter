"""Official Pixabay video search with the required short-lived query cache."""

import hashlib
import json
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import requests


PIXABAY_VIDEO_SEARCH_URL = "https://pixabay.com/api/videos/"
PIXABAY_CACHE_PATH = Path(".cache/pixabay/searches.json")
PIXABAY_CACHE_SECONDS = 24 * 60 * 60
MAX_STOCK_DOWNLOAD_BYTES = 80 * 1024 * 1024


@dataclass(frozen=True)
class PixabayVideo:
    file_url: str
    page_url: str
    creator_name: str
    creator_url: str
    duration: int
    provider_name: str = "Pixabay"


@dataclass(frozen=True)
class TemporaryPixabayVideo:
    path: Path
    size_bytes: int


class PixabayError(Exception):
    """Expected Pixabay lookup, cache, or download failure."""


def search_pixabay_video(query, api_key, minimum_duration=8, cache_path=None):
    """Find a safe portrait MP4 and cache API responses for 24 hours."""
    if not api_key:
        raise PixabayError("PIXABAY_API_KEY is missing")

    params = {
        "key": api_key,
        "q": query,
        "lang": "en",
        "video_type": "film",
        "safesearch": "true",
        "order": "popular",
        "per_page": 50,
    }
    cache_file = Path(cache_path or PIXABAY_CACHE_PATH)
    cache_key = hashlib.sha256(query.casefold().encode("utf-8")).hexdigest()
    data = _read_cache(cache_file, cache_key)

    if data is None:
        try:
            response = requests.get(
                PIXABAY_VIDEO_SEARCH_URL,
                params=params,
                timeout=(10, 30),
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            raise PixabayError(type(error).__name__) from error
        if not isinstance(data, dict):
            raise PixabayError("unexpected Pixabay response")
        _write_cache(cache_file, cache_key, data)

    candidates = []
    for video in data.get("hits", []):
        if int(video.get("duration") or 0) < minimum_duration:
            continue
        renditions = [
            rendition for rendition in (video.get("videos") or {}).values()
            if rendition.get("url")
            and int(rendition.get("height") or 0) > int(rendition.get("width") or 0)
            and int(rendition.get("size") or 0) <= MAX_STOCK_DOWNLOAD_BYTES
        ]
        if not renditions:
            continue
        selected = min(
            renditions,
            key=lambda rendition: abs(int(rendition.get("width") or 0) - 1080),
        )
        username = str(video.get("user") or "Pixabay creator")
        user_id = int(video.get("user_id") or 0)
        profile_slug = quote(username.replace(" ", "-"))
        creator_url = (
            f"https://pixabay.com/users/{profile_slug}-{user_id}/"
            if user_id else "https://pixabay.com/"
        )
        candidates.append(PixabayVideo(
            file_url=selected["url"],
            page_url=str(video.get("pageURL") or "https://pixabay.com/videos/"),
            creator_name=username,
            creator_url=creator_url,
            duration=int(video.get("duration") or 0),
        ))

    if not candidates:
        raise PixabayError("no suitable portrait video")
    return candidates[0]


def download_pixabay_video(video_url):
    """Download Pixabay media instead of permanently hotlinking its CDN."""
    response = None
    temp_path = None
    completed = False
    try:
        response = requests.get(video_url, timeout=(10, 45), stream=True)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "video/mp4" not in content_type.casefold():
            raise PixabayError("Pixabay file is not MP4")

        with tempfile.NamedTemporaryFile(
            prefix="autoposter-pixabay-", suffix=".mp4", delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)
            downloaded = 0
            for chunk in response.iter_content(chunk_size=128 * 1024):
                if not chunk:
                    continue
                downloaded += len(chunk)
                if downloaded > MAX_STOCK_DOWNLOAD_BYTES:
                    raise PixabayError("Pixabay video exceeds download limit")
                temp_file.write(chunk)
        if downloaded == 0:
            raise PixabayError("Pixabay video is empty")
        completed = True
        return TemporaryPixabayVideo(temp_path, downloaded)
    except requests.RequestException as error:
        raise PixabayError(type(error).__name__) from error
    finally:
        if response is not None:
            response.close()
        if temp_path and temp_path.exists() and not completed:
            temp_path.unlink()


def _read_cache(cache_path, cache_key):
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        entry = cache.get(cache_key, {})
        if time.time() - float(entry.get("saved_at", 0)) < PIXABAY_CACHE_SECONDS:
            return entry.get("data")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return None


def _write_cache(cache_path, cache_key, data):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        if not isinstance(cache, dict):
            cache = {}
    except (OSError, json.JSONDecodeError):
        cache = {}
    cache[cache_key] = {"saved_at": time.time(), "data": data}
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="pixabay-cache-",
        suffix=".json",
        dir=cache_path.parent,
        delete=False,
    ) as temp_file:
        json.dump(cache, temp_file, ensure_ascii=False)
        temp_path = Path(temp_file.name)
    temp_path.replace(cache_path)
