"""notipy CLI entrypoint."""

from __future__ import annotations

import os
import sys

import argparse

from notipy.runner import run_command
from notipy.sender import send_notification

ENV_EMAIL_ADDR = "NOTIPY_EMAIL_ADDR"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notipy",
        description=(
            "Run a command and send an email notification with the output when it finishes.\n\n"
            "Use -- to separate notipy options from the command:\n"
            "  notipy --to you@example.com -- python train.py --epochs 100"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--to", "-t",
        dest="email",
        metavar="ADDRESS",
        default=None,
        help=(
            f"Recipient email address. "
            f"Falls back to the {ENV_EMAIL_ADDR} environment variable."
        ),
    )
    parser.add_argument(
        "--subject", "-s",
        dest="subject",
        metavar="TEXT",
        default=None,
        help="Email subject line (auto-generated from command + exit status if omitted).",
    )
    parser.add_argument(
        "--no-mail",
        action="store_true",
        default=False,
        help="Run the command but skip sending the email (useful for testing).",
    )
    # Everything after '--' (or positional args if '--' is omitted)
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        metavar="COMMAND",
        help="The command (and its arguments) to run.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── Resolve recipient address ─────────────────────────────────────────────
    email = args.email or os.environ.get(ENV_EMAIL_ADDR)
    if not email and not args.no_mail:
        parser.error(
            f"No recipient address given. "
            f"Use --to <address> or export {ENV_EMAIL_ADDR}=<address>."
        )

    # ── Resolve command ───────────────────────────────────────────────────────
    command_parts: list[str] = args.command
    # Strip a leading '--' separator if the user wrote: notipy [opts] -- cmd
    if command_parts and command_parts[0] == "--":
        command_parts = command_parts[1:]

    if not command_parts:
        parser.error("No command provided. Example: notipy -- sleep 5")

    command_str = " ".join(command_parts)

    # ── Run ───────────────────────────────────────────────────────────────────
    print(f"[notipy] Running: {command_str}", flush=True)
    result = run_command(command_str)

    status_label = "finished successfully" if result.succeeded else f"failed (exit {result.returncode})"
    print(f"[notipy] Command {status_label}.", flush=True)

    # ── Notify ────────────────────────────────────────────────────────────────
    if not args.no_mail:
        print(f"[notipy] Sending notification to {email} …", flush=True)
        try:
            send_notification(to_addr=email, result=result, subject=args.subject)
            print("[notipy] Email sent.", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[notipy] WARNING: failed to send email: {exc}", file=sys.stderr)
    else:
        print("[notipy] --no-mail set, skipping email.", flush=True)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
