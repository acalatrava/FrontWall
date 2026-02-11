import html as html_mod
import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, Response

from shield.sanitizer import InputSanitizer
from shield.rate_limiter import RateLimiter
from shield.post_security import scan_post_data
from utils import get_client_ip

logger = logging.getLogger("frontwall.shield.post_handler")

ADMIN_AJAX_PATHS = {"/wp-admin/admin-ajax.php", "/wp-admin/admin-post.php"}


class PostHandler:
    """Handles POST exceptions: validates, sanitizes, and forwards to the original WordPress."""

    def __init__(
        self,
        rate_limiter: RateLimiter,
        site_id: str = "",
        target_url: str = "",
        internal_url: str | None = None,
        override_host: str | None = None,
        event_collector=None,
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
        self.collector = event_collector

    def _emit(self, event_type, severity, client_ip, path, request, details=None):
        if self.collector:
            self.collector.emit(
                event_type=event_type,
                severity=severity,
                client_ip=client_ip,
                path=path,
                method="POST",
                user_agent=request.headers.get("user-agent", ""),
                site_id=self.site_id,
                details=details,
                blocked=True,
            )

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

    def _parse_form_data(self, raw_data: dict[str, str], path: str) -> dict[str, str]:
        """Return the raw_data as-is — parsing already happened."""
        return raw_data

    def _check_action_whitelist(self, rule: dict, raw_data: dict[str, str], path: str) -> str | None:
        """For admin-ajax endpoints, verify the action is in the allowed list.

        Returns None if allowed, or an error string if blocked.
        """
        if path.lower() not in ADMIN_AJAX_PATHS:
            return None

        allowed_csv = rule.get("allowed_actions")
        if not allowed_csv:
            return None

        allowed_set = {a.strip().lower() for a in allowed_csv.split(",") if a.strip()}
        if not allowed_set:
            return None

        action = raw_data.get("action", "").strip().lower()
        if not action:
            return "Missing 'action' parameter for admin-ajax endpoint"

        if action not in allowed_set:
            return f"Action '{action}' is not in the allowed list"

        return None

    async def handle_post(self, request: Request) -> Response:
        path = request.url.path
        client_ip = get_client_ip(request)

        rule = self.find_matching_rule(path)
        if not rule:
            if self.learn_mode:
                return await self._learn_and_forward(request, path, client_ip)
            logger.warning("POST to unregistered path: %s (IP: %s)", path, client_ip)
            self._emit("post_unregistered", "low", client_ip, path, request)
            return Response(content="Method Not Allowed", status_code=405, media_type="text/plain")

        allowed = await self.rate_limiter.check_endpoint(
            client_ip,
            path,
            max_requests=rule.get("rate_limit_requests", 10),
            window_seconds=rule.get("rate_limit_window", 60),
        )
        if not allowed:
            logger.warning("POST rate limit hit: %s (IP: %s)", path, client_ip)
            self._emit("post_rate_limited", "medium", client_ip, path, request)
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

        threat = scan_post_data(raw_data, client_ip=client_ip, path=path)
        if threat:
            logger.warning("POST security scan blocked: %s on %s (IP: %s)", threat["threat"], path, client_ip)
            self._emit("post_injection_blocked", "critical", client_ip, path, request, threat)
            return Response(content="Forbidden", status_code=403, media_type="text/plain")

        action_err = self._check_action_whitelist(rule, raw_data, path)
        if action_err:
            logger.warning("Admin-ajax action blocked: %s (IP: %s, path: %s)", action_err, client_ip, path)
            self._emit("post_action_blocked", "high", client_ip, path, request, {"reason": action_err, "action": raw_data.get("action", "")})
            return Response(content="Forbidden", status_code=403, media_type="text/plain")

        honeypot = rule.get("honeypot_field")
        if honeypot and raw_data.get(honeypot):
            logger.warning("Honeypot triggered on %s (IP: %s)", path, client_ip)
            self._emit("honeypot_triggered", "critical", client_ip, path, request, {"honeypot_field": honeypot})
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
        raw_data = {}
        already_known = any(p["path"] == path for p in self.learned_posts)

        if not already_known and len(self.learned_posts) < self._max_learned:
            try:
                import json as _json
                if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
                    form_data = await request.form()
                    field_names = list(form_data.keys())
                    raw_data = {k: str(v) for k, v in form_data.items() if not hasattr(v, "read")}
                elif "application/json" in content_type:
                    json_body = _json.loads(body)
                    if isinstance(json_body, dict):
                        field_names = list(json_body.keys())
                        raw_data = {k: str(v) for k, v in json_body.items()}
            except Exception:
                pass

            threat = scan_post_data(raw_data, client_ip=client_ip, path=path)
            if threat:
                logger.warning("Learn mode security scan blocked: %s on %s (IP: %s)", threat["threat"], path, client_ip)
                self._emit("post_injection_blocked", "critical", client_ip, path, request, threat)
                return Response(content="Forbidden", status_code=403, media_type="text/plain")

            learned_action = None
            if path.lower() in ADMIN_AJAX_PATHS and "action" in raw_data:
                learned_action = raw_data["action"].strip()

            self.learned_posts.append({
                "path": path,
                "fields": field_names,
                "client_ip": client_ip,
                "action": learned_action,
            })
            logger.info("Learn mode captured POST: %s (fields: %s, action: %s, IP: %s)", path, field_names, learned_action, client_ip)

            try:
                from database import async_session
                from models.post_rule import PostRule, RuleField

                db_forward_url = self.target_url + path
                async with async_session() as db:
                    rule = PostRule(
                        site_id=self.site_id,
                        name=f"Auto-learned: {path}" + (f" [{learned_action}]" if learned_action else ""),
                        url_pattern=path,
                        forward_to=db_forward_url,
                        is_active=True,
                        rate_limit_requests=10,
                        rate_limit_window=60,
                        allowed_actions=learned_action if learned_action else None,
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
                    "allowed_actions": learned_action if learned_action else None,
                    "fields": [
                        {"field_name": f, "field_type": "text", "required": False,
                            "max_length": 5000, "validation_regex": None}
                        for f in field_names
                    ],
                })
                logger.info("Auto-created POST rule for %s with %d fields (allowed_actions: %s)", path, len(field_names), learned_action)
            except Exception as exc:
                logger.error("Failed to auto-create rule for %s: %s", path, exc)
        elif already_known and path.lower() in ADMIN_AJAX_PATHS and raw_data.get("action"):
            self._append_learned_action(path, raw_data["action"].strip())

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

    def _append_learned_action(self, path: str, action: str):
        """When a known admin-ajax rule receives a new action in learn mode, add it."""
        for rule in self.rules:
            if rule["url_pattern"] != path:
                continue
            current = rule.get("allowed_actions") or ""
            existing = {a.strip().lower() for a in current.split(",") if a.strip()}
            if action.lower() in existing:
                return
            new_list = current + (", " if current else "") + action
            rule["allowed_actions"] = new_list

            try:
                import asyncio
                asyncio.ensure_future(self._update_allowed_actions_db(path, new_list))
            except Exception:
                pass
            logger.info("Appended action '%s' to rule for %s", action, path)
            return

    async def _update_allowed_actions_db(self, path: str, allowed_actions: str):
        """Persist the updated allowed_actions to the database."""
        try:
            from database import async_session
            from models.post_rule import PostRule
            from sqlalchemy import update as sa_update

            async with async_session() as db:
                await db.execute(
                    sa_update(PostRule)
                    .where(PostRule.site_id == self.site_id, PostRule.url_pattern == path)
                    .values(allowed_actions=allowed_actions)
                )
                await db.commit()
        except Exception as exc:
            logger.error("Failed to update allowed_actions for %s: %s", path, exc)
