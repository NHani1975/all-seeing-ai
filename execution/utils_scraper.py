"""
utils_scraper.py — Shared scraping helpers.

Single responsibility: fetch raw HTML and convert it to clean,
AI-ready plain text. Also provides a smart head+tail truncation
strategy that preserves both opening context and closing content.

Usage:
    from utils_scraper import fetch_page, clean_html, smart_truncate
"""

import re
import requests
from bs4 import BeautifulSoup

# ── Constants ────────────────────────────────────────────────────────────────
REQUEST_TIMEOUT  = 15          # seconds before giving up on a request
MAX_CONTENT_LEN  = 12_000      # hard cap for AI input (chars)
HEAD_CHARS       = 6_000       # chars to keep from beginning
TAIL_CHARS       = 6_000       # chars to keep from end
TAIL_SEPARATOR   = "\n\n[...content truncated...]\n\n"

# Tags whose content adds no value for analysis
NOISE_TAGS = [
    "script", "style", "noscript", "iframe", "svg",
    "picture", "video", "audio", "canvas", "head",
    "header", "footer", "nav", "aside", "form",
    "button", "input", "select", "textarea",
    "meta", "link", "advertisement",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    ),
}


def fetch_page(url: str) -> str:
    """
    Fetch raw HTML from a URL.

    Args:
        url: Full URL including scheme (https://...).

    Returns:
        Raw HTML as a string.

    Raises:
        ValueError: If the URL is empty or has no scheme.
        RuntimeError: If the HTTP request fails (network error, 4xx, 5xx).
    """
    if not url or not url.startswith(("http://", "https://")):
        raise ValueError(
            f"Invalid URL: '{url}'. Must start with http:// or https://"
        )

    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text

    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            f"Could not connect to '{url}'. "
            "Check the URL and your internet connection."
        ) from exc

    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Request to '{url}' timed out after {REQUEST_TIMEOUT}s."
        )

    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"HTTP error {exc.response.status_code} fetching '{url}': {exc}"
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Unexpected request error for '{url}': {exc}") from exc


def clean_html(html: str) -> str:
    """
    Convert raw HTML to clean, readable plain text.

    Strategy:
    1. Always extract title + meta description as a guaranteed prefix.
    2. Strip only truly noisy tags (scripts, styles, iframes, etc.).
    3. Pull visible text from semantic content tags.
    4. Fall back to all visible body text if semantic pass yields little.
    5. Never raise on sparse pages — return what we have with a note.

    Args:
        html: Raw HTML string.

    Returns:
        Clean plain-text string suitable for AI processing.

    Raises:
        ValueError: Only if the HTML is completely unparseable (empty input).
    """
    if not html or not html.strip():
        raise ValueError("Empty HTML received — nothing to parse.")

    soup = BeautifulSoup(html, "lxml")

    # ── 1. Extract meta info first (always available even on JS sites) ────────
    meta_parts = []

    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        meta_parts.append("Page Title: " + title_tag.get_text(strip=True))

    for attr in [("meta", {"name": "description"}),
                 ("meta", {"property": "og:description"}),
                 ("meta", {"name": "og:description"}),
                 ("meta", {"property": "description"})]:
        tag = soup.find(attr[0], attr[1])
        if tag and tag.get("content", "").strip():
            desc = tag["content"].strip()
            if desc not in " ".join(meta_parts):   # avoid duplicates
                meta_parts.append("Description: " + desc)
            break

    for tag in soup.find_all("meta", attrs={"property": True}):
        prop = tag.get("property", "")
        if prop.startswith("og:") and tag.get("content", "").strip():
            if prop not in ("og:description",):    # already got description
                meta_parts.append(f"{prop}: {tag['content'].strip()}")

    meta_prefix = "\n".join(meta_parts)

    # ── 2. Strip truly noisy tags only ────────────────────────────────────────
    STRIP_TAGS = [
        "script", "style", "noscript", "iframe",
        "svg", "canvas", "video", "audio",
        "link", "meta",
    ]
    for tag in STRIP_TAGS:
        for el in soup.find_all(tag):
            el.decompose()

    # ── 3. Ad/cookie banners by class/id pattern ──────────────────────────────
    ad_patterns = re.compile(
        r"(cookie[-_]?banner|cookie[-_]?consent|gdpr|ad[-_]slot|"
        r"advertisement|popup[-_]overlay|modal[-_]overlay)",
        re.IGNORECASE,
    )
    for el in soup.find_all(True):
        if not el.attrs:
            continue
        combined = " ".join(el.get("class", [])) + " " + el.get("id", "")
        if ad_patterns.search(combined):
            el.decompose()

    # ── 4. Try semantic content first ─────────────────────────────────────────
    SEMANTIC_TAGS = ["main", "article", "section", "[role=main]"]
    semantic_text = ""
    for selector in SEMANTIC_TAGS:
        nodes = soup.select(selector)
        if nodes:
            semantic_text = "\n".join(n.get_text(separator="\n") for n in nodes)
            break

    # ── 5. Fallback: all body text ────────────────────────────────────────────
    body = soup.find("body")
    body_text = body.get_text(separator="\n") if body else soup.get_text(separator="\n")

    # Pick whichever gives more content
    raw_text = semantic_text if len(semantic_text) > len(body_text) * 0.3 else body_text

    # ── 6. Clean up whitespace ────────────────────────────────────────────────
    text = re.sub(r"\n{3,}", "\n\n", raw_text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = text.strip()

    # ── 7. Combine meta prefix + body text ───────────────────────────────────
    if meta_prefix:
        text = meta_prefix + "\n\n" + text if text else meta_prefix

    if not text:
        # Last resort: the page is completely opaque (blank JS shell)
        text = (
            "NOTE: This page appears to be entirely JavaScript-rendered. "
            "No static text content could be extracted."
        )

    return text



def smart_truncate(text: str, max_chars: int = MAX_CONTENT_LEN) -> str:
    """
    Truncate text using a head + tail strategy.

    Instead of blindly cutting at max_chars, this preserves the
    beginning (most important for context) AND the end (often contains
    CTAs, pricing, or closing value props). The middle is dropped.

    Args:
        text:      Input text.
        max_chars: Total character budget (default: 12 000).

    Returns:
        Truncated text, or the original text if it fits within max_chars.
    """
    if len(text) <= max_chars:
        return text

    half = max_chars // 2
    head = text[:half]
    tail = text[-half:]
    return head + TAIL_SEPARATOR + tail
