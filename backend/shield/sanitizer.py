import re
import html
import logging
import unicodedata

import bleach

logger = logging.getLogger("frontwall.shield.sanitizer")

SQL_INJECTION_PATTERNS = [
    re.compile(r"(\b(union|select|insert|update|delete|drop|alter|create|exec|execute)\b.*\b(from|into|table|database|where)\b)", re.IGNORECASE),
    re.compile(r"(--|;|/\*|\*/|@@|@)", re.IGNORECASE),
    re.compile(r"(\b(or|and)\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    re.compile(r"('\s*(or|and)\s+')", re.IGNORECASE),
    re.compile(r"(0x[0-9a-fA-F]+)"),
]

XSS_PATTERNS = [
    re.compile(r"<script[\s>]", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe[\s>]", re.IGNORECASE),
    re.compile(r"<object[\s>]", re.IGNORECASE),
    re.compile(r"<embed[\s>]", re.IGNORECASE),
    re.compile(r"<link[\s>]", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
]

COMMAND_INJECTION_PATTERNS = [
    re.compile(r"[;&|`$]"),
    re.compile(r"\.\./"),
    re.compile(r"(cat|ls|rm|mv|cp|chmod|chown|wget|curl|bash|sh|nc|netcat)\s", re.IGNORECASE),
]

FIELD_TYPE_VALIDATORS = {
    "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    "phone": re.compile(r"^[\d\s+\-().]{6,20}$"),
    "number": re.compile(r"^-?\d+(\.\d+)?$"),
    "url": re.compile(r"^https?://[^\s<>\"']+$"),
    "text": re.compile(r"^[\s\S]*$"),
}


def detect_sql_injection(value: str) -> bool:
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            return True
    return False


def detect_xss(value: str) -> bool:
    for pattern in XSS_PATTERNS:
        if pattern.search(value):
            return True
    return False


def detect_command_injection(value: str) -> bool:
    for pattern in COMMAND_INJECTION_PATTERNS:
        if pattern.search(value):
            return True
    return False


def sanitize_value(value: str, field_type: str = "text") -> str:
    """Sanitize a form field value: normalize unicode, strip HTML, neutralize threats."""
    value = unicodedata.normalize("NFC", value)
    value = value.replace("\x00", "")
    value = bleach.clean(value, tags=[], attributes={}, strip=True)
    value = html.unescape(value)
    value = bleach.clean(value, tags=[], attributes={}, strip=True)

    if field_type == "email":
        value = re.sub(r"[^\w.@+\-]", "", value)
    elif field_type == "phone":
        value = re.sub(r"[^\d\s+\-().]", "", value)
    elif field_type == "number":
        value = re.sub(r"[^\d.\-]", "", value)
    elif field_type == "url":
        if not re.match(r"^https?://", value):
            value = ""

    return value.strip()


def validate_field_type(value: str, field_type: str) -> bool:
    validator = FIELD_TYPE_VALIDATORS.get(field_type)
    if validator:
        return bool(validator.match(value))
    return True


class InputSanitizer:
    """Comprehensive input sanitizer for POST data."""

    def sanitize_and_validate(
        self,
        data: dict[str, str],
        field_rules: list[dict],
    ) -> tuple[dict[str, str], list[str]]:
        """Sanitize and validate form data against field rules.
        Returns (sanitized_data, list_of_errors).
        """
        sanitized: dict[str, str] = {}
        errors: list[str] = []
        allowed_fields = {f["field_name"] for f in field_rules}

        for key in data:
            if key not in allowed_fields:
                logger.warning("Stripped unknown field: %s", key)

        for rule in field_rules:
            name = rule["field_name"]
            ftype = rule.get("field_type", "text")
            required = rule.get("required", False)
            max_length = rule.get("max_length", 1000)
            regex = rule.get("validation_regex")

            raw_value = data.get(name, "")

            if required and not raw_value:
                errors.append(f"Field '{name}' is required")
                continue

            if not raw_value:
                continue

            if len(raw_value) > max_length:
                errors.append(f"Field '{name}' exceeds max length ({max_length})")
                continue

            if detect_sql_injection(raw_value):
                errors.append(f"Field '{name}' contains potentially dangerous content")
                logger.warning("SQL injection attempt in field '%s'", name)
                continue

            if detect_xss(raw_value):
                errors.append(f"Field '{name}' contains potentially dangerous content")
                logger.warning("XSS attempt in field '%s'", name)
                continue

            clean_value = sanitize_value(raw_value, ftype)

            if not validate_field_type(clean_value, ftype):
                errors.append(f"Field '{name}' has invalid format for type '{ftype}'")
                continue

            if regex:
                if not re.match(regex, clean_value):
                    errors.append(f"Field '{name}' does not match required pattern")
                    continue

            sanitized[name] = clean_value

        return sanitized, errors
