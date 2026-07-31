from __future__ import annotations
import importlib.util, json, sys, time
from tier_checks.core.base import TierCheck
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult
from tier_checks.tier1.reference_contract import validate


class ReferenceRegenerationCheck(TierCheck):
    check_id = "reference-regeneration"
    tier = 1
    requirement = "Current outputs regenerate the committed deterministic analysis reference."
    supported_depths = frozenset({"in-depth"})

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        details = []
        try:
            path = context.path("python/analysis_reference.py")
            spec = importlib.util.spec_from_file_location(
                "tier_checks_runtime_analysis_reference", path
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load {path}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            actual = module.build_analysis_reference(context.repo)
            expected = json.loads(
                context.path("tests/references/analysis_reference.json").read_text(encoding="utf-8")
            )
            errors = validate(actual)
            if actual != expected:
                errors.append("regenerated payload differs from frozen JSON")
        except Exception as exc:
            errors = [f"regeneration failed: {type(exc).__name__}: {exc}"]
        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            "FAIL" if errors else "PASS",
            (
                "regenerated reference matches"
                if not errors
                else f"{len(errors)} regeneration issue(s)"
            ),
            tuple(errors + details),
            time.monotonic() - started,
        )


CHECK = ReferenceRegenerationCheck()
