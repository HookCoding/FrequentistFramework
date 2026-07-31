#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tier_checks.core.context import CheckContext
from tier_checks.core.discovery import discover_checks
from tier_checks.core.models import CheckResult
from tier_checks.core.reporting import print_result, print_summary, write_json


def parse_tiers(values: list[str]) -> set[int]:
    tiers = set()
    for value in values:
        if value == "all":
            tiers.update({1, 2})
        else:
            tiers.add(int(value))
    return tiers or {1, 2}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Auto-discover and run modular FrequentistFramework tier checks."
    )
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="FrequentistFramework repository root"
    )
    parser.add_argument(
        "--tier",
        action="append",
        choices=("1", "2", "all"),
        default=[],
        help="tier to check; repeatable",
    )
    parser.add_argument(
        "--depth",
        choices=("fast", "in-depth"),
        default="fast",
        help="fast static checks or in-depth behavioral checks",
    )
    parser.add_argument(
        "--detail", choices=("summary", "verbose"), default="summary", help="console output detail"
    )
    parser.add_argument("--timeout", type=int, default=300, help="per-check subprocess timeout")
    parser.add_argument("--json-out", help="optional path for a full machine-readable report")
    parser.add_argument(
        "--list", action="store_true", help="list detected checks without running them"
    )
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    tiers = parse_tiers(args.tier)
    package_root = Path(__file__).resolve().parent
    try:
        checks = discover_checks(package_root, tiers)
    except Exception as exc:
        print(f"[FAIL] check discovery: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for check in checks:
            depths = ", ".join(sorted(check.supported_depths))
            print(f"T{check.tier} {check.check_id} [{depths}] - {check.requirement}")
        return 0

    context = CheckContext(repo=repo, depth=args.depth, timeout=args.timeout)
    results: list[CheckResult] = []
    for check in checks:
        if args.depth not in check.supported_depths:
            result = CheckResult(
                check.check_id,
                check.tier,
                check.requirement,
                "SKIP",
                f"not part of {args.depth} depth",
            )
        else:
            try:
                result = check.run(context)
            except Exception as exc:
                result = CheckResult(
                    check.check_id,
                    check.tier,
                    check.requirement,
                    "FAIL",
                    "unhandled check error",
                    (f"{type(exc).__name__}: {exc}",),
                )
        results.append(result)
        print_result(result, args.detail, not args.no_color)

    print_summary(results)
    if args.json_out:
        write_json(results, args.json_out)
    return 0 if all(result.successful for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
