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
- 103 passed;
- 2 prepared-dependency tests deselected;
- 0 expected failures;
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

It does not cover physics changes, CLs, repository-wide formatting, CERN-only scientific execution, Tier-3 refactoring, or Tier-4 orchestration.

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

## Installation-policy status

The declared external dependencies have matching Git index gitlinks at their verified pinned revisions.

The destructive `rm -rf` operations have been removed from `install.sh`, and the former strict expected-failure test now passes normally.

The installer now provides:

- a verified read-only `--check` mode;
- a verified non-destructive `--build` mode;
- strict dependency, gitlink, nested RooFitExtensions, environment, output, and pyBumpHunter validation;
- configurable positive-integer parallelism through `INSTALL_JOBS`.

The prepared-checkout C++ rebuild completed successfully, reproduced all 12 protected build-artifact SHA-256 hashes, preserved tracked source cleanliness, passed runtime readiness, and passed the authoritative J100/J50 scientific gate.

The lightweight gate currently has no expected installation-policy failures. Clean-clone acquisition and building in a separate fresh checkout remain outside the completed acceptance evidence.

## CI policy

`.github/workflows/tier1-root-comparison.yml` now:

- checks out the repository;
- selects Python 3.12.13;
- installs `requirements-dev-lock.txt`;
- runs `python scripts/quality_check.py --mode full`;
- covers `harry` and `tier-2-m365`;
- excludes CERN-only scientific execution.

The hosted lightweight quality gate has been exercised successfully on GitHub Actions. CERN-only runtime readiness and scientific characterization remain separate LXPlus gates.

## Optional pre-commit configuration

`.pre-commit-config.yaml` (the third-party `pre-commit` framework) is an optional convenience only.

- The runner is not installed or pinned.
- Contributors are not required to install hooks.
- The authoritative command is `python scripts/quality_check.py --mode full`.
- The Ruff hook version differs from the pinned Tier-2 Ruff version.
- Hook behavior is not yet aligned with the authoritative lightweight quality gate.

### Mandatory git-native pre-commit gate (distinct from the above)

`.githooks/pre-commit`, installed via `bash scripts/install_git_hooks.sh`
(see README.md), is a **separate, plain git hook** — not the
`pre-commit` framework above, and it does not change the policy in this
section: it adds no dependency (`pre-commit` stays absent from both
`requirements-dev.txt` and `requirements-dev-lock.txt`, confirmed by
`tests/test_repo_utils.py::test_precommit_is_not_a_locked_development_dependency`),
requires no pinned version, and calls the same already-authoritative
commands directly:

- `python scripts/quality_check.py --mode full` (always) — the same
  lightweight gate CI runs.
- `python -m pytest tests/test_analysis_workflows_integration.py -m
  "integration and requires_root" -v` (only when
  `scripts/setup_buildAndFit.sh` succeeds here, i.e. CVMFS/ROOT is
  actually available locally — skipped with a warning otherwise, never
  blocking a commit on an environment that legitimately lacks CVMFS).

Installing it is opt-in (`bash scripts/install_git_hooks.sh`, one time
per checkout) and any single commit can still bypass it with
`git commit --no-verify` — the gate a bypassed commit ultimately has to
pass is still CI's own `python scripts/quality_check.py --mode full`,
unchanged. `tests/test_repo_utils.py::test_git_hook_pre_commit_gate_matches_authoritative_commands`
pins that the hook and its installer exist, are executable, and
reference these exact commands.

## Retired modular tier-check framework

The experimental `tier_checks/` framework has been retired and removed after a complete coverage audit.

The audit confirmed that it did not provide unique Tier-1 or Tier-2 acceptance coverage beyond the authoritative system. Several checks were weaker than, duplicated, or had fallen behind the accepted implementation:

- its targeted pytest check omitted `tests/test_run_anaFit.py`;
- its Ruff and Black target list also omitted `tests/test_run_anaFit.py`;
- its Ruff and Black checks targeted the complete checker directory rather than an explicit Python-file list;
- its workflow-input and recorded-output checks were weaker than the accepted launcher-contract, reference, runtime-readiness, and scientific integration tests;
- its reference contract was weaker than the production schema-version-2 provenance validator;
- its full-quality check called the authoritative `scripts/quality_check.py` gate directly;
- its in-depth mode duplicated pytest, Ruff, and Black execution;
- warnings and skipped checks counted as successful outcomes.

The authoritative Tier-1 and Tier-2 acceptance interfaces remain:

- `python scripts/quality_check.py --mode full`;
- the prepared-dependency pytest gate;
- the scientific runtime-readiness pytest gate;
- the authoritative J100/J50 scientific integration gate;
- `bash install.sh --check`;
- `INSTALL_JOBS=2 bash install.sh --build`.

Potential future enhancements identified during the audit include subprocess timeouts, optional provenance-backed JSON quality reports, requirement-level duration reporting, active Python identity reporting, and non-empty documentation-presence checks. These are enhancement ideas only and do not require maintaining a second acceptance framework.

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

Tier 2 is healthy when the locked environment reproduces, selected tests pass with no unexpected failures, Ruff and Black pass, the full gate exits 0, hosted CI policy remains aligned, and documentation is current.
