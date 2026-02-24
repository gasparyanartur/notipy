"""notipy CLI entrypoint."""

from __future__ import annotations

import os
import shlex
import sys
import argparse

from notipy.runner import run_command
from notipy.notifier import send_notification, DEFAULT_ADDR, ENV_ADDR
from notipy import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notipy",
        description=(
            "Run a command and receive an ntfy.sh push notification when it finishes.\n\n"
            "Use -- to separate notipy options from the command:\n"
            "  notipy -- python train.py --epochs 100"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--addr", "-a",
        dest="addr",
        metavar="ADDR",
        default=None,
        help=(
            f"Address suffix for the ntfy.sh topic 'notipy-<addr>'. "
            f"Falls back to {ENV_ADDR} env var, then '{DEFAULT_ADDR}'."
        ),
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        default=False,
        help="Run the command but skip sending the notification (useful for testing).",
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

    # ── Resolve address ───────────────────────────────────────────────────────
    addr = args.addr or os.environ.get(ENV_ADDR) or DEFAULT_ADDR
    topic = f"notipy-{addr}"

    # ── Resolve command ───────────────────────────────────────────────────────
    command_parts: list[str] = args.command
    # Strip a leading '--' separator if the user wrote: notipy [opts] -- cmd
    if command_parts and command_parts[0] == "--":
        command_parts = command_parts[1:]

    if not command_parts:
        parser.error("No command provided. Example: notipy -- sleep 5")

    command_str = shlex.join(command_parts)

    # ── Run ───────────────────────────────────────────────────────────────────
    print(f"[notipy] Running: {command_str}", flush=True)
    result = run_command(command_str)

    status_label = "finished successfully" if result.succeeded else f"failed (exit {result.returncode})"
    print(f"[notipy] Command {status_label}.", flush=True)

    # ── Notify ────────────────────────────────────────────────────────────────
    if not args.no_notify:
        print(f"[notipy] Sending notification to ntfy.sh/{topic} …", flush=True)
        try:
            send_notification(result=result, addr=addr)
            print("[notipy] Notification sent.", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[notipy] WARNING: failed to send notification: {exc}", file=sys.stderr)
    else:
        print("[notipy] --no-notify set, skipping notification.", flush=True)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
