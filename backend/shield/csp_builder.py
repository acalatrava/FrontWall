import logging
import re
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger("frontwall.shield.csp_builder")

_URL_RE = re.compile(r'https?://[a-zA-Z0-9._-]+(?:\.[a-zA-Z]{2,})+')

KNOWN_DOMAIN_GROUPS = {
    "fonts.googleapis.com": {"fonts.gstatic.com", "fonts.googleapis.com"},
    "fonts.gstatic.com": {"fonts.gstatic.com", "fonts.googleapis.com"},
    "ajax.googleapis.com": {"ajax.googleapis.com"},
    "cdn.gtranslate.net": {"cdn.gtranslate.net", "translate.google.com", "translate.googleapis.com"},
    "translate.google.com": {"cdn.gtranslate.net", "translate.google.com", "translate.googleapis.com"},
    "maps.googleapis.com": {"maps.googleapis.com", "maps.gstatic.com", "maps.google.com"},
    "www.google-analytics.com": {"www.google-analytics.com", "www.googletagmanager.com", "analytics.google.com"},
    "www.googletagmanager.com": {"www.googletagmanager.com", "www.google-analytics.com", "analytics.google.com"},
}


def _extract_origins_from_text(text: str) -> set[str]:
    """Extract all external origin URLs from any text content (HTML, CSS, JS)."""
    origins: set[str] = set()
    for match in _URL_RE.findall(text):
        try:
            parsed = urlparse(match)
            if parsed.scheme and parsed.netloc:
                origins.add(f"{parsed.scheme}://{parsed.netloc}")
        except Exception:
            pass
    return origins


def _expand_with_known_groups(origins: set[str]) -> set[str]:
    """Expand origins with known associated domains."""
    expanded = set(origins)
    for origin in origins:
        try:
            host = urlparse(origin).netloc
            if host in KNOWN_DOMAIN_GROUPS:
                for related in KNOWN_DOMAIN_GROUPS[host]:
                    expanded.add(f"https://{related}")
        except Exception:
            pass
    return expanded


def scan_cache_for_origins(cache_dir: Path, target_url: str | None = None) -> dict:
    """Scan all cached files and return external origins for CSP building."""
    all_origins: set[str] = set()
    has_inline_scripts = False

    scannable = list(cache_dir.rglob("*.html")) + list(cache_dir.rglob("*.css")) + list(cache_dir.rglob("*.js"))
    logger.info("Scanning %d files for external origins", len(scannable))

    for file_path in scannable:
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            origins = _extract_origins_from_text(text)
            all_origins.update(origins)

            if file_path.suffix == ".html":
                if re.search(r'<script(?:\s[^>]*)?>(?!\s*$).+?</script>', text, re.DOTALL):
                    has_inline_scripts = True
                if re.search(r'\bon\w+\s*=\s*["\']', text):
                    has_inline_scripts = True
        except Exception as exc:
            logger.warning("Failed to scan %s: %s", file_path, exc)

    all_origins = _expand_with_known_groups(all_origins)

    if target_url:
        try:
            parsed = urlparse(target_url)
            if parsed.netloc:
                all_origins.add(f"https://{parsed.netloc}")
                all_origins.add(f"http://{parsed.netloc}")
        except Exception:
            pass

    logger.info("Discovered %d external origins", len(all_origins))

    return {
        "origins": sorted(all_origins),
        "needs_unsafe_inline": has_inline_scripts,
        "needs_unsafe_eval": True,
    }


def build_csp(scan_result: dict) -> str:
    """Build a Content-Security-Policy string from scan results."""
    origins = scan_result.get("origins", [])
    origins_str = " ".join(origins)

    script_base = "'self'"
    if scan_result.get("needs_unsafe_inline"):
        script_base += " 'unsafe-inline'"
    if scan_result.get("needs_unsafe_eval"):
        script_base += " 'unsafe-eval'"

    directives = [
        f"default-src 'self' {origins_str}",
        f"script-src {script_base} {origins_str}",
        f"style-src 'self' 'unsafe-inline' {origins_str}",
        f"img-src 'self' data: blob: {origins_str}",
        f"font-src 'self' data: {origins_str}",
        f"connect-src 'self' {origins_str}",
        f"media-src 'self' {origins_str}",
        f"frame-src 'self' {origins_str}",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ]

    return "; ".join(directives)
