import asyncio
import hashlib
import secrets
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.admin_user import AdminUser
from models.refresh_token import RefreshToken
from schemas.auth import SetupRequest, LoginRequest, AuthResponse
from services.security_collector import collector as security_collector
from utils import get_client_ip

router = APIRouter(prefix="/api/auth", tags=["auth"])

_login_attempts: dict[str, list[float]] = defaultdict(list)
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 300
_LOGIN_LOCKOUT_SECONDS = 600
_login_lock = asyncio.Lock()


async def _check_login_rate(ip: str) -> None:
    async with _login_lock:
        now = time.monotonic()
        cutoff = now - _LOGIN_WINDOW_SECONDS
        _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]

        if len(_login_attempts[ip]) >= _LOGIN_MAX_ATTEMPTS:
            oldest = _login_attempts[ip][0]
            remaining = int(_LOGIN_LOCKOUT_SECONDS - (now - oldest))
            raise HTTPException(
                status_code=429,
                detail=f"Too many login attempts. Try again in {max(remaining, 1)} seconds.",
            )


async def _record_login_attempt(ip: str) -> None:
    async with _login_lock:
        _login_attempts[ip].append(time.monotonic())


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _create_access_token(user_id: str, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "exp": now + timedelta(minutes=settings.jwt_access_expire_minutes),
        "iat": now,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def _create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


async def _store_refresh_token(
    db: AsyncSession, user_id: str, raw_token: str, family_id: str | None = None,
) -> str:
    if family_id is None:
        family_id = str(uuid.uuid4())

    token_hash = _hash_token(raw_token)
    expires = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)

    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family_id=family_id,
        expires_at=expires,
    )
    db.add(rt)
    await db.commit()
    return family_id


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_access_expire_minutes * 60,
        path="/api",
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_refresh_expire_days * 86400,
        path="/api/auth",
        domain=settings.cookie_domain,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/api", domain=settings.cookie_domain)
    response.delete_cookie(key="refresh_token", path="/api/auth", domain=settings.cookie_domain)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

    user = await db.get(AdminUser, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/setup-required")
async def setup_required(db: AsyncSession = Depends(get_db)):
    count = await db.execute(select(func.count(AdminUser.id)))
    return {"setup_required": (count.scalar() or 0) == 0}


_setup_lock = asyncio.Lock()


@router.post("/setup")
async def setup(data: SetupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    async with _setup_lock:
        count = await db.execute(select(func.count(AdminUser.id)))
        if (count.scalar() or 0) > 0:
            raise HTTPException(status_code=400, detail="Setup already completed")

        user = AdminUser(
            username=data.username,
            password_hash=_hash_password(data.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access = _create_access_token(user.id, user.username)
    refresh = _create_refresh_token()
    await _store_refresh_token(db, user.id, refresh)

    _set_auth_cookies(response, access, refresh)
    return {"user_id": user.id, "username": user.username}


@router.post("/login")
async def login(data: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    client_ip = get_client_ip(request)
    await _check_login_rate(client_ip)

    result = await db.execute(select(AdminUser).where(AdminUser.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not _verify_password(data.password, user.password_hash):
        await _record_login_attempt(client_ip)
        security_collector.emit(
            event_type="login_failed",
            severity="high",
            client_ip=client_ip,
            path="/api/auth/login",
            method="POST",
            user_agent=request.headers.get("user-agent", ""),
            details={"username": data.username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access = _create_access_token(user.id, user.username)
    refresh = _create_refresh_token()
    await _store_refresh_token(db, user.id, refresh)

    _set_auth_cookies(response, access, refresh)
    return {"user_id": user.id, "username": user.username}


@router.post("/refresh")
async def refresh_tokens(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    raw_refresh = request.cookies.get("refresh_token")
    if not raw_refresh:
        raise HTTPException(status_code=401, detail="No refresh token")

    token_hash = _hash_token(raw_refresh)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if not stored:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if stored.revoked:
        client_ip = get_client_ip(request)
        security_collector.emit(
            event_type="token_reuse",
            severity="critical",
            client_ip=client_ip,
            path="/api/auth/refresh",
            method="POST",
            user_agent=request.headers.get("user-agent", ""),
            details={"family_id": stored.family_id},
        )
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == stored.family_id)
            .values(revoked=True)
        )
        await db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=401,
            detail="Token reuse detected — all sessions revoked. Please log in again.",
        )

    if stored.expires_at < now:
        stored.revoked = True
        await db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh token expired")

    stored.revoked = True
    await db.flush()

    user = await db.get(AdminUser, stored.user_id)
    if not user:
        await db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="User not found")

    new_access = _create_access_token(user.id, user.username)
    new_refresh = _create_refresh_token()
    await _store_refresh_token(db, user.id, new_refresh, family_id=stored.family_id)

    _set_auth_cookies(response, new_access, new_refresh)
    return {"user_id": user.id, "username": user.username}


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    raw_refresh = request.cookies.get("refresh_token")
    if raw_refresh:
        token_hash = _hash_token(raw_refresh)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        if stored:
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == stored.family_id)
                .values(revoked=True)
            )
            await db.commit()

    _clear_auth_cookies(response)
    return {"status": "logged_out"}


@router.get("/me")
async def me(user: AdminUser = Depends(get_current_user)):
    return {"user_id": user.id, "username": user.username, "created_at": user.created_at.isoformat()}
