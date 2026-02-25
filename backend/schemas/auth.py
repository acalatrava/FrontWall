import re
from datetime import datetime

from pydantic import BaseModel, field_validator, EmailStr


class SetupRequest(BaseModel):
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if len(v) > 128:
            raise ValueError("Password must not exceed 128 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        EmailStr._validate(v)
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if len(v) > 320:
            raise ValueError("Email too long")
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) > 128:
            raise ValueError("Password too long")
        return v


class AuthResponse(BaseModel):
    user_id: str
    email: str
    role: str


class InviteRequest(BaseModel):
    email: str
    role: str = "viewer"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        EmailStr._validate(v)
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("admin", "viewer"):
            raise ValueError("Role must be 'admin' or 'viewer'")
        return v


class AcceptInviteRequest(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if len(v) > 128:
            raise ValueError("Password must not exceed 128 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) > 320:
            raise ValueError("Email too long")
        return v


class ResetPasswordRequest(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if len(v) > 128:
            raise ValueError("Password must not exceed 128 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    email_verified: bool
    last_login: datetime | None
    created_at: datetime
    has_passkey: bool = False

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is not None and v not in ("admin", "viewer"):
            raise ValueError("Role must be 'admin' or 'viewer'")
        return v


class PasskeyRegisterRequest(BaseModel):
    name: str = "My Passkey"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 64:
            raise ValueError("Passkey name too long")
        if not v:
            v = "My Passkey"
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if len(v) > 128:
            raise ValueError("Password must not exceed 128 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v
