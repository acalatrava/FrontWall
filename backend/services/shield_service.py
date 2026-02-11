import asyncio
import logging
from pathlib import Path

import uvicorn
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database import async_session
from models.site import Site
from models.post_rule import PostRule, RuleField
from shield.server import create_shield_app
from shield.csp_builder import scan_cache_for_origins, build_csp
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

    async with async_session() as db:
        site = await db.get(Site, site_id)
        target_url = site.target_url if site else None

    scan_result = scan_cache_for_origins(cache_dir, target_url=target_url)
    csp = build_csp(scan_result)
    logger.info("Built dynamic CSP with %d external origins", len(scan_result["origins"]))

    shield_app = create_shield_app(site_id, csp=csp)

    rate_limiter = RateLimiter(
        global_requests=settings.rate_limit_requests,
        global_window=settings.rate_limit_window_seconds,
    )

    internal_url = site.internal_url if site else None
    override_host = site.override_host if site else None

    post_rules = await _load_post_rules(site_id)
    _post_handler = PostHandler(
        rate_limiter,
        site_id=site_id,
        target_url=target_url or "",
        internal_url=internal_url,
        override_host=override_host,
    )
    _post_handler.load_rules(post_rules)

    @shield_app.api_route("/{path:path}", methods=["POST"])
    async def handle_post(request: Request, path: str = ""):
        return await _post_handler.handle_post(request)

    shield_app.add_middleware(
        WAFMiddleware,
        rate_limiter=rate_limiter,
        max_body_size=settings.max_request_size_bytes,
        post_handler=_post_handler,
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


def set_learn_mode(enabled: bool) -> bool:
    if _post_handler is None:
        return False
    _post_handler.learn_mode = enabled
    logger.info("Learn mode %s", "enabled" if enabled else "disabled")
    return True


def is_learn_mode() -> bool:
    if _post_handler is None:
        return False
    return _post_handler.learn_mode


def get_learned_posts() -> list[dict]:
    if _post_handler is None:
        return []
    return list(_post_handler.learned_posts)


async def auto_deploy_if_needed() -> None:
    """Check if any site had shield_active=True and re-deploy it on startup."""
    async with async_session() as db:
        result = await db.execute(select(Site).where(Site.shield_active == True))
        site = result.scalar_one_or_none()
        if not site:
            return

        cache_dir = Path(settings.cache_dir) / site.id
        if not cache_dir.exists():
            logger.warning("Site %s was marked as shielded but has no cache. Skipping auto-deploy.", site.id)
            site.shield_active = False
            await db.commit()
            return

    try:
        await deploy_shield(site.id)
        logger.info("Auto-deployed shield for site %s on startup", site.id)
    except Exception as exc:
        logger.error("Failed to auto-deploy shield for site %s: %s", site.id, exc)
