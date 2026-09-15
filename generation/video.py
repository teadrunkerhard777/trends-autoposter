"""Small, dependency-light MP4 cards built from one editorial image."""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


@dataclass(frozen=True)
class TemporaryVideo:
    path: Path
    size_bytes: int


class VideoRenderError(Exception):
    """Expected failure while producing a Telegram-ready video."""


def render_video_card(image_path, copy, style, size, duration_seconds):
    """Render an animated MP4 from an image and project-supplied card copy."""
    cover_path = None
    video_path = None
    completed = False

    try:
        with Image.open(image_path) as source:
            cover = _build_cover(source, copy, style, size)

        with tempfile.NamedTemporaryFile(
            prefix="autoposter-video-cover-", suffix=".png", delete=False
        ) as cover_file:
            cover_path = Path(cover_file.name)
            cover.save(cover_file, format="PNG", optimize=True)

        with tempfile.NamedTemporaryFile(
            prefix="autoposter-video-", suffix=".mp4", delete=False
        ) as video_file:
            video_path = Path(video_file.name)

        fps = 25
        frames = max(1, int(duration_seconds * fps))
        width, height = size
        filter_graph = (
            f"zoompan=z='min(zoom+0.00035,1.05)':d={frames}:"
            f"s={width}x{height}:fps={fps},"
            "fade=t=in:st=0:d=0.35,"
            f"fade=t=out:st={max(0, duration_seconds - 0.6)}:d=0.6"
        )
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loop", "1",
            "-i", str(cover_path), "-vf", filter_graph,
            "-t", str(duration_seconds), "-an", "-c:v", "libx264",
            "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(video_path),
        ]
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=90, check=False
        )

        if result.returncode != 0 or not video_path.exists():
            raise VideoRenderError("ffmpeg could not render the video")

        size_bytes = video_path.stat().st_size
        if size_bytes == 0:
            raise VideoRenderError("ffmpeg returned an empty video")

        completed = True
        return TemporaryVideo(video_path, size_bytes)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise VideoRenderError(type(error).__name__) from error
    finally:
        if cover_path and cover_path.exists():
            cover_path.unlink()
        if video_path and video_path.exists() and not completed:
            video_path.unlink()


def _build_cover(source, copy, style, size):
    width, height = size
    foreground = style["foreground"]
    muted = style["muted"]
    accent = style["accent"]
    background = style["background"]

    rgb_source = ImageOps.exif_transpose(source).convert("RGB")
    backdrop = ImageOps.fit(rgb_source, size, method=Image.Resampling.LANCZOS)
    backdrop = ImageEnhance.Brightness(backdrop).enhance(0.48)
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(radius=3))

    image = Image.new("RGB", size, background)
    image.paste(backdrop)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, height * 0.42, width, height), fill=(9, 12, 17, 205))
    draw.rectangle((72, 92, 242, 106), fill=accent)

    brand_font = _font(34, bold=True)
    eyebrow_font = _font(34, bold=True)
    title_font = _font(70, bold=True)
    small_font = _font(30)
    draw.text((72, 42), copy["brand"], font=brand_font, fill=foreground)
    draw.text((72, int(height * 0.49)), copy["eyebrow"], font=eyebrow_font, fill=accent)

    title_lines = _wrap_text(draw, copy["title"], title_font, width - 144, 5)
    y = int(height * 0.56)
    for line in title_lines:
        draw.text((72, y), line, font=title_font, fill=foreground)
        y += 84

    draw.text(
        (72, height - 78), copy.get("tagline", ""), font=small_font, fill=muted
    )
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def _font(size, bold=False):
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width, max_lines):
    words = " ".join(str(text).split()).split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines - 1:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    consumed = " ".join(lines)
    if len(consumed) < len(" ".join(words)) and lines:
        while draw.textlength(f"{lines[-1]}…", font=font) > max_width:
            lines[-1] = lines[-1][:-1].rstrip()
        lines[-1] = f"{lines[-1]}…"
    return lines
