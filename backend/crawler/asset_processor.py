import logging
import mimetypes
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse, urljoin

import warnings

import httpx
from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from crawler.url_rewriter import URLRewriter

logger = logging.getLogger("webshield.crawler.assets")

ASSET_EXTENSIONS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pdf", ".mp4", ".webm", ".mp3", ".ogg",
    ".json", ".xml", ".txt", ".map",
}


def extract_asset_urls(html: str, base_url: str) -> set[str]:
    """Extract all asset URLs referenced in HTML (CSS, JS, images, fonts, etc.)."""
    soup = BeautifulSoup(html, "lxml")
    assets: set[str] = set()

    for tag in soup.find_all(["link", "script", "img", "source", "video", "audio"]):
        if not isinstance(tag, Tag):
            continue
        for attr in ("href", "src"):
            val = tag.get(attr)
            if val and isinstance(val, str):
                absolute = urljoin(base_url, val)
                assets.add(absolute)

        srcset = tag.get("srcset")
        if srcset and isinstance(srcset, str):
            for entry in srcset.split(","):
                parts = entry.strip().split()
                if parts:
                    absolute = urljoin(base_url, parts[0])
                    assets.add(absolute)

    for tag in soup.find_all("style"):
        if tag.string:
            assets.update(_extract_css_urls(tag.string, base_url))

    for tag in soup.find_all(attrs={"style": True}):
        if isinstance(tag, Tag):
            style_val = tag.get("style", "")
            if isinstance(style_val, str) and "url(" in style_val:
                assets.update(_extract_css_urls(style_val, base_url))

    return assets


def extract_css_asset_urls(css_content: str, css_url: str) -> set[str]:
    """Extract url() references from CSS content."""
    return _extract_css_urls(css_content, css_url)


def _extract_css_urls(css: str, base_url: str) -> set[str]:
    import re
    urls: set[str] = set()
    for match in re.finditer(r"url\(['\"]?([^)'\"\s]+)['\"]?\)", css):
        raw = match.group(1)
        if raw.startswith("data:"):
            continue
        absolute = urljoin(base_url, raw)
        urls.add(absolute)
    return urls


async def download_asset(
    client: httpx.AsyncClient,
    url: str,
    cache_dir: Path,
    rewriter: URLRewriter,
    url_translator: "Callable[[str], str] | None" = None,
) -> int:
    """Download a single asset and store it in the cache directory.
    Returns size in bytes, or 0 on failure.
    """
    if not rewriter.is_same_origin(url):
        return 0

    try:
        fetch_url = url_translator(url) if url_translator else url
        resp = await client.get(fetch_url, follow_redirects=True, timeout=30)
        if resp.status_code != 200:
            logger.debug("Asset %s returned status %d", url, resp.status_code)
            return 0

        cache_path = rewriter.url_to_cache_path(url)
        full_path = cache_dir / cache_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        content = resp.content

        content_type = resp.headers.get("content-type", "")
        if "text/css" in content_type:
            text = content.decode("utf-8", errors="replace")
            text = rewriter.rewrite_css(text)

            sub_urls = extract_css_asset_urls(text, url)
            for sub_url in sub_urls:
                if rewriter.is_same_origin(sub_url):
                    await download_asset(client, sub_url, cache_dir, rewriter, url_translator)

            content = text.encode("utf-8")

        full_path.write_bytes(content)

        clean_path = rewriter.url_to_cache_path_no_query(url)
        if clean_path != cache_path:
            clean_full = cache_dir / clean_path
            if not clean_full.exists():
                clean_full.parent.mkdir(parents=True, exist_ok=True)
                clean_full.write_bytes(content)

        return len(content)

    except Exception as exc:
        logger.warning("Failed to download asset %s: %s", url, exc)
        return 0
