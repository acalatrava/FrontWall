import asyncio
import hashlib
import hmac
import secrets
import time
import uuid
import logging
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
from models.passkey import Passkey
from schemas.auth import (
    SetupRequest, LoginRequest, AuthResponse,
    InviteRequest, AcceptInviteRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    UserResponse, UserUpdateRequest, PasskeyRegisterRequest,
)
from services.security_collector import collector as security_collector
from services.email_service import send_invite, send_password_reset
from utils import get_client_ip

logger = logging.getLogger("frontwall.api.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

_login_attempts: dict[str, list[float]] = defaultdict(list)
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 300
_LOGIN_LOCKOUT_SECONDS = 600
_login_lock = asyncio.Lock()

_ACCOUNT_LOCKOUT_THRESHOLD = 10
_ACCOUNT_LOCKOUT_MINUTES = 30

_webauthn_challenges: dict[str, tuple[bytes, float]] = {}
_CHALLENGE_TTL = 300


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
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _create_access_token(user_id: str, username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": now + timedelta(minutes=settings.jwt_access_expire_minutes),
        "iat": now,
        "type": "access",
        "jti": str(uuid.uuid4()),
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


async def _check_account_lock(user: AdminUser, db: AsyncSession) -> None:
    if user.locked_until:
        lock_time = user.locked_until.replace(tzinfo=timezone.utc) if user.locked_until.tzinfo is None else user.locked_until
        if lock_time > datetime.now(timezone.utc):
            remaining = int((lock_time - datetime.now(timezone.utc)).total_seconds())
            raise HTTPException(
                status_code=423,
                detail=f"Account locked. Try again in {max(remaining, 1)} seconds.",
            )
        user.locked_until = None
        user.failed_logins = 0
        await db.flush()


async def _record_failed_login(user: AdminUser, db: AsyncSession) -> None:
    user.failed_logins = (user.failed_logins or 0) + 1
    if user.failed_logins >= _ACCOUNT_LOCKOUT_THRESHOLD:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=_ACCOUNT_LOCKOUT_MINUTES)
        logger.warning("Account %s locked after %d failed attempts", user.username, user.failed_logins)
    await db.commit()


async def _clear_failed_logins(user: AdminUser, db: AsyncSession) -> None:
    if user.failed_logins:
        user.failed_logins = 0
        user.locked_until = None
        await db.flush()


async def _issue_tokens(user: AdminUser, response: Response, db: AsyncSession) -> dict:
    user.last_login = datetime.now(timezone.utc)
    await _clear_failed_logins(user, db)
    await db.commit()

    access = _create_access_token(user.id, user.username, user.role)
    refresh = _create_refresh_token()
    await _store_refresh_token(db, user.id, refresh)

    _set_auth_cookies(response, access, refresh)
    return {"user_id": user.id, "username": user.username, "role": user.role}


# ── Dependencies ──

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
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")
    return user


async def require_admin(user: AdminUser = Depends(get_current_user)) -> AdminUser:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ── Setup ──

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
            email=data.email,
            password_hash=_hash_password(data.password),
            role="admin",
            is_active=True,
            email_verified=bool(data.email),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return await _issue_tokens(user, response, db)


# ── Login ──

@router.post("/login")
async def login(data: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    client_ip = get_client_ip(request)
    await _check_login_rate(client_ip)

    result = await db.execute(select(AdminUser).where(AdminUser.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not _verify_password(data.password, user.password_hash):
        if user:
            await _record_failed_login(user, db)
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

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    await _check_account_lock(user, db)

    return await _issue_tokens(user, response, db)


# ── Token refresh ──

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

    expires_at = stored.expires_at.replace(tzinfo=timezone.utc) if stored.expires_at.tzinfo is None else stored.expires_at
    if expires_at < now:
        stored.revoked = True
        await db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh token expired")

    stored.revoked = True
    await db.flush()

    user = await db.get(AdminUser, stored.user_id)
    if not user or not user.is_active:
        await db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    new_access = _create_access_token(user.id, user.username, user.role)
    new_refresh = _create_refresh_token()
    await _store_refresh_token(db, user.id, new_refresh, family_id=stored.family_id)

    _set_auth_cookies(response, new_access, new_refresh)
    return {"user_id": user.id, "username": user.username, "role": user.role}


# ── Logout ──

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


# ── Me ──

@router.get("/me")
async def me(user: AdminUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    pk_count = await db.execute(
        select(func.count(Passkey.id)).where(Passkey.user_id == user.id)
    )
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "has_passkey": (pk_count.scalar() or 0) > 0,
        "created_at": user.created_at.isoformat(),
    }


# ── Invite ──

@router.post("/invite")
async def invite_user(
    data: InviteRequest,
    admin: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(AdminUser).where(AdminUser.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)

    user = AdminUser(
        username=data.email.split("@")[0] + "_" + secrets.token_hex(3),
        email=data.email,
        password_hash="!invited",
        role=data.role,
        is_active=False,
        invite_token_hash=token_hash,
        invite_expires=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    invite_url = f"{settings.base_url}/accept-invite?token={raw_token}"
    await send_invite(data.email, invite_url, admin.username)

    return {"status": "invited", "user_id": user.id, "email": data.email}


@router.post("/accept-invite")
async def accept_invite(data: AcceptInviteRequest, response: Response, db: AsyncSession = Depends(get_db)):
    token_hash = _hash_token(data.token)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(AdminUser).where(AdminUser.invite_token_hash == token_hash)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired invite")

    invite_exp = user.invite_expires
    if invite_exp:
        invite_exp = invite_exp.replace(tzinfo=timezone.utc) if invite_exp.tzinfo is None else invite_exp
    if not invite_exp or invite_exp < now:
        raise HTTPException(status_code=400, detail="Invite has expired")

    existing_result = await db.execute(select(AdminUser).where(AdminUser.username == data.username))
    existing_user = existing_result.scalar_one_or_none()
    if existing_user and existing_user.id != user.id:
        raise HTTPException(status_code=409, detail="Username already taken")

    user.username = data.username
    user.password_hash = _hash_password(data.password)
    user.is_active = True
    user.email_verified = True
    user.invite_token_hash = None
    user.invite_expires = None
    await db.commit()

    return await _issue_tokens(user, response, db)


# ── Password reset ──

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).where(AdminUser.email == data.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        raw_token = secrets.token_urlsafe(48)
        user.reset_token_hash = _hash_token(raw_token)
        user.reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.commit()

        reset_url = f"{settings.base_url}/reset-password?token={raw_token}"
        await send_password_reset(user.email, reset_url)

    return {"status": "ok", "message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    token_hash = _hash_token(data.token)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(AdminUser).where(AdminUser.reset_token_hash == token_hash)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    reset_exp = user.reset_expires
    if reset_exp:
        reset_exp = reset_exp.replace(tzinfo=timezone.utc) if reset_exp.tzinfo is None else reset_exp
    if not reset_exp or reset_exp < now:
        raise HTTPException(status_code=400, detail="Reset token has expired")

    user.password_hash = _hash_password(data.password)
    user.reset_token_hash = None
    user.reset_expires = None
    user.failed_logins = 0
    user.locked_until = None

    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .values(revoked=True)
    )
    await db.commit()

    return {"status": "ok", "message": "Password reset successfully. Please log in."}


# ── User management (admin only) ──

@router.get("/users")
async def list_users(
    admin: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AdminUser).order_by(AdminUser.created_at))
    users = result.scalars().all()

    response = []
    for u in users:
        pk_count = await db.execute(
            select(func.count(Passkey.id)).where(Passkey.user_id == u.id)
        )
        response.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "email_verified": u.email_verified,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat(),
            "has_passkey": (pk_count.scalar() or 0) > 0,
        })
    return response


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdateRequest,
    admin: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == admin.id and data.role and data.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
    if user_id == admin.id and data.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user = await db.get(AdminUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
        if not data.is_active:
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id)
                .values(revoked=True)
            )

    await db.commit()
    return {"status": "updated", "user_id": user_id}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = await db.get(AdminUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await db.execute(delete(Passkey).where(Passkey.user_id == user_id))
    await db.delete(user)
    await db.commit()
    return {"status": "deleted", "user_id": user_id}


# ── Passkey / WebAuthn ──

@router.post("/passkey/register-options")
async def passkey_register_options(
    data: PasskeyRegisterRequest,
    user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from webauthn import generate_registration_options, options_to_json
    from webauthn.helpers.structs import (
        AuthenticatorSelectionCriteria,
        ResidentKeyRequirement,
        UserVerificationRequirement,
        PublicKeyCredentialDescriptor,
    )

    existing = await db.execute(
        select(Passkey).where(Passkey.user_id == user.id)
    )
    exclude = [
        PublicKeyCredentialDescriptor(id=pk.credential_id)
        for pk in existing.scalars().all()
    ]

    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=user.id.encode("utf-8"),
        user_name=user.username,
        user_display_name=user.username,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )

    _webauthn_challenges[user.id] = (options.challenge, time.monotonic())

    return {"options": options_to_json(options), "passkey_name": data.name}


@router.post("/passkey/register-verify")
async def passkey_register_verify(
    request: Request,
    user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from webauthn import verify_registration_response
    from webauthn.helpers import parse_registration_credential_json
    import json as _json

    body = await request.json()
    credential_json = body.get("credential")
    passkey_name = body.get("name", "My Passkey")[:64]

    if user.id not in _webauthn_challenges:
        raise HTTPException(status_code=400, detail="No pending registration challenge")

    challenge, ts = _webauthn_challenges.pop(user.id)
    if time.monotonic() - ts > _CHALLENGE_TTL:
        raise HTTPException(status_code=400, detail="Challenge expired")

    try:
        credential = parse_registration_credential_json(_json.dumps(credential_json))
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
        )
    except Exception as exc:
        logger.warning("Passkey registration failed for %s: %s", user.username, exc)
        raise HTTPException(status_code=400, detail="Passkey registration failed")

    existing = await db.execute(
        select(Passkey).where(Passkey.credential_id == verification.credential_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This passkey is already registered")

    transports_str = ",".join(body.get("transports", []))

    pk = Passkey(
        user_id=user.id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        name=passkey_name,
        transports=transports_str if transports_str else None,
    )
    db.add(pk)
    await db.commit()

    return {"status": "registered", "passkey_id": pk.id, "name": pk.name}


@router.post("/passkey/auth-options")
async def passkey_auth_options(db: AsyncSession = Depends(get_db)):
    from webauthn import generate_authentication_options, options_to_json
    from webauthn.helpers.structs import UserVerificationRequirement

    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    session_id = secrets.token_urlsafe(32)
    _webauthn_challenges[session_id] = (options.challenge, time.monotonic())

    return {"options": options_to_json(options), "session_id": session_id}


@router.post("/passkey/auth-verify")
async def passkey_auth_verify(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    from webauthn import verify_authentication_response
    from webauthn.helpers import parse_authentication_credential_json
    import json as _json

    body = await request.json()
    credential_json = body.get("credential")
    session_id = body.get("session_id")

    if not session_id or session_id not in _webauthn_challenges:
        raise HTTPException(status_code=400, detail="No pending authentication challenge")

    challenge, ts = _webauthn_challenges.pop(session_id)
    if time.monotonic() - ts > _CHALLENGE_TTL:
        raise HTTPException(status_code=400, detail="Challenge expired")

    try:
        credential = parse_authentication_credential_json(_json.dumps(credential_json))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid credential data")

    result = await db.execute(
        select(Passkey).where(Passkey.credential_id == credential.raw_id)
    )
    stored_pk = result.scalar_one_or_none()

    if not stored_pk:
        client_ip = get_client_ip(request)
        security_collector.emit(
            event_type="passkey_auth_failed",
            severity="high",
            client_ip=client_ip,
            path="/api/auth/passkey/auth-verify",
            method="POST",
            user_agent=request.headers.get("user-agent", ""),
        )
        raise HTTPException(status_code=401, detail="Unknown passkey")

    user = await db.get(AdminUser, stored_pk.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
            credential_public_key=stored_pk.public_key,
            credential_current_sign_count=stored_pk.sign_count,
        )
    except Exception as exc:
        logger.warning("Passkey auth failed for %s: %s", user.username, exc)
        raise HTTPException(status_code=401, detail="Passkey verification failed")

    stored_pk.sign_count = verification.new_sign_count
    stored_pk.last_used = datetime.now(timezone.utc)

    return await _issue_tokens(user, response, db)


@router.get("/passkeys")
async def list_passkeys(
    user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from webauthn.helpers import bytes_to_base64url

    result = await db.execute(
        select(Passkey).where(Passkey.user_id == user.id).order_by(Passkey.created_at)
    )
    passkeys = result.scalars().all()
    return [
        {
            "id": pk.id,
            "name": pk.name,
            "created_at": pk.created_at.isoformat(),
            "last_used": pk.last_used.isoformat() if pk.last_used else None,
            "credential_id_preview": bytes_to_base64url(pk.credential_id)[:16] + "...",
        }
        for pk in passkeys
    ]


@router.delete("/passkeys/{passkey_id}")
async def delete_passkey(
    passkey_id: str,
    user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pk = await db.get(Passkey, passkey_id)
    if not pk or pk.user_id != user.id:
        raise HTTPException(status_code=404, detail="Passkey not found")

    await db.delete(pk)
    await db.commit()
    return {"status": "deleted"}
