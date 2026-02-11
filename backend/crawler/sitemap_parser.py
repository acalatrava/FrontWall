import logging
from urllib.parse import urljoin
from xml.etree import ElementTree

import httpx

logger = logging.getLogger("frontwall.crawler.sitemap")

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


async def parse_robots_txt(client: httpx.AsyncClient, base_url: str) -> tuple[list[str], list[str]]:
    """Parse robots.txt and return (sitemap_urls, disallowed_paths)."""
    sitemaps: list[str] = []
    disallowed: list[str] = []

    try:
        resp = await client.get(urljoin(base_url, "/robots.txt"), timeout=10)
        if resp.status_code != 200:
            return sitemaps, disallowed

        for line in resp.text.splitlines():
            line = line.strip()
            if line.lower().startswith("sitemap:"):
                sitemaps.append(line.split(":", 1)[1].strip())
            elif line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    disallowed.append(path)
    except Exception as exc:
        logger.warning("Failed to parse robots.txt: %s", exc)

    return sitemaps, disallowed


async def parse_sitemap(client: httpx.AsyncClient, sitemap_url: str) -> list[str]:
    """Parse a sitemap XML and return discovered URLs. Handles sitemap indexes recursively."""
    urls: list[str] = []

    try:
        resp = await client.get(sitemap_url, timeout=15)
        if resp.status_code != 200:
            return urls

        root = ElementTree.fromstring(resp.content)

        for sitemap_tag in root.findall("sm:sitemap", SITEMAP_NS):
            loc = sitemap_tag.find("sm:loc", SITEMAP_NS)
            if loc is not None and loc.text:
                child_urls = await parse_sitemap(client, loc.text.strip())
                urls.extend(child_urls)

        for url_tag in root.findall("sm:url", SITEMAP_NS):
            loc = url_tag.find("sm:loc", SITEMAP_NS)
            if loc is not None and loc.text:
                urls.append(loc.text.strip())

    except Exception as exc:
        logger.warning("Failed to parse sitemap %s: %s", sitemap_url, exc)

    return urls


async def discover_urls_from_sitemaps(
    client: httpx.AsyncClient, base_url: str, respect_robots: bool = True
) -> tuple[list[str], list[str]]:
    """Full sitemap discovery: parse robots.txt, then all sitemaps.
    Returns (discovered_urls, disallowed_paths).
    """
    sitemaps, disallowed = await parse_robots_txt(client, base_url)

    if not sitemaps:
        sitemaps = [urljoin(base_url, "/sitemap.xml")]

    all_urls: list[str] = []
    for sitemap_url in sitemaps:
        urls = await parse_sitemap(client, sitemap_url)
        all_urls.extend(urls)

    if not respect_robots:
        disallowed = []

    logger.info(
        "Sitemap discovery: %d URLs found, %d disallowed paths",
        len(all_urls),
        len(disallowed),
    )
    return all_urls, disallowed
