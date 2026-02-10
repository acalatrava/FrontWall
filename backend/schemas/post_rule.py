from datetime import datetime
from pydantic import BaseModel


class RuleFieldSchema(BaseModel):
    field_name: str
    field_type: str = "text"
    required: bool = False
    max_length: int = 1000
    validation_regex: str | None = None


class PostRuleCreate(BaseModel):
    site_id: str
    name: str
    url_pattern: str
    forward_to: str
    is_active: bool = True
    success_redirect: str | None = None
    success_message: str | None = None
    rate_limit_requests: int = 10
    rate_limit_window: int = 60
    honeypot_field: str | None = None
    enable_csrf: bool = False
    fields: list[RuleFieldSchema] = []


class PostRuleUpdate(BaseModel):
    name: str | None = None
    url_pattern: str | None = None
    forward_to: str | None = None
    is_active: bool | None = None
    success_redirect: str | None = None
    success_message: str | None = None
    rate_limit_requests: int | None = None
    rate_limit_window: int | None = None
    honeypot_field: str | None = None
    enable_csrf: bool | None = None
    fields: list[RuleFieldSchema] | None = None


class RuleFieldResponse(BaseModel):
    id: str
    field_name: str
    field_type: str
    required: bool
    max_length: int
    validation_regex: str | None

    model_config = {"from_attributes": True}


class PostRuleResponse(BaseModel):
    id: str
    site_id: str
    name: str
    url_pattern: str
    forward_to: str
    is_active: bool
    success_redirect: str | None
    success_message: str | None
    rate_limit_requests: int
    rate_limit_window: int
    honeypot_field: str | None
    enable_csrf: bool
    fields: list[RuleFieldResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
