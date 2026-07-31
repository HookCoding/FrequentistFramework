from __future__ import annotations
import time
from tier_checks.core.base import TierCheck
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult
from tier_checks.tier2.manifest import DEPENDENCY_FILES


class DependencyFilesCheck(TierCheck):
    check_id = "dependency-files"
    tier = 2
    requirement = "Direct and locked development dependency files exist and are non-empty."

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        failures = []
        details = []
        for relative in DEPENDENCY_FILES:
            path = context.path(relative)
            if not path.is_file():
                failures.append(f"missing: {relative}")
            elif path.stat().st_size == 0:
                failures.append(f"empty: {relative}")
            else:
                details.append(f"{relative}: {path.stat().st_size} bytes")
        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            "FAIL" if failures else "PASS",
            (
                "dependency files present"
                if not failures
                else f"{len(failures)} dependency-file issue(s)"
            ),
            tuple(details + failures),
            time.monotonic() - started,
        )


CHECK = DependencyFilesCheck()
