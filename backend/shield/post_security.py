import re
import logging
from urllib.parse import unquote

logger = logging.getLogger("frontwall.shield.post_security")

LFI_PATTERNS = [
    re.compile(r"\.\./"),
    re.compile(r"\.\.\\"),
    re.compile(r"\.\.%2f", re.IGNORECASE),
    re.compile(r"\.\.%5c", re.IGNORECASE),
    re.compile(r"php://", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"filter://", re.IGNORECASE),
    re.compile(r"expect://", re.IGNORECASE),
    re.compile(r"zip://", re.IGNORECASE),
    re.compile(r"phar://", re.IGNORECASE),
    re.compile(r"data://", re.IGNORECASE),
    re.compile(r"glob://", re.IGNORECASE),
    re.compile(r"/etc/passwd"),
    re.compile(r"/etc/shadow"),
    re.compile(r"/proc/self"),
    re.compile(r"wp-config\.php", re.IGNORECASE),
    re.compile(r"\.htaccess", re.IGNORECASE),
    re.compile(r"web\.config", re.IGNORECASE),
]

SUSPICIOUS_PARAM_NAMES = {
    "loop-file", "template", "file", "filepath", "path",
    "page", "include", "require", "dir", "document",
    "folder", "root", "pg", "style", "php_path",
    "doc", "document_root", "load_file",
}

NULL_BYTE_PATTERN = re.compile(r"%00|\\x00|\x00")


def _deep_decode(value: str, max_rounds: int = 3) -> str:
    """Recursively URL-decode a value to catch double/triple encoding."""
    prev = value
    for _ in range(max_rounds):
        decoded = unquote(prev)
        if decoded == prev:
            break
        prev = decoded
    return prev


def scan_value_for_lfi(value: str) -> str | None:
    """Check a single value for LFI patterns. Returns the matched threat or None."""
    decoded = _deep_decode(value)
    for variant in (value, decoded):
        for pattern in LFI_PATTERNS:
            if pattern.search(variant):
                return pattern.pattern
    return None


def scan_value_for_null_byte(value: str) -> bool:
    decoded = _deep_decode(value)
    return bool(NULL_BYTE_PATTERN.search(value) or NULL_BYTE_PATTERN.search(decoded))


def scan_post_data(
    raw_data: dict[str, str],
    client_ip: str = "",
    path: str = "",
) -> dict | None:
    """Scan all POST field names and values for injection attacks.

    Returns a dict with threat details if blocked, or None if clean.
    """
    for name, value in raw_data.items():
        name_lower = name.lower().replace("_", "-")
        if name_lower in SUSPICIOUS_PARAM_NAMES:
            lfi_hit = scan_value_for_lfi(value)
            if lfi_hit:
                logger.warning(
                    "LFI via suspicious param '%s' blocked (pattern: %s, IP: %s, path: %s)",
                    name, lfi_hit, client_ip, path,
                )
                return {
                    "threat": "lfi_suspicious_param",
                    "param": name,
                    "pattern": lfi_hit,
                }

        lfi_hit = scan_value_for_lfi(value)
        if lfi_hit:
            logger.warning(
                "LFI in field '%s' blocked (pattern: %s, IP: %s, path: %s)",
                name, lfi_hit, client_ip, path,
            )
            return {
                "threat": "lfi_value",
                "param": name,
                "pattern": lfi_hit,
            }

        if scan_value_for_null_byte(value):
            logger.warning(
                "Null byte in field '%s' blocked (IP: %s, path: %s)",
                name, client_ip, path,
            )
            return {
                "threat": "null_byte",
                "param": name,
            }

    return None
