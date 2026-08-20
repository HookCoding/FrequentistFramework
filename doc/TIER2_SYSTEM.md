## Tier-2 system: reproducible Python quality environment

This document is the user-facing operating guide for the Tier-2 quality system in this repository. Tier 2 builds on the Tier-1 J100/J50 safety net by providing a supported Python environment, pinned development tooling, formatting and lint checks, and a reproducible full quality gate.

### 1) Purpose, audience, and status

#### Purpose

Tier 2 provides a consistent development and verification environment for the Tier-1 Python source and regression tests. It is intended to make cleanup and future refactoring safer without changing the authoritative physics workflow.

#### Intended audience

- Developers changing the Tier-1 Python source, tests, or quality-gate scripts.
- Reviewers checking that changes pass pytest, Ruff, and Black.
- Users recreating the supported development environment from the dependency lock.

#### Current status

The established Tier-2 quality system is complete and passing.

Current verified baseline:

- Python: 3.12.13
- Project requirement: Python 3.11 or newer
- pytest: 9.1.1
- Ruff: 0.16.0
- Black: 26.5.1
- Targeted tests: 18 passed
- Ruff: passed
- Black: passed
- Full quality-gate exit code: 0

The separate modular `tier_checks/` framework is operational but is not yet part of the completed Tier-2 acceptance baseline. Its final in-depth verification remains outstanding.

### 2) Scope and non-goals

#### In scope

- A repository-local Python virtual environment.
- Direct and locked development dependency records.
- The explicit Tier-1 pytest target set.
- Ruff lint verification for the approved Python targets.
- Black format verification for the approved Python targets.
- Fast and full modes in `scripts/quality_check.py`.
- Reproducible recreation of the development environment from `requirements-dev-lock.txt`.

#### Out of scope

- Changes to the J100/J50 physics workflows.
- CLs extraction or validation.
- Broad formatting or linting of unrelated legacy source files.
- Repository-wide Ruff or Black commands against `.`.
- Tier-3 structural refactoring.
- Tier-4 workflow orchestration.
- A policy decision for generated `post_fit.pdf` files.

### 3) Authoritative files

#### Environment and dependencies

- `pyproject.toml`
- `requirements-dev.txt`
- `requirements-dev-lock.txt`
- `.venv/` as the local environment location; the directory is not version-controlled.

#### Quality gate

- `scripts/quality_check.py`

#### Approved source targets

- `python/analysis_reference.py`
- `python/repo_utils.py`
- `scripts/compare_root_outputs.py`
- `scripts/quality_check.py`

#### Approved test targets

- `tests/test_analysis_reference.py`
- `tests/test_compare_root_outputs.py`
- `tests/test_repo_utils.py`

#### Documentation and provenance

- `doc/TIER1_SYSTEM.md`
- `doc/TIER1_ENVIRONMENT_PROVENANCE.md`
- `doc/TIER2_SYSTEM.md`
- `doc/ACTIVITY_LOG.md`

### 4) Supported environment

Activate the repository-local environment from the repository root:

```bash
source .venv/bin/activate
```

Verify the active toolchain:

```bash
command -v python
python --version
python -m pytest --version
python -m ruff --version
python -m black --version
```

Expected baseline:

```text
Python 3.12.13
pytest 9.1.1
ruff 0.16.0
black 26.5.1
```

The supported project interpreter must satisfy the Python requirement declared in `pyproject.toml`.

### 5) Dependency records and clean reproduction

`requirements-dev.txt` records the direct development dependencies. `requirements-dev-lock.txt` records the exact reproducible dependency set.

Create a clean Python 3.12 environment outside the repository:

```bash
CLEAN_VENV="$(mktemp -d)/tier2-clean-venv"
python3.12 -m venv "$CLEAN_VENV"
source "$CLEAN_VENV/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements-dev-lock.txt
```

Verify the recreated environment:

```bash
python --version
python -m pytest --version
python -m ruff --version
python -m black --version
python scripts/quality_check.py --mode full
```

Acceptance requires the full quality gate to exit with code 0.

### 6) Quality-gate operation

#### Fast mode

```bash
python scripts/quality_check.py --mode fast
```

Fast mode performs the Tier-1 baseline path checks, optional workflow hints, pytest availability check, and targeted regression tests.

#### Full mode

```bash
python scripts/quality_check.py --mode full
```

Full mode performs all fast-mode checks and then runs Ruff and Black against the explicit approved targets.

Current verified result:

```text
18 tests passed
Ruff passed
Black passed
Full quality-gate exit code: 0
```

#### Run the targeted tests directly

```bash
python -m pytest \
  tests/test_analysis_reference.py \
  tests/test_compare_root_outputs.py \
  tests/test_repo_utils.py \
  -q
```

#### Check only the analysis-reference implementation and tests

