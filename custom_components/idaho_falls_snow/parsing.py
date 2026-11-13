import re

_WORKING_STATUSES = {"working", "in progress", "active", "plowing", "started"}
_COMPLETED_STATUSES = {"complete", "completed", "finished", "done", "plowed"}
_UPDATED_RE = re.compile(
    r"Updated\\s*:?[ \\t]*([A-Za-z]{3,9}\\.?\\s+\\d{1,2},\\s+\\d{4})",
    re.IGNORECASE,
)


def normalize_status(value):
    """Normalize a source status without matching substrings accidentally."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).split())


def working(value):
    """Return true only for recognized active status words or phrases."""
    normalized = normalize_status(value)
    return normalized in _WORKING_STATUSES or bool(
        set(normalized.split()) & {"working", "active", "plowing", "started"}
    ) or "in progress" in normalized


def completed(value):
    """Return true only for recognized completed status words."""
    normalized = normalize_status(value)
    return normalized in _COMPLETED_STATUSES or bool(
        set(normalized.split()) & {"complete", "completed", "finished", "done", "plowed"}
    )


def updated_date(text):
    """Extract the City page's displayed update date, including abbreviated months."""
    match = _UPDATED_RE.search(text or "")
    return match.group(1) if match else None


def zone_key(value):
    """Normalize GIS zone labels into stable integration keys."""
    normalized = normalize_status(value)
    if "downtown" in normalized or normalized == "dt":
        return "downtown"
    if normalized in {"a", "zone a", "1"} or normalized.endswith(" zone a"):
        return "a"
    if normalized in {"b", "zone b", "2"} or normalized.endswith(" zone b"):
        return "b"
    return normalized
