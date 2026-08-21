# Tier-2 system: reproducible Python quality environment

Tier 2 provides the reproducible development environment and lightweight quality gate supporting the Tier-1 J100/J50 safety net.

## Current status

Verified development baseline:

- Python 3.12.13
- pytest 9.1.1
- Ruff 0.16.0
- Black 26.5.1

Latest full lightweight gate:

- 105 collected;
- 101 passed;
- 2 prepared-dependency tests deselected;
- 2 strict expected installation-policy failures;
- Ruff passed;
- Black passed;
- exit code 0.

## Scope

Tier 2 covers:

- `.venv` development environment;
- `requirements-dev.txt` and `requirements-dev-lock.txt`;
- explicit pytest targets;
- explicit Ruff and Black targets;
- fast and full quality commands;
- clean-lock reproduction;
- generated-output ownership checks;
- CI policy;
- separation of lightweight, dependency, and scientific gates.

It does not cover physics changes, CLs, repository-wide formatting, CERN-only hosted execution, Tier-3 refactoring, Tier-4 orchestration, or installer repair.

## Authoritative files

Environment:

- `pyproject.toml`
- `requirements-dev.txt`
- `requirements-dev-lock.txt`

Quality gate:

- `scripts/quality_check.py`

Approved source targets:

- `python/analysis_reference.py`
- `python/repo_utils.py`
- `scripts/compare_root_outputs.py`
- `scripts/quality_check.py`

Approved lightweight tests:

- `tests/test_analysis_reference.py`
- `tests/test_compare_root_outputs.py`
- `tests/test_repo_utils.py`
- `tests/test_run_anaFit.py`

Separate scientific integration tests:

- `tests/test_analysis_workflows_integration.py`

## Recreate the environment

```bash
CLEAN_ROOT="$(mktemp -d /tmp/frequentist-tier2-clean.XXXXXX)"
python3.12 -m venv "$CLEAN_ROOT/venv"
"$CLEAN_ROOT/venv/bin/python" -m pip install --upgrade pip
"$CLEAN_ROOT/venv/bin/python" -m pip install \
  -r requirements-dev-lock.txt
"$CLEAN_ROOT/venv/bin/python" \
  scripts/quality_check.py --mode full
```

The clean-lock checkpoint reproduced Python 3.12.13, pytest 9.1.1, Ruff 0.16.0, and Black 26.5.1. Pip itself is not pinned.

## Gate operation

Fast gate:

```bash
python scripts/quality_check.py --mode fast
```

Full gate:

```bash
python scripts/quality_check.py --mode full
```

The ordinary gate excludes tests marked `requires_analysis_dependencies` and does not include the integration test file.

Prepared dependency gate:

```bash
python -m pytest tests/test_repo_utils.py \
  -m "requires_analysis_dependencies" -v
```

Scientific gate:

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v
```

## Pytest markers

- `integration`: executes authoritative workflows
- `requires_root`: needs the configured ROOT/RooFit runtime
- `requires_analysis_dependencies`: needs prepared external checkouts

## Explicit target policy

Do not use repository-wide acceptance commands:

```bash
python -m ruff check .
python -m black --check .
```

Ruff and Black must receive explicit approved Python files. Policy tests protect this separation.

## Current lightweight coverage

The suite covers:

- strict workflow and payload schemas;
- schema-version-1 and schema-version-2 manifests;
- scientific provenance validation;
- fit and p-value tolerances;
- launcher configuration and failure propagation;
- BumpHunter safeguards;
- plot-independent acceptance;
- selected TH1 comparison behavior;
- generated-output ownership;
- CI policy;
- optional pre-commit policy;
- launcher permissions;
- installation-contract checks.

## Strict expected failures

Two strict `xfail` tests document:

1. Missing Git index gitlinks for declared external dependencies.
2. Destructive `rm -rf` operations in `install.sh`.

An unexpected pass is treated as a failure so the policy must be reviewed deliberately after repair.

## CI policy

`.github/workflows/tier1-root-comparison.yml` now:

- checks out the repository;
- selects Python 3.12.13;
- installs `requirements-dev-lock.txt`;
- runs `python scripts/quality_check.py --mode full`;
- covers `harry` and `tier-2-m365`;
- excludes CERN-only scientific execution.

The policy is tested locally. Hosted execution remains pending commit and push.

## Optional pre-commit

`.pre-commit-config.yaml` is an optional convenience only.

- The runner is not installed or pinned.
- Contributors are not required to install hooks.
- The authoritative command is `python scripts/quality_check.py --mode full`.
- The Ruff hook version differs from the pinned Tier-2 Ruff version.
- Hook behavior is not yet aligned with the read-only acceptance gate.

## Modular tier_checks framework

The separate `tier_checks/` framework is not part of Tier-2 acceptance. It remains incomplete until its explicit Ruff and Black targets, 12-check in-depth result, and `tests/test_tier_checks.py` are verified.

## Troubleshooting

Activate the development environment before running Tier-2 checks:

```bash
source .venv/bin/activate
python --version
```

If full mode fails, verify:

```bash
python -m ruff --version
python -m black --version
```

The scientific setup may switch Python to 3.9.12. Reactivate `.venv` before returning to Tier-2 work.

## Change control

```bash
git status -sb
git diff --check
git status --short
git diff --stat
```

Stage explicit paths only. Append every substantial change to `doc/ACTIVITY_LOG.md`.

## Completion definition

Tier 2 is healthy when the locked environment reproduces, selected tests pass, expected installation-policy failures remain expected, Ruff and Black pass, the full gate exits 0, CI policy remains aligned, and documentation is current.
