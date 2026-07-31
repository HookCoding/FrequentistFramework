from __future__ import annotations

import json
from collections import Counter
from typing import Iterable

from .models import CheckResult

COLORS = {"PASS": "\033[32m", "FAIL": "\033[31m", "WARN": "\033[33m", "SKIP": "\033[36m"}
RESET = "\033[0m"


def print_result(result: CheckResult, detail: str, color: bool) -> None:
    prefix = f"[{result.status}]"
    if color:
        prefix = f"{COLORS[result.status]}{prefix}{RESET}"
    print(f"{prefix} T{result.tier} {result.check_id}: {result.summary}")
    if detail == "verbose":
        print(f"    Requirement: {result.requirement}")
        print(f"    Duration: {result.duration_seconds:.3f}s")
        for line in result.details:
            print(f"    {line}")


def print_summary(results: Iterable[CheckResult]) -> None:
    results = list(results)
    counts = Counter(result.status for result in results)
    print(
        "\nSummary: "
        + ", ".join(f"{name}={counts.get(name, 0)}" for name in ("PASS", "FAIL", "WARN", "SKIP"))
    )


def write_json(results: Iterable[CheckResult], destination: str) -> None:
    payload = [result.to_dict() for result in results]
    with open(destination, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
