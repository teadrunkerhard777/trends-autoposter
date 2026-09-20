import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 AutoposterTemplate/1.0"}
DEFAULT_RETRIES = 3
RETRY_DELAY_SECONDS = 0.5
SERVICE_PREFIXES = (
    "photo:", "фото:", "video:", "источник изображения:", "иллюстрация:",
    "read also", "advertisement", "sponsored",
)


def fetch_article_html(url, source_config=None):
    """Fetch one article page with finite timeout and HTTP validation."""

    config = source_config or {}
    headers = {**REQUEST_HEADERS, **(config.get("headers") or {})}
    retries = (
        max(0, int(config.get("retries", DEFAULT_RETRIES)))
        if source_config is not None
        else 0
    )

    for attempt in range(retries + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            if attempt == retries:
                raise

            # Give repeated transient failures progressively more recovery time.
            time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))


def extract_article_text(html, source=None, source_extractors=None):
    """Use a source-specific extractor or the conservative generic body."""

    soup = BeautifulSoup(html, "html.parser")
    extractor = (source_extractors or {}).get(source)

    if extractor is not None:
        return extractor(soup)

    body = soup.select_one("article") or soup.select_one("main") or soup
    paragraphs = [
        " ".join(node.get_text(" ", strip=True).split())
        for node in body.find_all("p")
    ]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def clean_article_text(text, source=None, source_stop_markers=None):
    """Remove generic service paragraphs and isolated source footers."""

    stop_markers = tuple(
        marker.casefold()
        for marker in (source_stop_markers or {}).get(source, ())
    )
    cleaned = []

    for raw_paragraph in (text or "").splitlines():
        paragraph = " ".join(raw_paragraph.split())

        if not paragraph:
            continue

        normalized = paragraph.casefold()

        if stop_markers and normalized.startswith(stop_markers):
            break

        if normalized.startswith(SERVICE_PREFIXES):
            continue

        cleaned.append(paragraph)

    return "\n\n".join(cleaned)


def extract_article_image_url(html, page_url):
    """Return the best plausible editorial preview image from page metadata."""

    soup = BeautifulSoup(html, "html.parser")
    selectors = (
        ('meta[property="og:image"]', "content"),
        ('meta[name="twitter:image"]', "content"),
        ('link[rel="image_src"]', "href"),
    )

    for selector, attribute in selectors:
        node = soup.select_one(selector)
        value = node.get(attribute, "").strip() if node else ""

        if value and _is_plausible_article_image(value, node):
            return urljoin(page_url, value)

    return None


def _is_plausible_article_image(value, node):
    """Reject metadata that clearly points to branding or tiny placeholders."""

    normalized = value.casefold()

    if normalized.startswith(("data:", "javascript:")):
        return False

    filename = normalized.split("?", 1)[0].rsplit("/", 1)[-1]
    if any(marker in filename for marker in ("logo", "avatar", "favicon", "icon", "spinner", "placeholder")):
        return False

    width = _metadata_dimension(node, "width")
    height = _metadata_dimension(node, "height")
    return not (width and height and (width < 300 or height < 180))


def _metadata_dimension(node, dimension):
    """Read an adjacent Open Graph dimension when the publisher provides it."""

    if node is None or not node.name == "meta":
        return None

    property_name = node.get("property") or node.get("name") or ""
    expected = f"{property_name}:{dimension}"
    dimension_node = node.find_next(
        "meta",
        attrs={
            "property" if node.get("property") else "name": expected,
        },
    )

    if dimension_node is None:
        return None

    try:
        return int(dimension_node.get("content", ""))
    except (TypeError, ValueError):
        return None
