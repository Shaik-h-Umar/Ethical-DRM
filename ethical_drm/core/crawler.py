from __future__ import annotations

import html
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import urljoin
from uuid import uuid4

import requests
from bs4 import BeautifulSoup

try:
    from .detector import detect_leak
except ImportError:
    from core.detector import detect_leak


ALLOWED_MEDIA_EXTENSIONS = (".mp4", ".jpg", ".png")
MEDIA_PATH_HINTS = ("video", "stream", "media", "file", "photo", "image")
REQUEST_TIMEOUT_SECONDS = 8
MAX_SCAN_LINKS = 5
MIN_DETECTION_CONFIDENCE = 25.0
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
DEFAULT_PLATFORM_URLS = [
    "https://t.me/s/telegram",
    "https://www.youtube.com",
    "https://drive.google.com",
]


def _is_valid_http_url(url: str) -> bool:
    """Return True for well-formed HTTP/HTTPS URLs."""
    if not isinstance(url, str):
        return False

    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _has_media_extension(link: str) -> bool:
    """Return True when URL path appears to point to supported media."""
    parsed = urlparse(link)
    path = parsed.path.lower()
    return any(ext in path for ext in ALLOWED_MEDIA_EXTENSIONS)


def _is_probable_media_link(link: str, *, tag_name: str | None = None) -> bool:
    """Heuristic matcher for media links where file extensions may be hidden."""
    if not _is_valid_http_url(link):
        return False

    if _has_media_extension(link):
        return True

    parsed = urlparse(link)
    lower_path = parsed.path.lower()
    lower_query = parsed.query.lower()
    host = parsed.netloc.lower()

    if tag_name in {"video", "source", "img"}:
        return True
    if any(hint in lower_path for hint in MEDIA_PATH_HINTS):
        return True
    if any(token in lower_query for token in ("mime=video", "mime=image", "format=mp4")):
        return True
    if "telegram" in host or "t.me" in host:
        return any(hint in lower_path for hint in ("video", "file", "stream"))
    return False


def _normalize_media_url(url: str) -> str:
    """Normalize encoded URL variants commonly found in script/meta blobs."""
    cleaned = html.unescape(url.strip())
    cleaned = cleaned.replace("\\u0026", "&")
    cleaned = cleaned.rstrip("\\")
    return cleaned


def _extract_media_from_text(html_text: str) -> set[str]:
    """Extract absolute media URLs from raw HTML/JS text."""
    matches = re.findall(r"https?://[^\s\"'<>]+", html_text)
    results: set[str] = set()
    for candidate in matches:
        normalized = _normalize_media_url(candidate)
        if _is_probable_media_link(normalized):
            results.add(normalized)
    return results


def _normalize_detector_result(result) -> tuple[str | None, float]:
    """Normalize detector output to (user, confidence_percent)."""
    if isinstance(result, dict):
        user = result.get("user")
        confidence = float(result.get("confidence", 0.0) or 0.0)
        return user, confidence

    if isinstance(result, (tuple, list)) and len(result) >= 2:
        user = result[0]
        confidence = float(result[1] or 0.0)
        return user, confidence

    return None, 0.0


def crawl_for_media(url: str) -> list[str]:
    """Crawl a webpage and return unique absolute media links (.mp4/.jpg/.png)."""
    if not _is_valid_http_url(url):
        return []

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers=REQUEST_HEADERS)
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    media_links: set[str] = set()

    for tag in soup.find_all(["a", "img", "video", "source"]):
        candidate = tag.get("href") or tag.get("src")
        if not candidate:
            continue

        candidate = _normalize_media_url(candidate)
        resolved = _normalize_media_url(urljoin(url, candidate))
        if not _is_valid_http_url(resolved):
            continue

        if _is_probable_media_link(resolved, tag_name=tag.name):
            media_links.add(resolved)

    # Some platforms expose media via meta tags rather than visible anchors.
    for meta in soup.find_all("meta"):
        candidate = _normalize_media_url(meta.get("content") or "")
        if not candidate:
            continue
        resolved = _normalize_media_url(urljoin(url, candidate))
        property_name = (meta.get("property") or meta.get("name") or "").lower()
        if _is_probable_media_link(resolved) or property_name in {"og:video", "og:image"}:
            media_links.add(resolved)

    # Fallback extraction for links embedded in script blobs.
    media_links.update(_extract_media_from_text(response.text))

    # Prioritize video links first so bounded scans cover the most relevant media.
    return sorted(media_links, key=lambda link: (".mp4" not in link.lower(), link))


def download_file(url: str, filename: str) -> str | None:
    """Download a media URL to a temp file and return local path, else None."""
    if not _is_valid_http_url(url):
        return None

    safe_name = Path(filename).name or f"media_{uuid4().hex[:8]}"
    temp_path = Path(tempfile.gettempdir()) / safe_name

    try:
        with requests.get(
            url,
            stream=True,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers=REQUEST_HEADERS,
        ) as response:
            response.raise_for_status()
            with open(temp_path, "wb") as file_obj:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file_obj.write(chunk)
    except requests.RequestException:
        return None
    except OSError:
        return None

    return str(temp_path)


def detect_platform(url: str, source_url: str | None = None) -> str:
    """Infer source platform name from URL."""
    lowered = url.lower()
    source_lowered = (source_url or "").lower()
    if "t.me" in lowered:
        return "Telegram"
    if "t.me" in source_lowered:
        return "Telegram"
    if "youtube" in lowered:
        return "YouTube"
    if "youtube" in source_lowered:
        return "YouTube"
    if "drive.google.com" in lowered:
        return "Google Drive"
    if "drive.google.com" in source_lowered:
        return "Google Drive"
    return "Web"


def scan_url(url: str, database: list) -> list[dict]:
    """Scan up to 5 media links from a page and return verified leak findings."""
    if not _is_valid_http_url(url):
        return []

    media_links = crawl_for_media(url)
    if not media_links:
        return []

    findings: list[dict] = []
    seen_download_urls: set[str] = set()

    for idx, media_url in enumerate(media_links[:MAX_SCAN_LINKS], start=1):
        if media_url in seen_download_urls:
            continue
        seen_download_urls.add(media_url)

        extension = Path(urlparse(media_url).path).suffix.lower() or ".bin"
        temp_name = f"crawl_media_{idx}_{uuid4().hex[:8]}{extension}"
        local_path = download_file(media_url, temp_name)
        if not local_path:
            continue

        try:
            raw_result = detect_leak(local_path, database)
            user, confidence = _normalize_detector_result(raw_result)

            if user and confidence >= MIN_DETECTION_CONFIDENCE:
                findings.append(
                    {
                        "platform": detect_platform(media_url, source_url=url),
                        "url": media_url,
                        "user": user,
                        "confidence": round(confidence, 2),
                    }
                )
        except Exception:
            # Skip unsupported or unreadable files to keep scan robust for demo.
            pass
        finally:
            try:
                os.remove(local_path)
            except OSError:
                pass

    return findings


def scan_platforms(database: list, platform_urls: list[str] | None = None) -> list[dict]:
    """Run lightweight fallback scanning across a small set of platform URLs."""
    urls = platform_urls or DEFAULT_PLATFORM_URLS
    aggregated: list[dict] = []
    seen_urls: set[str] = set()

    for source_url in urls[:3]:
        try:
            results = scan_url(source_url, database)
        except Exception:
            continue

        for item in results:
            media_url = item.get("url")
            if not media_url or media_url in seen_urls:
                continue
            seen_urls.add(media_url)
            aggregated.append(item)

    return aggregated
