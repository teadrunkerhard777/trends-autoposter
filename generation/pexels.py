"""Minimal official Pexels API client for optional stock-video backgrounds."""

import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests


PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/v1/videos/search"
MAX_STOCK_DOWNLOAD_BYTES = 80 * 1024 * 1024


@dataclass(frozen=True)
class PexelsVideo:
    file_url: str
    page_url: str
    creator_name: str
    creator_url: str
    duration: int


@dataclass(frozen=True)
class TemporaryStockVideo:
    path: Path
    size_bytes: int


class PexelsError(Exception):
    """Expected Pexels lookup or download failure."""


def search_pexels_video(query, api_key, minimum_duration=8):
    """Find a portrait MP4 using the documented Pexels search endpoint."""
    if not api_key:
        raise PexelsError("PEXELS_API_KEY is missing")

    try:
        response = requests.get(
            PEXELS_VIDEO_SEARCH_URL,
            headers={"Authorization": api_key},
            params={
                "query": query,
                "orientation": "portrait",
                "size": "medium",
                "locale": "en-US",
                "per_page": 15,
            },
            timeout=(10, 30),
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        raise PexelsError(type(error).__name__) from error

    if not isinstance(data, dict):
        raise PexelsError("unexpected Pexels response")

    candidates = []
    for video in data.get("videos", []):
        if int(video.get("duration") or 0) < minimum_duration:
            continue
        files = [
            entry for entry in video.get("video_files", [])
            if entry.get("file_type") == "video/mp4"
            and entry.get("link")
            and int(entry.get("height") or 0) > int(entry.get("width") or 0)
        ]
        if not files:
            continue
        selected = min(
            files,
            key=lambda entry: abs(int(entry.get("width") or 0) - 1080),
        )
        user = video.get("user") or {}
        candidates.append(PexelsVideo(
            file_url=selected["link"],
            page_url=str(video.get("url") or "https://www.pexels.com/videos/"),
            creator_name=str(user.get("name") or "Pexels creator"),
            creator_url=str(user.get("url") or "https://www.pexels.com/"),
            duration=int(video.get("duration") or 0),
        ))

    if not candidates:
        raise PexelsError("no suitable portrait video")
    return candidates[0]


def download_stock_video(video_url):
    """Stream one validated Pexels MP4 into the system temp directory."""
    response = None
    temp_path = None
    completed = False
    try:
        response = requests.get(video_url, timeout=(10, 45), stream=True)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "video/mp4" not in content_type.casefold():
            raise PexelsError("stock file is not MP4")
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = 0
            if declared_size > MAX_STOCK_DOWNLOAD_BYTES:
                raise PexelsError("stock video exceeds download limit")

        with tempfile.NamedTemporaryFile(
            prefix="autoposter-pexels-", suffix=".mp4", delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)
            downloaded = 0
            for chunk in response.iter_content(chunk_size=128 * 1024):
                if not chunk:
                    continue
                downloaded += len(chunk)
                if downloaded > MAX_STOCK_DOWNLOAD_BYTES:
                    raise PexelsError("stock video exceeds download limit")
                temp_file.write(chunk)

        if downloaded == 0:
            raise PexelsError("stock video is empty")
        completed = True
        return TemporaryStockVideo(temp_path, downloaded)
    except requests.RequestException as error:
        raise PexelsError(type(error).__name__) from error
    finally:
        if response is not None:
            response.close()
        if temp_path and temp_path.exists() and not completed:
            temp_path.unlink()
