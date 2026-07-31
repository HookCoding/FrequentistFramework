from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence


def run_command(command: Sequence[str], cwd: Path, timeout: int) -> tuple[int, str]:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def output_tail(output: str, lines: int = 25) -> tuple[str, ...]:
    return tuple(output.splitlines()[-lines:])
