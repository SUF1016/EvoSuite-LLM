from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from .models import CommandResult


class CommandError(RuntimeError):
    def __init__(self, message: str, result: CommandResult | None = None) -> None:
        super().__init__(message)
        self.result = result


def require_executable(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise CommandError(
            f"Executable '{name}' was not found on PATH. Install it or set the "
            "corresponding executable path in the config."
        )
    return resolved


def run_command(
    args: list[str],
    cwd: Path,
    timeout_seconds: int = 600,
    check: bool = False,
) -> CommandResult:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            shell=False,
        )
        result = CommandResult(
            args=args,
            cwd=cwd,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_seconds=time.monotonic() - start,
        )
    except FileNotFoundError as exc:
        raise CommandError(f"Executable not found while running: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        result = CommandResult(
            args=args,
            cwd=cwd,
            returncode=124,
            stdout=stdout,
            stderr=stderr + f"\nCommand timed out after {timeout_seconds}s.",
            elapsed_seconds=time.monotonic() - start,
        )

    if check and not result.ok:
        raise CommandError(f"Command failed with exit code {result.returncode}", result)
    return result


def write_command_log(result: CommandResult, output_dir: Path, stem: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in stem)
    path = output_dir / f"{safe_stem}.json"
    path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
