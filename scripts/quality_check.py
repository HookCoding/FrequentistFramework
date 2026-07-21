from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = ["python/repo_utils.py", "scripts/quality_check.py", "tests"]

    run_command([sys.executable, "-m", "pytest", "tests"], repo_root)
    run_command([sys.executable, "-m", "ruff", "check", *targets], repo_root)
    run_command([sys.executable, "-m", "black", "--check", *targets], repo_root)


if __name__ == "__main__":
    main()
