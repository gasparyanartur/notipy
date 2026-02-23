"""Run a shell command, stream its output to the terminal, and capture it."""

from __future__ import annotations

import subprocess
import sys
import threading
from dataclasses import dataclass, field


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    command: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0

    def combined_log(self) -> str:
        """Return a single string suitable for the logs.txt attachment."""
        parts: list[str] = [f"$ {self.command}\n"]
        if self.stdout:
            parts.append("=== STDOUT ===\n")
            parts.append(self.stdout)
            if not self.stdout.endswith("\n"):
                parts.append("\n")
        if self.stderr:
            parts.append("\n=== STDERR ===\n")
            parts.append(self.stderr)
            if not self.stderr.endswith("\n"):
                parts.append("\n")
        parts.append(f"\n=== EXIT CODE: {self.returncode} ===\n")
        return "".join(parts)


def run_command(command: str) -> RunResult:
    """Run *command* in a shell, tee-ing output to the terminal while capturing it.

    stdout is forwarded to sys.stdout and stderr to sys.stderr so the user sees
    live output, while both streams are also accumulated for the email attachment.
    """
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

    return RunResult(
        returncode=process.returncode,
        stdout="".join(stdout_chunks),
        stderr="".join(stderr_chunks),
        command=command,
    )
