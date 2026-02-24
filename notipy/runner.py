"""Run a shell command, stream its output to the terminal, and capture it."""

from __future__ import annotations

import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    command: str
    started_at: datetime
    finished_at: datetime

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0

    @property
    def duration(self) -> float:
        """Elapsed seconds."""
        return (self.finished_at - self.started_at).total_seconds()

    def combined_log(self) -> str:
        """Return a formatted log string for the notification body."""
        def _fmt(dt: datetime) -> str:
            return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

        duration_str = f"{self.duration:.1f}s"

        lines: list[str] = [
            f"$ {self.command}",
            "",
            "── Timing ───────────────────────────────────",
            f"  Started:  {_fmt(self.started_at)}",
            f"  Finished: {_fmt(self.finished_at)}",
            f"  Duration: {duration_str}",
            "",
        ]

        if self.stdout:
            lines.append("── STDOUT ───────────────────────────────────")
            lines.append("")
            lines.append(self.stdout.rstrip("\n"))
            lines.append("")

        if self.stderr:
            lines.append("── STDERR ───────────────────────────────────")
            lines.append("")
            lines.append(self.stderr.rstrip("\n"))
            lines.append("")

        status = "OK" if self.succeeded else f"FAILED"
        lines.append("── Exit ─────────────────────────────────────")
        lines.append(f"  Code:   {self.returncode}  ({status})")
        lines.append("")

        return "\n".join(lines)


def run_command(command: str) -> RunResult:
    """Run *command* in a shell, tee-ing output to the terminal while capturing it.

    stdout is forwarded to sys.stdout and stderr to sys.stderr so the user sees
    live output, while both streams are also accumulated for the notification body.
    """
    started_at = datetime.now(tz=timezone.utc)

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line-buffered
    )

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def _drain(pipe, chunks: list[str], dest) -> None:
        for line in pipe:
            dest.write(line)
            dest.flush()
            chunks.append(line)

    t_out = threading.Thread(
        target=_drain, args=(process.stdout, stdout_chunks, sys.stdout), daemon=True
    )
    t_err = threading.Thread(
        target=_drain, args=(process.stderr, stderr_chunks, sys.stderr), daemon=True
    )
    t_out.start()
    t_err.start()
    t_out.join()
    t_err.join()
    process.wait()

    finished_at = datetime.now(tz=timezone.utc)

    return RunResult(
        returncode=process.returncode,
        stdout="".join(stdout_chunks),
        stderr="".join(stderr_chunks),
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
