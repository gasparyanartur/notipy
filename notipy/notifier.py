"""Send a notification to an ntfy.sh topic."""

from __future__ import annotations

import http.client
import json
import os
import socket
import ssl

from notipy.runner import RunResult

# ── Constants ─────────────────────────────────────────────────────────────────

ENV_ADDR = "NOTIPY_ADDR"
DEFAULT_ADDR = "gasparyanartur-public"
NTFY_HOST = "ntfy.sh"

# ntfy message body cap (server enforces 4096 bytes)
_MAX_BODY = 4000


def _build_title(result: RunResult) -> str:
    icon = "✅" if result.succeeded else "❌"
    cmd = result.command if len(result.command) <= 60 else result.command[:57] + "..."
    suffix = "done" if result.succeeded else f"failed (exit {result.returncode})"
    return f"{icon} {cmd!r} {suffix} ({result.duration:.1f}s)"


def _build_body(result: RunResult) -> str:
    hostname = socket.gethostname()
    log = result.combined_log()
    header = f"Host: {hostname}\n\n"
    body = header + log
    if len(body) > _MAX_BODY:
        keep = _MAX_BODY - len(header) - 24
        body = header + log[:keep] + "\n\n... (output truncated)"
    return body


def send_notification(result: RunResult, addr: str | None = None) -> None:
    """POST a notification to ntfy.sh.

    Address resolution order
    ------------------------
    1. *addr* argument
    2. ``NOTIPY_ADDR`` environment variable
    3. Built-in default (``gasparyanartur-public``)

    The ntfy topic is constructed as ``notipy-{addr}``.
    """
    resolved_addr = addr or os.environ.get(ENV_ADDR) or DEFAULT_ADDR
    resolved_topic = f"notipy-{resolved_addr}"

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
