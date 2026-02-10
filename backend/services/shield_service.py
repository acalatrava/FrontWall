import asyncio
import logging
from pathlib import Path

import uvicorn
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database import async_session
from models.site import Site
from models.post_rule import PostRule, RuleField
from shield.server import create_shield_app
from shield.waf import WAFMiddleware
from shield.rate_limiter import RateLimiter
from shield.post_handler import PostHandler

logger = logging.getLogger("webshield.services.shield")

_shield_server: uvicorn.Server | None = None
_shield_task: asyncio.Task | None = None
_post_handler: PostHandler | None = None


async def _load_post_rules(site_id: str) -> list[dict]:
    async with async_session() as db:
        result = await db.execute(
            select(PostRule)
            .where(PostRule.site_id == site_id, PostRule.is_active == True)
            .options(selectinload(PostRule.fields))
        )
        rules = result.scalars().all()

        rule_dicts = []
        for rule in rules:
            fields = [
                {
                    "field_name": f.field_name,
                    "field_type": f.field_type,
                    "required": f.required,
                    "max_length": f.max_length,
                    "validation_regex": f.validation_regex,
                }
                for f in rule.fields
            ]
            rule_dicts.append({
                "url_pattern": rule.url_pattern,
                "forward_to": rule.forward_to,
                "is_active": rule.is_active,
                "success_redirect": rule.success_redirect,
                "success_message": rule.success_message,
                "rate_limit_requests": rule.rate_limit_requests,
                "rate_limit_window": rule.rate_limit_window,
                "honeypot_field": rule.honeypot_field,
                "enable_csrf": rule.enable_csrf,
                "fields": fields,
            })
        return rule_dicts


async def deploy_shield(site_id: str) -> bool:
    global _shield_server, _shield_task, _post_handler

    if _shield_server is not None:
        await undeploy_shield()

    cache_dir = Path(settings.cache_dir) / site_id
    if not cache_dir.exists():
        raise FileNotFoundError(f"Cache directory not found for site {site_id}. Run a crawl first.")

    shield_app = create_shield_app(site_id)

    rate_limiter = RateLimiter(
        global_requests=settings.rate_limit_requests,
        global_window=settings.rate_limit_window_seconds,
    )

    post_rules = await _load_post_rules(site_id)
    _post_handler = PostHandler(rate_limiter)
    _post_handler.load_rules(post_rules)

    @shield_app.api_route("/{path:path}", methods=["POST"])
    async def handle_post(request, path: str = ""):
        return await _post_handler.handle_post(request)

    shield_app.add_middleware(
        WAFMiddleware,
        rate_limiter=rate_limiter,
        max_body_size=settings.max_request_size_bytes,
    )

    config = uvicorn.Config(
        shield_app,
        host="0.0.0.0",
        port=settings.shield_port,
        log_level=settings.log_level,
        access_log=True,
    )
    _shield_server = uvicorn.Server(config)

    async def _run():
        await _shield_server.serve()

    _shield_task = asyncio.create_task(_run())

    async with async_session() as db:
        site = await db.get(Site, site_id)
        if site:
            site.shield_active = True
            await db.commit()

    logger.info("Shield deployed for site %s on port %d", site_id, settings.shield_port)
    return True


async def undeploy_shield() -> bool:
    global _shield_server, _shield_task, _post_handler

    if _shield_server is None:
        return False

    _shield_server.should_exit = True
    if _shield_task:
        try:
            await asyncio.wait_for(_shield_task, timeout=10)
        except asyncio.TimeoutError:
            _shield_task.cancel()

    async with async_session() as db:
        result = await db.execute(select(Site).where(Site.shield_active == True))
        for site in result.scalars():
            site.shield_active = False
        await db.commit()

    _shield_server = None
    _shield_task = None
    _post_handler = None

    logger.info("Shield undeployed")
    return True


def is_shield_active() -> bool:
    return _shield_server is not None and not _shield_server.should_exit
