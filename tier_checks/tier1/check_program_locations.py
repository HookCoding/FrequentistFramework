from __future__ import annotations
import time
from tier_checks.core.base import TierCheck
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult
from tier_checks.tier1.manifest import OPTIONAL_PATHS, REQUIRED_PATHS


class ProgramLocationsCheck(TierCheck):
    check_id = "program-locations"
    tier = 1
    requirement = "All recorded Tier 1 programs, tests, references, and documentation exist."

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        missing = [path for path in REQUIRED_PATHS if not context.path(path).exists()]
        optional_missing = [path for path in OPTIONAL_PATHS if not context.path(path).exists()]
        status = "FAIL" if missing else ("WARN" if optional_missing else "PASS")
        details = tuple(
            [
                *(f"missing required: {p}" for p in missing),
                *(f"missing optional: {p}" for p in optional_missing),
            ]
        )
        summary = (
            "all required Tier 1 paths are present"
            if not missing
            else f"{len(missing)} required path(s) missing"
        )
        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            status,
            summary,
            details,
            time.monotonic() - started,
        )


CHECK = ProgramLocationsCheck()
