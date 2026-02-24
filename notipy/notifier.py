"""Send a notification to an ntfy.sh topic."""

from __future__ import annotations

import os
import socket
import urllib.request
from urllib.error import URLError

from notipy.runner import RunResult

# ── Constants ─────────────────────────────────────────────────────────────────

ENV_TOPIC = "NOTIPY_TOPIC"
DEFAULT_TOPIC = "gasparyanartur-notipy-public"
NTFY_BASE_URL = "https://ntfy.sh"

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
    """POST a notification to ntfy.sh/<topic>.

    Topic resolution order
    ----------------------
    1. *topic* argument
    2. ``NOTIPY_TOPIC`` environment variable
    3. Built-in default (``gasparyanartur-notipy-public``)
    """
    resolved_topic = topic or os.environ.get(ENV_TOPIC) or DEFAULT_TOPIC

    url = f"{NTFY_BASE_URL}/{resolved_topic}"
    body = _build_body(result).encode("utf-8")
    tags = "white_check_mark" if result.succeeded else "x"

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Title": _build_title(result),
            "Tags": tags,
            "Priority": "default",
            "Content-Type": "text/plain; charset=utf-8",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
    except URLError as exc:
        raise RuntimeError(
            f"Failed to reach ntfy server at {url}: {exc.reason}"
        ) from exc
