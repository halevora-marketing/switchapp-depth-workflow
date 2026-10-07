from __future__ import annotations

import re


_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def safe_title(value: str, *, fallback: str = "Untitled Clip", limit: int = 100) -> str:
    """Return a descriptive title that is safe as a cross-platform folder name."""
    cleaned = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        cleaned = fallback
    if cleaned.upper() in _WINDOWS_RESERVED:
        cleaned = f"{cleaned} Clip"
    return cleaned[:limit].rstrip(" .") or fallback


def slug(value: str) -> str:
    normalized = safe_title(value).lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or "untitled-clip"

