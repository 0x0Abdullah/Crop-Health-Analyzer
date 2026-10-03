"""User preferences: defaults, validation and persistence.

Settings are stored in the local SQLite database (``settings`` table) so they survive browser
refreshes and app restarts. Every value is validated against ``SCHEMA`` before it is used, so a
corrupted or outdated stored value can never break the interface.
"""
from typing import Any, Dict, List

THEMES: List[str] = ["System", "Light", "Dark"]
TEXT_SIZES: List[str] = ["Small", "Default", "Large"]

DEFAULTS: Dict[str, Any] = {
    "theme": "System",            # System follows the operating-system / browser preference
    "text_size": "Default",       # scales the whole interface
    "reduce_motion": False,       # disables animations and transitions
    "default_crop": "",           # pre-selected crop on Analyze / Plants ("" = first supported crop)
    "show_reminders_home": True,  # show due follow-up reminders on the Home page
    "show_quality_details": False,  # show sharpness / brightness numbers for uploaded photos
    "auto_open_results": True,    # jump to the results page when an assessment finishes
    "save_chats": True,           # store assistant conversations in the local database
}

# key -> (type, allowed values or None)
SCHEMA: Dict[str, Any] = {
    "theme": (str, THEMES),
    "text_size": (str, TEXT_SIZES),
    "reduce_motion": (bool, None),
    "default_crop": (str, None),
    "show_reminders_home": (bool, None),
    "show_quality_details": (bool, None),
    "auto_open_results": (bool, None),
    "save_chats": (bool, None),
}


def sanitize(raw: Dict[str, Any], crops: List[str] = None) -> Dict[str, Any]:
    """Return a complete, valid settings dict: unknown keys dropped, bad values replaced by defaults."""
    out = dict(DEFAULTS)
    raw = raw or {}
    for key, (typ, allowed) in SCHEMA.items():
        if key not in raw:
            continue
        val = raw[key]
        if typ is bool:
            if isinstance(val, bool):
                out[key] = val
        elif typ is str and isinstance(val, str):
            if allowed is None or val in allowed:
                out[key] = val
    if crops is not None and out["default_crop"] not in crops:
        out["default_crop"] = ""
    return out


def load_settings(repo, crops: List[str] = None) -> Dict[str, Any]:
    try:
        return sanitize(repo.get_settings(), crops)
    except Exception:  # a broken settings table must never stop the app from starting
        return sanitize({}, crops)


def save_setting(repo, key: str, value: Any, crops: List[str] = None) -> Dict[str, Any]:
    """Validate and persist one setting; returns the full, sanitized settings dict."""
    if key not in SCHEMA:
        raise KeyError(f"Unknown setting: {key}")
    current = load_settings(repo, crops)
    current[key] = value
    clean = sanitize(current, crops)
    repo.set_setting(key, clean[key])
    return clean


def reset_settings(repo) -> Dict[str, Any]:
    repo.clear_settings()
    return dict(DEFAULTS)
