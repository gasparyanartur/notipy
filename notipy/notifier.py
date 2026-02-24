"""Send a notification to an ntfy.sh topic."""

from __future__ import annotations

import http.client
import json
import os
import socket
import ssl

from notipy.runner import RunResult

# ── Constants ─────────────────────────────────────────────────────────────────

ENV_TOPIC = "NOTIPY_TOPIC"
DEFAULT_TOPIC = "gasparyanartur-notipy-public"
NTFY_HOST = "ntfy.sh"

# ntfy message body cap (server enforces 4096 bytes)
_MAX_BODY = 4000


def _build_title(result: RunResult) -> str:
    icon = "✅" if result.succeeded else "❌"
    cmd = result.command if len(result.command) <= 60 else result.command[:57] + "..."
    suffix = "done" if result.succeeded else f"failed (exit {result.returncode})"
    return f"{icon} {cmd!r} {suffix}"


def _build_body(result: RunResult) -> str:
    hostname = socket.gethostname()
    log = result.combined_log()
    header = f"Host: {hostname}\n\n"
    available = _MAX_BODY - len(header)
    if len(log) > available:
        log = log[:available - 22] + "\n\n... (output truncated)"
    return header + log


def send_notification(result: RunResult, topic: str | None = None) -> None:
    """POST a notification to ntfy.sh.

    Topic resolution order
    ----------------------
    1. *topic* argument
    2. ``NOTIPY_TOPIC`` environment variable
    3. Built-in default (``gasparyanartur-notipy-public``)
    """
    resolved_topic = topic or os.environ.get(ENV_TOPIC) or DEFAULT_TOPIC

    tags = ["white_check_mark"] if result.succeeded else ["x"]
    payload = {
        "topic": resolved_topic,
        "title": _build_title(result),
        "message": _build_body(result),
        "tags": tags,
    }
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(NTFY_HOST, context=ctx, timeout=30)
    try:
        conn.request(
            "POST",
            "/",
            body=encoded,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        body = resp.read()
        if resp.status >= 400:
            raise RuntimeError(
                f"ntfy server returned HTTP {resp.status}: "
                f"{body.decode('utf-8', errors='replace')}"
            )
    finally:
        conn.close()
