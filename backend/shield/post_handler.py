import html as html_mod
import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, Response

from shield.sanitizer import InputSanitizer
from shield.rate_limiter import RateLimiter

logger = logging.getLogger("frontwall.shield.post_handler")


class PostHandler:
    """Handles POST exceptions: validates, sanitizes, and forwards to the original WordPress."""

    def __init__(
        self,
        rate_limiter: RateLimiter,
        site_id: str = "",
        target_url: str = "",
        internal_url: str | None = None,
        override_host: str | None = None,
    ):
        self.sanitizer = InputSanitizer()
        self.rate_limiter = rate_limiter
        self.rules: list[dict] = []
        self.site_id = site_id
        self.target_url = target_url.rstrip("/")
        self.internal_url = internal_url.rstrip("/") if internal_url else None
        self.override_host = override_host
        self.learn_mode = False
        self.learned_posts: list[dict] = []
        self._max_learned = 500

    def _build_forward_url(self, path: str) -> str:
        """Build the URL to forward a POST to (internal if configured, otherwise target)."""
        base = self.internal_url if self.internal_url else self.target_url
        return base + path

    def _get_forward_headers(self, request: Request, client_ip: str) -> dict:
        """Build headers for the forwarded request, including Host override."""
        content_type = request.headers.get("content-type", "")
        target_scheme = urlparse(self.target_url).scheme
        fwd_headers = {
            "Content-Type": content_type,
            "X-Forwarded-For": client_ip,
            "X-Forwarded-Proto": target_scheme,
            "X-Forwarded-Host": self.override_host or urlparse(self.target_url).netloc,
            "User-Agent": request.headers.get("user-agent", "FrontWall/1.0"),
        }
        if self.internal_url and self.override_host:
            fwd_headers["Host"] = self.override_host
        if request.headers.get("x-requested-with"):
            fwd_headers["X-Requested-With"] = request.headers["x-requested-with"]
        if request.headers.get("accept"):
            fwd_headers["Accept"] = request.headers["accept"]
        return fwd_headers

    def load_rules(self, rules: list[dict]) -> None:
        self.rules = rules

    def find_matching_rule(self, path: str) -> dict | None:
        for rule in self.rules:
            if not rule.get("is_active", True):
                continue
            pattern = rule["url_pattern"]
            if pattern == path:
                return rule
            if "*" in pattern or "(" in pattern or "[" in pattern:
                try:
                    if re.fullmatch(pattern, path, flags=re.IGNORECASE):
                        return rule
                except (re.error, RecursionError):
                    continue
        return None

    async def handle_post(self, request: Request) -> Response:
        path = request.url.path
        client_ip = self._get_client_ip(request)

        rule = self.find_matching_rule(path)
        if not rule:
            if self.learn_mode:
                return await self._learn_and_forward(request, path, client_ip)
            logger.warning("POST to unregistered path: %s (IP: %s)", path, client_ip)
            return Response(content="Method Not Allowed", status_code=405, media_type="text/plain")

        allowed = await self.rate_limiter.check_endpoint(
            client_ip,
            path,
            max_requests=rule.get("rate_limit_requests", 10),
            window_seconds=rule.get("rate_limit_window", 60),
        )
        if not allowed:
            logger.warning("POST rate limit hit: %s (IP: %s)", path, client_ip)
            return Response(content="Too Many Requests", status_code=429, media_type="text/plain")

        body = await request.body()
        content_type = request.headers.get("content-type", "")

        try:
            if "application/x-www-form-urlencoded" in content_type:
                form_data = await request.form()
                raw_data = {k: str(v) for k, v in form_data.items()}
            elif "multipart/form-data" in content_type:
                form_data = await request.form()
                raw_data = {k: str(v) for k, v in form_data.items() if not hasattr(v, "read")}
            elif "application/json" in content_type:
                json_body = await request.json()
                raw_data = {k: str(v) for k, v in json_body.items()} if isinstance(json_body, dict) else {}
            else:
                return Response(content="Unsupported Media Type", status_code=415, media_type="text/plain")
        except Exception:
            return Response(content="Bad Request", status_code=400, media_type="text/plain")

        honeypot = rule.get("honeypot_field")
        if honeypot and raw_data.get(honeypot):
            logger.warning("Honeypot triggered on %s (IP: %s)", path, client_ip)
            return self._success_response(rule)

        field_rules = rule.get("fields", [])
        sanitized_data, errors = self.sanitizer.sanitize_and_validate(raw_data, field_rules)

        if errors:
            return JSONResponse(
                content={"status": "error", "errors": errors},
                status_code=422,
            )

        forward_url = self._build_forward_url(path)
        try:
            forward_headers = self._get_forward_headers(request, client_ip)
            async with httpx.AsyncClient(timeout=30, verify=True) as client:
                resp = await client.post(
                    forward_url,
                    content=body,
                    headers=forward_headers,
                    follow_redirects=False,
                )

                logger.info(
                    "POST forwarded: %s -> %s (status: %d, IP: %s)",
                    path, forward_url, resp.status_code, client_ip,
                )

                excluded = {"transfer-encoding", "content-encoding", "connection"}
                resp_headers = {
                    k: v for k, v in resp.headers.items()
                    if k.lower() not in excluded
                }

                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers=resp_headers,
                )

        except httpx.TimeoutException:
            logger.error("Timeout forwarding POST to %s", forward_url)
            return Response(content="Gateway Timeout", status_code=504, media_type="text/plain")
        except Exception as exc:
            logger.error("Error forwarding POST to %s: %s", forward_url, exc)
            return Response(content="Bad Gateway", status_code=502, media_type="text/plain")

    def _success_response(self, rule: dict) -> Response:
        redirect = rule.get("success_redirect")
        if redirect:
            parsed = urlparse(redirect)
            if parsed.scheme and parsed.scheme not in ("http", "https"):
                redirect = "/"
            if parsed.netloc and not redirect.startswith("/"):
                redirect = "/"
            return RedirectResponse(url=redirect, status_code=303)
        message = html_mod.escape(rule.get("success_message", "Form submitted successfully."))
        return HTMLResponse(
            content=f"<html><body><p>{message}</p></body></html>",
            status_code=200,
        )

    async def _learn_and_forward(self, request: Request, path: str, client_ip: str) -> Response:
        """Capture an unmatched POST, auto-create a rule, and proxy to the original server."""
        body = await request.body()
        content_type = request.headers.get("content-type", "")
        forward_url = self._build_forward_url(path)

        field_names = []
        already_known = any(p["path"] == path for p in self.learned_posts)

        if not already_known and len(self.learned_posts) < self._max_learned:
            try:
                import json as _json
                if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
                    form_data = await request.form()
                    field_names = list(form_data.keys())
                elif "application/json" in content_type:
                    json_body = _json.loads(body)
                    if isinstance(json_body, dict):
                        field_names = list(json_body.keys())
            except Exception:
                pass

            self.learned_posts.append({
                "path": path,
                "fields": field_names,
                "client_ip": client_ip,
            })
            logger.info("Learn mode captured POST: %s (fields: %s, IP: %s)", path, field_names, client_ip)

            try:
                from database import async_session
                from models.post_rule import PostRule, RuleField

                db_forward_url = self.target_url + path
                async with async_session() as db:
                    rule = PostRule(
                        site_id=self.site_id,
                        name=f"Auto-learned: {path}",
                        url_pattern=path,
                        forward_to=db_forward_url,
                        is_active=True,
                        rate_limit_requests=10,
                        rate_limit_window=60,
                    )
                    db.add(rule)
                    await db.flush()

                    for fname in field_names:
                        db.add(RuleField(
                            rule_id=rule.id,
                            field_name=fname,
                            field_type="text",
                            required=False,
                            max_length=5000,
                        ))

                    await db.commit()

                self.rules.append({
                    "url_pattern": path,
                    "forward_to": db_forward_url,
                    "is_active": True,
                    "success_redirect": None,
                    "success_message": None,
                    "rate_limit_requests": 10,
                    "rate_limit_window": 60,
                    "honeypot_field": None,
                    "enable_csrf": False,
                    "fields": [
                        {"field_name": f, "field_type": "text", "required": False,
                            "max_length": 5000, "validation_regex": None}
                        for f in field_names
                    ],
                })
                logger.info("Auto-created POST rule for %s with %d fields", path, len(field_names))
            except Exception as exc:
                logger.error("Failed to auto-create rule for %s: %s", path, exc)

        try:
            forward_headers = self._get_forward_headers(request, client_ip)
            async with httpx.AsyncClient(timeout=30, verify=True) as client:
                resp = await client.post(
                    forward_url,
                    content=body,
                    headers=forward_headers,
                    follow_redirects=False,
                )

                logger.info(
                    "Learn mode forwarded POST: %s -> %s (status: %d, IP: %s)",
                    path, forward_url, resp.status_code, client_ip,
                )

                excluded_headers = {"transfer-encoding", "content-encoding", "connection"}
                resp_headers = {
                    k: v for k, v in resp.headers.items()
                    if k.lower() not in excluded_headers
                }

                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers=resp_headers,
                )
        except httpx.TimeoutException:
            logger.error("Timeout forwarding learned POST to %s", forward_url)
            return Response(content="Gateway Timeout", status_code=504, media_type="text/plain")
        except Exception as exc:
            logger.error("Error forwarding learned POST to %s: %s", forward_url, exc)
            return Response(content="Bad Gateway", status_code=502, media_type="text/plain")

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "0.0.0.0"
