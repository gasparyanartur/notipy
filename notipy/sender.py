"""Send an email notification with a logs.txt attachment via SMTP."""

from __future__ import annotations

import os
import smtplib
import socket
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from notipy.runner import RunResult


# ── Environment variable names ────────────────────────────────────────────────

ENV_SMTP_HOST = "NOTIPY_SMTP_HOST"
ENV_SMTP_PORT = "NOTIPY_SMTP_PORT"
ENV_SMTP_USER = "NOTIPY_SMTP_USER"
ENV_SMTP_PASS = "NOTIPY_SMTP_PASS"
ENV_FROM_ADDR = "NOTIPY_FROM_ADDR"

_DEFAULT_SMTP_HOST = "smtp.gmail.com"
_DEFAULT_SMTP_PORT = 587


def _build_subject(result: RunResult) -> str:
    status = "✅ done" if result.succeeded else f"❌ failed (exit {result.returncode})"
    # Keep subject short – trim command if needed
    cmd = result.command if len(result.command) <= 60 else result.command[:57] + "..."
    return f"notipy: {cmd!r} {status}"


def _build_body(result: RunResult) -> str:
    hostname = socket.gethostname()
    status = "SUCCESS ✅" if result.succeeded else f"FAILED ❌  (exit code {result.returncode})"
    lines = [
        f"Host:      {hostname}",
        f"Command:   {result.command}",
        f"Status:    {status}",
        "",
        "Full output is attached as logs.txt.",
    ]
    return "\n".join(lines)


def send_notification(
    to_addr: str,
    result: RunResult,
    subject: str | None = None,
) -> None:
    """Send an email to *to_addr* with the command result.

    Required environment variables
    --------------------------------
    NOTIPY_SMTP_USER   SMTP login username (also used as the From address by default)
    NOTIPY_SMTP_PASS   SMTP login password / app-password

    Optional environment variables
    --------------------------------
    NOTIPY_SMTP_HOST   SMTP server hostname  (default: smtp.gmail.com)
    NOTIPY_SMTP_PORT   SMTP port             (default: 587, STARTTLS)
    NOTIPY_FROM_ADDR   Sender address        (default: NOTIPY_SMTP_USER)
    """
    smtp_host = os.environ.get(ENV_SMTP_HOST, _DEFAULT_SMTP_HOST)
    smtp_port = int(os.environ.get(ENV_SMTP_PORT, _DEFAULT_SMTP_PORT))
    smtp_user = os.environ.get(ENV_SMTP_USER)
    smtp_pass = os.environ.get(ENV_SMTP_PASS)
    from_addr = os.environ.get(ENV_FROM_ADDR) or smtp_user

    if not smtp_user or not smtp_pass:
        raise EnvironmentError(
            f"SMTP credentials not set. Please export {ENV_SMTP_USER} and {ENV_SMTP_PASS}."
        )
    if not from_addr:
        raise EnvironmentError(
            f"Sender address unknown. Set {ENV_FROM_ADDR} or {ENV_SMTP_USER}."
        )

    final_subject = subject or _build_subject(result)

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = final_subject

    # Plain-text body
    msg.attach(MIMEText(_build_body(result), "plain", "utf-8"))

    # logs.txt attachment
    log_bytes = result.combined_log().encode("utf-8")
    attachment = MIMEBase("text", "plain", charset="utf-8")
    attachment.set_payload(log_bytes)
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename="logs.txt")
    msg.attach(attachment)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_addr, to_addr, msg.as_string())
