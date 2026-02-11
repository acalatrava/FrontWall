import re
from urllib.parse import urlparse, urljoin, urlunparse, quote


class URLRewriter:
    """Rewrites absolute WordPress URLs to relative paths for static serving."""

    def __init__(self, target_origin: str):
        parsed = urlparse(target_origin)
        self.origin = f"{parsed.scheme}://{parsed.netloc}"
        self.scheme = parsed.scheme
        self.netloc = parsed.netloc

    def is_same_origin(self, url: str) -> bool:
        parsed = urlparse(url)
        if not parsed.netloc:
            return True
        return parsed.netloc == self.netloc

    def to_absolute(self, url: str, base_url: str) -> str:
        return urljoin(base_url, url)

    def to_relative_path(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"
        return path

    def url_to_cache_path(self, url: str) -> str:
        """Convert a URL to a filesystem-safe cache path."""
        parsed = urlparse(url)
        path = self._normalize_cache_path(parsed.path)

        if parsed.query:
            safe_query = quote(parsed.query, safe="")
            name_parts = path.rsplit(".", 1)
            if len(name_parts) == 2:
                path = f"{name_parts[0]}_{safe_query}.{name_parts[1]}"
            else:
                path = f"{path}_{safe_query}"

        return path

    def url_to_cache_path_no_query(self, url: str) -> str:
        """Convert a URL to cache path ignoring query string (the fallback version)."""
        parsed = urlparse(url)
        return self._normalize_cache_path(parsed.path)

    @staticmethod
    def _normalize_cache_path(url_path: str) -> str:
        path = url_path.strip("/")
        if not path:
            path = "index.html"
        elif path.endswith("/"):
            path += "index.html"
        elif "." not in path.split("/")[-1]:
            path += "/index.html"
        return path

    def rewrite_html(self, html: str) -> str:
        """Replace all absolute URLs pointing to the target origin with relative paths.
        Handles both http:// and https:// variants of the origin."""

        def replace_origin_url(match: re.Match) -> str:
            prefix = match.group(1)
            url = match.group(2)
            if self._is_any_scheme_same_origin(url):
                parsed = urlparse(url)
                relative = parsed.path or "/"
                if parsed.query:
                    relative += f"?{parsed.query}"
                if parsed.fragment:
                    relative += f"#{parsed.fragment}"
                return f'{prefix}"{relative}"'
            return match.group(0)

        pattern = re.compile(
            r'((?:href|src|action|srcset)\s*=\s*)["\']([^"\']*)["\']',
            re.IGNORECASE,
        )
        html = pattern.sub(replace_origin_url, html)

        for scheme in ("https", "http"):
            escaped_origin = re.escape(f"{scheme}://{self.netloc}")
            html = re.sub(
                rf"{escaped_origin}(/[^\s\"'<>]*)",
                r"\1",
                html,
            )

        for scheme in ("https", "http"):
            json_origin = scheme + ":\\/" + "\\/" + self.netloc
            html = html.replace(json_origin, "")

        html = html.replace("\\/" + "\\/" + self.netloc, "")

        html = html.replace("//" + self.netloc, "")

        for scheme in ("https", "http"):
            bare = f"{scheme}://{self.netloc}"
            html = html.replace(f'"{bare}"', '"/"')
            html = html.replace(f"'{bare}'", "'/'")

        return html

    def _is_any_scheme_same_origin(self, url: str) -> bool:
        """Check if a URL points to the same host, regardless of http/https."""
        parsed = urlparse(url)
        if not parsed.netloc:
            return True
        return parsed.netloc == self.netloc

    def rewrite_css(self, css: str) -> str:
        """Replace absolute URLs in CSS url() declarations.
        Handles both http:// and https:// variants of the origin."""

        def replace_css_url(match: re.Match) -> str:
            url = match.group(1).strip("'\"")
            if self._is_any_scheme_same_origin(url):
                parsed = urlparse(url)
                relative = parsed.path or "/"
                return f"url('{relative}')"
            return match.group(0)

        pattern = re.compile(r"url\(([^)]+)\)", re.IGNORECASE)
        return pattern.sub(replace_css_url, css)
