import logging
import re
from urllib.parse import urljoin

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, Response

from shield.sanitizer import InputSanitizer
from shield.rate_limiter import RateLimiter

logger = logging.getLogger("webshield.shield.post_handler")


class PostHandler:
    """Handles POST exceptions: validates, sanitizes, and forwards to the original WordPress."""

    def __init__(self, rate_limiter: RateLimiter):
        self.sanitizer = InputSanitizer()
        self.rate_limiter = rate_limiter
        self.rules: list[dict] = []

    def load_rules(self, rules: list[dict]) -> None:
        self.rules = rules

    def find_matching_rule(self, path: str) -> dict | None:
        for rule in self.rules:
            if not rule.get("is_active", True):
                continue
            pattern = rule["url_pattern"]
            if pattern == path:
                return rule
            try:
                if re.match(pattern, path):
                    return rule
            except re.error:
                continue
        return None

    async def handle_post(self, request: Request) -> Response:
        path = request.url.path
        client_ip = self._get_client_ip(request)

        rule = self.find_matching_rule(path)
        if not rule:
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

        try:
            content_type = request.headers.get("content-type", "")
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

        forward_url = rule["forward_to"]
        try:
            async with httpx.AsyncClient(timeout=30, verify=True) as client:
                forward_headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Forwarded-For": client_ip,
                    "X-Forwarded-Proto": request.url.scheme,
                    "User-Agent": request.headers.get("user-agent", "WebShield/1.0"),
                }

                resp = await client.post(
                    forward_url,
                    data=sanitized_data,
                    headers=forward_headers,
                    follow_redirects=False,
                )

                logger.info(
                    "POST forwarded: %s -> %s (status: %d, IP: %s)",
                    path, forward_url, resp.status_code, client_ip,
                )

        except httpx.TimeoutException:
            logger.error("Timeout forwarding POST to %s", forward_url)
            return Response(content="Gateway Timeout", status_code=504, media_type="text/plain")
        except Exception as exc:
            logger.error("Error forwarding POST to %s: %s", forward_url, exc)
            return Response(content="Bad Gateway", status_code=502, media_type="text/plain")

        return self._success_response(rule)

    def _success_response(self, rule: dict) -> Response:
        redirect = rule.get("success_redirect")
        if redirect:
            return RedirectResponse(url=redirect, status_code=303)
        message = rule.get("success_message", "Form submitted successfully.")
        return HTMLResponse(
            content=f"<html><body><p>{message}</p></body></html>",
            status_code=200,
        )

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "0.0.0.0"
