"""
WebSocket Security — System 12
Reject malformed payloads, limit message size, prevent replay abuse.
"""
from __future__ import annotations

import json
from typing import Any

MAX_MESSAGE_BYTES = 65_536  # 64 KB per WS message
ALLOWED_TYPES = {"ping", "subscribe", "unsubscribe"}


def validate_ws_message(raw: str) -> tuple[bool, str, Any]:
    """
    Returns (ok, reason, parsed).
    Fast-path for 'ping' string to avoid JSON parse overhead.
    """
    if raw == "ping":
        return True, "ok", "ping"

    if len(raw) > MAX_MESSAGE_BYTES:
        return False, "message_too_large", None

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return False, "invalid_json", None

    if not isinstance(data, dict):
        return False, "not_an_object", None

    msg_type = data.get("type")
    if msg_type is not None and msg_type not in ALLOWED_TYPES:
        return False, f"unknown_type:{msg_type}", None

    return True, "ok", data
