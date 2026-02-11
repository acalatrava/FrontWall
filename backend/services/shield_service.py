import asyncio
import logging
from dataclasses import dataclass, field
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
from shield.asset_learner import AssetLearner
from services.security_collector import collector as security_collector

logger = logging.getLogger("frontwall.services.shield")


@dataclass
class ShieldInstance:
    server: uvicorn.Server
    task: asyncio.Task
    post_handler: PostHandler
    asset_learner: AssetLearner
    port: int


_shields: dict[str, ShieldInstance] = {}


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
                "allowed_actions": rule.allowed_actions,
                "fields": fields,
            })
        return rule_dicts


def _parse_ip_list(raw: str) -> set[str]:
    if not raw or not raw.strip():
        return set()
    return {ip.strip() for ip in raw.split(",") if ip.strip()}


async def deploy_shield(site_id: str) -> int:
    if site_id in _shields:
        await undeploy_shield(site_id)

    cache_dir = Path(settings.cache_dir) / site_id
    if not cache_dir.exists():
        raise FileNotFoundError(f"Cache directory not found for site {site_id}. Run a crawl first.")

    async with async_session() as db:
        site = await db.get(Site, site_id)
        if not site:
            raise ValueError(f"Site {site_id} not found")
        if not site.shield_port:
            raise ValueError("Shield port must be configured before deploying")

        target_url = site.target_url
        internal_url = site.internal_url
        override_host = site.override_host
        port = site.shield_port

        waf_enabled = site.waf_enabled
        rate_limit_enabled = site.rate_limit_enabled
        rl_requests = site.rate_limit_requests
        rl_window = site.rate_limit_window
        security_headers_enabled = site.security_headers_enabled
        block_bots = site.block_bots
        block_suspicious_paths = site.block_suspicious_paths
        max_body_size = site.max_body_size
        ip_whitelist = _parse_ip_list(site.ip_whitelist)
        ip_blacklist = _parse_ip_list(site.ip_blacklist)

    for other_id, inst in _shields.items():
        if inst.port == port:
            raise ValueError(f"Port {port} is already in use by site {other_id}")

    scan_result = scan_cache_for_origins(cache_dir, target_url=target_url)
    csp = build_csp(scan_result)
    logger.info("Built dynamic CSP with %d external origins for site %s", len(scan_result["origins"]), site_id)

    asset_learner = AssetLearner(
        site_id=site_id,
        target_url=target_url,
        cache_dir=cache_dir,
        internal_url=internal_url,
        override_host=override_host,
    )

    shield_app = create_shield_app(
        site_id,
        csp=csp,
        asset_learner=asset_learner,
        security_headers=security_headers_enabled,
    )

    rate_limiter = RateLimiter(
        global_requests=rl_requests,
        global_window=rl_window,
    ) if rate_limit_enabled else None

    post_rules = await _load_post_rules(site_id)
    post_handler = PostHandler(
        rate_limiter or RateLimiter(),
        site_id=site_id,
        target_url=target_url,
        internal_url=internal_url,
        override_host=override_host,
        event_collector=security_collector,
    )
    post_handler.load_rules(post_rules)

    @shield_app.api_route("/{path:path}", methods=["POST"])
    async def handle_post(request: Request, path: str = ""):
        return await post_handler.handle_post(request)

    if waf_enabled:
        shield_app.add_middleware(
            WAFMiddleware,
            rate_limiter=rate_limiter,
            max_body_size=max_body_size,
            ip_whitelist=ip_whitelist,
            ip_blacklist=ip_blacklist,
            post_handler=post_handler,
            block_bots=block_bots,
            block_suspicious_paths=block_suspicious_paths,
            site_id=site_id,
            event_collector=security_collector,
        )

    config = uvicorn.Config(
        shield_app,
        host="0.0.0.0",
        port=port,
        log_level=settings.log_level,
        access_log=True,
    )
    server = uvicorn.Server(config)

    async def _run():
        await server.serve()

    task = asyncio.create_task(_run())

    _shields[site_id] = ShieldInstance(
        server=server,
        task=task,
        post_handler=post_handler,
        asset_learner=asset_learner,
        port=port,
    )

    async with async_session() as db:
        site = await db.get(Site, site_id)
        if site:
            site.shield_active = True
            await db.commit()

    logger.info("Shield deployed for site %s on port %d", site_id, port)
    return port


async def undeploy_shield(site_id: str) -> bool:
    instance = _shields.pop(site_id, None)
    if instance is None:
        return False

    instance.server.should_exit = True
    try:
        await asyncio.wait_for(instance.task, timeout=10)
    except asyncio.TimeoutError:
        instance.task.cancel()

    async with async_session() as db:
        site = await db.get(Site, site_id)
        if site:
            site.shield_active = False
            await db.commit()

    logger.info("Shield undeployed for site %s", site_id)
    return True


def is_shield_active(site_id: str) -> bool:
    inst = _shields.get(site_id)
    return inst is not None and not inst.server.should_exit


def get_all_shields_status() -> list[dict]:
    result = []
    for sid, inst in _shields.items():
        result.append({
            "site_id": sid,
            "port": inst.port,
            "active": not inst.server.should_exit,
            "learn_mode": inst.post_handler.learn_mode,
        })
    return result


def set_learn_mode(site_id: str, enabled: bool) -> bool:
    inst = _shields.get(site_id)
    if inst is None:
        return False
    inst.post_handler.learn_mode = enabled
    inst.asset_learner.enabled = enabled
    logger.info("Learn mode %s for site %s", "enabled" if enabled else "disabled", site_id)
    return True


def is_learn_mode(site_id: str) -> bool:
    inst = _shields.get(site_id)
    if inst is None:
        return False
    return inst.post_handler.learn_mode


def get_learned_posts(site_id: str) -> list[dict]:
    inst = _shields.get(site_id)
    if inst is None:
        return []
    return list(inst.post_handler.learned_posts)


def get_learned_assets(site_id: str) -> list[dict]:
    inst = _shields.get(site_id)
    if inst is None:
        return []
    return list(inst.asset_learner.learned_assets)


async def auto_deploy_if_needed() -> None:
    async with async_session() as db:
        result = await db.execute(select(Site).where(Site.shield_active == True))
        sites = result.scalars().all()

    for site in sites:
        cache_dir = Path(settings.cache_dir) / site.id
        if not cache_dir.exists():
            logger.warning("Site %s was marked as shielded but has no cache. Skipping.", site.id)
            async with async_session() as db:
                s = await db.get(Site, site.id)
                if s:
                    s.shield_active = False
                    await db.commit()
            continue

        if not site.shield_port:
            logger.warning("Site %s has no shield_port configured. Skipping auto-deploy.", site.id)
            async with async_session() as db:
                s = await db.get(Site, site.id)
                if s:
                    s.shield_active = False
                    await db.commit()
            continue

        try:
            await deploy_shield(site.id)
            logger.info("Auto-deployed shield for site %s on port %d", site.id, site.shield_port)
        except Exception as exc:
            logger.error("Failed to auto-deploy shield for site %s: %s", site.id, exc)
