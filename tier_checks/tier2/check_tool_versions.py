from __future__ import annotations
from importlib import metadata
import time
from tier_checks.core.base import TierCheck
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult
from tier_checks.tier2.manifest import EXPECTED_TOOLS


class ToolVersionsCheck(TierCheck):
    check_id = "tool-versions"
    tier = 2
    requirement = "pytest, Ruff, and Black match the reproducibly pinned Tier 2 versions."

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        failures = []
        details = []
        for package, expected in EXPECTED_TOOLS.items():
            try:
                actual = metadata.version(package)
            except metadata.PackageNotFoundError:
                failures.append(f"{package}: not installed")
                continue
            details.append(f"{package}: {actual}")
            if actual != expected:
                failures.append(f"{package}: expected {expected}, found {actual}")
        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            "FAIL" if failures else "PASS",
            "tool versions match pins" if not failures else f"{len(failures)} version issue(s)",
            tuple(details + failures),
            time.monotonic() - started,
        )


CHECK = ToolVersionsCheck()