```bash
python -m ruff check \
  python/analysis_reference.py \
  tests/test_analysis_reference.py

python -m black --check \
  python/analysis_reference.py \
  tests/test_analysis_reference.py

python -m pytest tests/test_analysis_reference.py -q
```

The analysis-reference test file currently contains eight tests, including five regression tests for strict workflow/schema validation and robust optional `BHresults.json` handling.

### 7) Target policy

Ruff and Black must receive an explicit list of approved Python files. Do not run the Tier-2 acceptance checks using:

```bash
python -m ruff check .
python -m black --check .
```

Repository-wide commands can inspect unrelated legacy Python files, Markdown, binary ROOT files, generated outputs, and other content outside the established Tier-2 scope.

When new Tier-2 Python files are intentionally added, update the explicit target list in the quality gate and its tests as part of the same reviewed change.

### 8) Tier-1 validation carried by Tier 2

Tier 2 preserves and verifies the Tier-1 analysis-reference contract:

- Only the `J100` and `J50` top-level workflows are accepted.
- Missing or unexpected top-level workflows are rejected.
- Each workflow payload must contain exactly `fit_parameters`, `p_chi2`, `p_bh`, and `cls_limit_points`.
- Missing or unexpected workflow payload keys are rejected.
- Optional `BHresults.json` files may be absent.
- Malformed, unreadable, or non-object BH JSON produces a clear `ValueError`.
- `cls_limit_points` remains an empty list until CLs integration is implemented.

### 9) Modular `tier_checks/` framework

The modular checker framework is separate from the established Tier-2 quality-gate baseline.

Previously demonstrated capabilities include:

- discovery of 12 checks;
- six Tier-1 checks and six Tier-2 checks;
- fast-mode operation with in-depth-only checks skipped;
- successful Tier-1 checks;
- successful environment, dependency, tool-version, and established quality-gate checks.

The framework must not be marked complete until all of the following are verified:

- Ruff and Black wrappers use only explicit Python targets.
- Neither wrapper receives `.` or a complete directory containing non-Python files.
- All checker Python files compile.
- All 12 checks remain discoverable.
- The Tier-2 in-depth suite passes.
- The complete Tier-1 and Tier-2 in-depth suite reports 12 passed, 0 failed, 0 warnings, and 0 skipped.
- `tests/test_tier_checks.py` is present and its framework-specific tests pass.
- Temporary reports, copied archives, and generated outputs remain outside the commit.

Until those criteria are met, `scripts/quality_check.py --mode full` remains the authoritative Tier-2 acceptance gate.

### 10) Troubleshooting

#### The active Python is too old

Symptom:

```text
Python 3.9.x
```

Action:

```bash
source .venv/bin/activate
python --version
```

The project requires Python 3.11 or newer, and the verified environment uses Python 3.12.13.

#### `python` is not found

Activate the repository-local environment:

```bash
source .venv/bin/activate
```

If activation is unavailable, use the environment executable explicitly:

```bash
.venv/bin/python --version
```

#### CRLF or `^M` whitespace failures

Files copied from Windows may contain CRLF line endings. Convert only the affected text files:

```bash
sed -i 's/\r$//' path/to/file.py
```

Then verify:

```bash
git diff --check
```

#### Fast mode passes but full mode fails

Check that Ruff and Black are installed in the same active interpreter:

```bash
python -m ruff --version
python -m black --version
```

If necessary, recreate the environment from `requirements-dev-lock.txt`.

#### Repository-wide Ruff or Black failures

Confirm that the command uses the explicit approved file list rather than `.`. Findings outside the approved target set do not automatically indicate failure of the established Tier-2 gate.

### 11) Branch and change-control procedure

Before substantial work:

```bash
git status -sb
git branch -vv
```

Before staging:

```bash
git diff --check
git status --short
git diff --stat
```

Stage explicit files only. Avoid broad commands such as `git add .` and `git commit -a` when unrelated generated outputs or experimental files exist in the working tree.

Every substantial Tier-2 repository or workflow change must be appended to `doc/ACTIVITY_LOG.md` as a new dated, titled section describing:

- the objective;
- the files and behaviour changed;
- verification performed;
- remaining work and scope boundaries.

### 12) Completion definition

The established Tier-2 system is healthy when:

- a supported Python 3.11-or-newer environment is active;
- the verified pinned tool versions are available;
- `requirements-dev-lock.txt` recreates a working clean environment;
- the targeted tests pass;
- Ruff passes against the approved targets;
- Black passes against the approved targets;
- `python scripts/quality_check.py --mode full` exits with code 0;
- environment provenance and the activity log are current;
- unrelated generated files remain outside the change set.

The latest verified project-environment result is 18 tests passed, Ruff passed, Black passed, and full quality-gate exit code 0.
