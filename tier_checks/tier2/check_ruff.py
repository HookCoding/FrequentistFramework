from __future__ import annotations

import sys
import time

from tier_checks.core.base import TierCheck
from tier_checks.core.command import output_tail, run_command
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult
from tier_checks.tier2.manifest import QUALITY_TARGETS


class RuffCheck(TierCheck):
    check_id = "ruff"
    tier = 2
    requirement = "Ruff passes on the authoritative Tier 2 targets and modular checker."
    supported_depths = frozenset({"in-depth"})

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        command = [
            sys.executable,
            "-m",
            "ruff",
            "check",
            *QUALITY_TARGETS,
        ]

        try:
            code, output = run_command(
                command,
                context.repo,
                context.timeout,
            )
            details = output_tail(output)
        except Exception as exc:
            code = 1
            details = (f"execution failed: {type(exc).__name__}: {exc}",)

        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            "PASS" if code == 0 else "FAIL",
            "Ruff passed" if code == 0 else f"Ruff exited {code}",
            details,
            time.monotonic() - started,
        )


CHECK = RuffCheck()
