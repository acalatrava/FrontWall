import json
import logging
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger("webshield.crawler.forms")


def detect_forms(html: str, page_url: str) -> str | None:
    """Detect all <form> elements and return a JSON string describing them."""
    soup = BeautifulSoup(html, "lxml")
    forms = soup.find_all("form")

    if not forms:
        return None

    detected: list[dict] = []

    for form in forms:
        if not isinstance(form, Tag):
            continue

        action = form.get("action", "")
        method = (form.get("method", "GET") or "GET").upper()

        fields: list[dict] = []

        for inp in form.find_all(["input", "textarea", "select"]):
            if not isinstance(inp, Tag):
                continue
            name = inp.get("name")
            if not name:
                continue
            field_info: dict = {
                "name": name,
                "type": inp.get("type", "text") if inp.name == "input" else inp.name,
                "required": inp.has_attr("required"),
            }
            maxlength = inp.get("maxlength")
            if maxlength:
                field_info["maxlength"] = int(maxlength)
            pattern = inp.get("pattern")
            if pattern:
                field_info["pattern"] = pattern
            fields.append(field_info)

        detected.append({
            "action": str(action),
            "method": method,
            "page_url": page_url,
            "fields": fields,
        })

    if not detected:
        return None

    logger.debug("Detected %d forms on %s", len(detected), page_url)
    return json.dumps(detected)
