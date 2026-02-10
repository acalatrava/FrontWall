from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.admin_user import AdminUser
from schemas.auth import SetupRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/setup-required")
async def setup_required(db: AsyncSession = Depends(get_db)):
    count = await db.execute(select(func.count(AdminUser.id)))
    return {"setup_required": (count.scalar() or 0) == 0}


@router.post("/setup", response_model=TokenResponse)
async def setup(data: SetupRequest, db: AsyncSession = Depends(get_db)):
    count = await db.execute(select(func.count(AdminUser.id)))
    if (count.scalar() or 0) > 0:
        raise HTTPException(status_code=400, detail="Setup already completed")

    user = AdminUser(
        username=data.username,
        password_hash=_hash_password(data.password),
    )
    db.add(user)
    await db.commit()

    token = _create_token(user.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).where(AdminUser.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not _verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = _create_token(user.username)
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(user: AdminUser = Depends(get_current_user)):
    return {"username": user.username, "created_at": user.created_at.isoformat()}
