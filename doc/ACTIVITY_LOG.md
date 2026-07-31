# Activity Log

This file is a human-readable record of substantial repository changes.

---

## 2026-07-28 — Tier-1 baseline hardening (J100/J50 Run-2 workflow)

### Objective
Make the repository more workable first (Tier 1), using the authoritative Run-2 workflow:

- `scripts/run_anaFit_J100.sh`
- `scripts/run_anaFit_J50.sh`

### Substantial changes completed

1. **Baseline workflow/repo audit completed**
   - Confirmed the authoritative scripts are present and tracked.
   - Confirmed required Run-2 input ROOT files exist:
     - `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root`
     - `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root`
   - Confirmed reference artifacts are present under `tests/references/`.

2. **`scripts/quality_check.py` strengthened with Tier-1 baseline checks**
   - Added required path validation for critical workflow files and reference artifacts.
   - Added optional workflow hint checks (non-fatal) for setup helpers.
   - Added explicit Python tool availability checks for:
     - `pytest`
     - `ruff`
     - `black`
   - Improved failure mode to be actionable (clear install guidance), rather than failing with opaque import/runtime errors.

3. **`doc/TIER1_SYSTEM.md` rewritten to match authoritative workflow**
   - Updated documentation focus from legacy/general flow to J100/J50 Run-2 execution.
   - Added Tier-1 baseline checklist aligned with `quality_check.py`.
   - Clarified scope boundaries and current known limitation:
     - `python/analysis_reference.py` still contains legacy fallback directory discovery (`run_135_1000_*`) and has not yet been fully migrated to prefer J100/J50 outputs first.

### Verification performed

- `python3 -m py_compile scripts/quality_check.py`
  - Result: **success** (`syntax_ok`)
- `python3 -m pytest tests/test_analysis_reference.py tests/test_compare_root_outputs.py tests/test_repo_utils.py -q`
  - Result: **12 passed**
- `python3 scripts/quality_check.py`
  - Result: expected environment failure message indicating missing `ruff` and `black` with install guidance.

### Current status / remaining Tier-1 items

- Pending: add environment pinning artifact (`requirements.txt` or `environment.yml`).
- Pending: migrate/extend `python/analysis_reference.py` to prioritize J100/J50 outputs.
- Pending: refresh frozen references/tests if migration changes output discovery.
- Pending: rerun full quality gate once lint/format tools are available in the active environment.

### Process note

From this point onward, each substantial activity will append a new dated section to this file summarizing:

- what changed,
- why it changed,
- how it was verified,
- and what remains.

---

## 2026-07-28 — Tier-1 completion planning + scope lock (background-only first)

### Objective
Capture the substantial Tier-1 planning and verification work completed after baseline hardening, while keeping the repo-workable-first constraint and authoritative Run-2 J100/J50 workflow fixed.

### Substantial changes completed

1. **Tier-1 completion scope was clarified and locked with the user**
   - Confirmed execution priority remains strict Tier order: Tier 1 -> Tier 4.
   - Confirmed authoritative workflow remains:
     - `scripts/run_anaFit_J100.sh`
     - `scripts/run_anaFit_J50.sh`
   - Confirmed delivery scope decision for current Tier-1 completion work:
     - **Background-only J100/J50 first**
     - **CLs workflow as a later Tier-1 extension**

2. **Repository/runtime evidence gathering for Tier-1 migration was completed**
   - Reviewed `python/analysis_reference.py` and confirmed legacy fallback discovery still targets `run/fits/...run_135_1000_(six|seven)Par` patterns.
   - Reviewed `tests/test_analysis_reference.py` and confirmed existing fixtures/assertions are still centered on legacy sixPar paths.
   - Inspected existing Run-2 outputs under:
     - `run/fits/J100/run_481_3000_sixPar/...`
     - `run/fits/J50/run_344_2079_sixPar/...`
   - Read J100 background-only quickFit log to establish current numerical/convergence behavior context before tightening regression criteria.

3. **Tier-1 implementation/testing plan prepared for next execution phase**
   - Planned migration of golden-master discovery and tests toward deterministic J100/J50-first behavior.
   - Planned preservation of tolerance-aware comparisons to protect against benign fit-level numeric jitter.
   - Planned separation of fast checks vs heavier/full checks as part of Tier-1 gate maturation.

### Verification performed

- Verified current activity log coverage by re-reading `doc/ACTIVITY_LOG.md` before appending this entry.
- Verified the planning basis against current repository files and existing run artifacts (no contradictory evidence found).

### Current status / remaining Tier-1 items

- Pending: add environment pinning artifact (`requirements.txt` or `environment.yml`).
- Pending: migrate `python/analysis_reference.py` to deterministic J100/J50-first discovery for background-only outputs.
- Pending: update tests/references to match J100/J50-first behavior.
- Pending: formalize tolerance checks where needed for stable regression assertions.
- Pending: complete fast-vs-full Tier-1 gate split and document usage.

### Process note

- User instruction reaffirmed and adopted as an ongoing rule:
  - "please be sure to add all changes to the acvitvity log"
- Going forward, every substantial repository or workflow change will be appended here as a new dated section.

---

## 2026-07-29 — Activity-log correction: explicit titled section added

### Objective
Correct the missing titled entry for the latest work record and keep this log compliant with the rule to append substantial changes as dated sections.

### Substantial changes completed

1. **Confirmed missing titled update section**
   - Re-read `doc/ACTIVITY_LOG.md` and verified no new dated section existed beyond the two 2026-07-28 entries.

2. **Added an explicit titled dated section**
   - Appended this 2026-07-29 section so the most recent correction is clearly identifiable by title and date.

### Verification performed

- Re-read `doc/ACTIVITY_LOG.md` after editing and confirmed this header is present:
  - `## 2026-07-29 — Activity-log correction: explicit titled section added`

### Current status / remaining Tier-1 items

- Pending: complete and verify the actual Tier-1 implementation deliverables (tests, environment pinning, quality-gate evolution) with concrete command outputs and file diffs.
- Pending: continue appending each substantial change as a new dated section in this log.

---

## 2026-07-29 — Tier-1 completion: provenance artifact + fast/full gate verification

### Objective
Complete the remaining Tier-1 implementation items for the authoritative J100/J50 Run-2 baseline by:

- recording environment provenance/pinning evidence,
- aligning Tier-1 system documentation with implemented behavior,
- executing and recording verification commands,
- preserving background-only-first scope with CLs deferred.

### Substantial changes completed

1. **Environment provenance/pinning artifact added**
   - Added `doc/TIER1_ENVIRONMENT_PROVENANCE.md`.
   - Recorded runtime and tooling evidence captured from bounded probes:
     - `python_executable = /usr/bin/python3`
     - `python_version = 3.9.25`
     - `pyproject requires-python = >=3.11`
     - `pytest = 8.4.2`, `ruff = missing`, `black = missing`
     - `root-config --version = 6.40.02`
     - `ROOT` module discoverability present
     - prior bounded PyROOT probe evidence: RooFit available
   - Recorded authoritative path checks for J100/J50 background-only logs and optional `BHresults.json` absence.

2. **Tier-1 system documentation updated to current implementation**
   - Updated `doc/TIER1_SYSTEM.md` to reflect real quality-gate usage:
     - `python3 scripts/quality_check.py --mode fast`
     - `python3 scripts/quality_check.py --mode full`
   - Documented explicit fast/full semantics and their dependency checks.
   - Updated `python/analysis_reference.py` description to current deterministic J100/J50 background-only behavior.
   - Linked `doc/TIER1_ENVIRONMENT_PROVENANCE.md` from the system document.
   - Kept scope boundary explicit: CLs remains a follow-up extension.

3. **Tier-1 verification command sequence executed and captured**
   - `python3 -m py_compile scripts/quality_check.py`
     - Result: success (`__RC_PYCOMPILE__=0`)
   - `python3 -m pytest tests/test_analysis_reference.py tests/test_compare_root_outputs.py tests/test_repo_utils.py -q`
     - Result: success (`13 passed`, `__RC_PYTEST__=0`)
   - `python3 scripts/quality_check.py --mode fast`
     - Result: success (`13 passed`, `__RC_FAST__=0`)
   - `python3 scripts/quality_check.py --mode full`
     - Result: expected actionable tooling failure (`__RC_FULL__=2`) due to missing `ruff`/`black`, with install guidance emitted by the script.

### Troubleshooting/process notes

- Direct PyROOT import probes intermittently exceeded command timeout bounds in this environment.
- To avoid blocking Tier-1 completion, provenance evidence was gathered through bounded checks (`root-config`, module discoverability, prior successful bounded probe results) and documented transparently.

### Current status / remaining Tier-1 items

- Tier-1 documentation/provenance and gate verification are now recorded.
- Remaining operational environment gap: active interpreter/runtime tooling still does not satisfy full lint/format stack (`ruff`, `black`) and is below declared Python baseline (`>=3.11`).
- CLs integration remains intentionally deferred per background-only-first scope.

---

## 2026-07-29 — Tier-1 system documentation expansion implemented

### Objective
Implement the planned expansion of `doc/TIER1_SYSTEM.md` so Tier-1 users have a complete, implementation-aligned operating guide for the authoritative J100/J50 Run-2 baseline.

### Substantial changes completed

1. **Expanded Tier-1 system guide to cover end-to-end user operations**
   - Reworked `doc/TIER1_SYSTEM.md` into a structured guide with:
     - purpose/audience/status,
     - Tier-1 goals and success criteria,
     - authoritative workflow/data surface,
     - Tier-1 repository map,
     - explicit quality-gate behavior (`--mode fast|full`, required paths, optional hints, exit semantics),
     - analysis-reference contract and schema expectations,
     - operating procedures, troubleshooting, reproducibility, and scope boundaries.

2. **Aligned documentation to source-of-truth implementation details**
   - Verified alignment to:
     - `scripts/quality_check.py` for required paths, optional hint paths, mode behavior, and tooling checks.
     - `python/analysis_reference.py` for workflow fit directories, log-selection behavior, supported fit-parameter names, and required payload keys.
     - `tests/references/analysis_reference.json` for current frozen baseline semantics (`J100`/`J50`, `cls_limit_points: []`, `p_bh: null`, `p_chi2: null`).

### Verification performed

- Consistency probe command (Python import/readback of Tier-1 constants + frozen reference keys)
  - Result: documentation-critical values matched implementation/reference data.
- `python3 -m pytest tests/test_analysis_reference.py tests/test_compare_root_outputs.py tests/test_repo_utils.py -q`
  - Result: **13 passed**.
- `grep -nE '[[:blank:]]+$' doc/TIER1_SYSTEM.md`
  - Result: no trailing whitespace (`__TRAILING_WS__=none`).

### Current status / remaining Tier-1 items

- Tier-1 system documentation expansion is complete and verified against current code/reference behavior.
- Remaining environment gap is unchanged: active runtime still lacks `ruff`/`black` and is below declared Python baseline (`>=3.11`) for full-mode parity.
- CLs integration remains intentionally deferred per background-only-first scope.

## 2026-07-30 — Tier-2 Python quality tooling and formatting baseline

### Objective

Establish a supported, reproducible project-local Python environment and enable
the complete pytest, Ruff, and Black quality-gate workflow.

### Substantial changes completed

- Recreated the repository-local virtual environment using Python 3.12.13.
- Installed pytest, Ruff, and Black into the same active interpreter environment.
- Added explicit development dependency records:
  - `requirements-dev.txt`
  - `requirements-dev-lock.txt`
- Added Git ignore exceptions so the development dependency records are
  intentionally version-controlled despite the repository-wide `*.txt` rule.
- Applied Ruff's safe automatic fixes to the explicit Tier-1 source and test targets.
- Applied Black formatting to the explicit Tier-1 source and test targets.
- Preserved unrelated working-tree content outside the Tier-2 staged changes.

### Environment evidence

- Python: `Python 3.12.13`
- Python executable: `/afs/cern.ch/user/h/hhook/FrequentistFramework/.venv/bin/python`
- pytest: `pytest 9.1.1`
- Ruff: `ruff 0.16.0`
- Black: `python -m black, 26.5.1 (compiled: yes)`

### Verification performed

- Command:
  `python scripts/quality_check.py --mode full`
- Full quality-gate status: **success**
- Full quality-gate exit code: **0**
- Complete command output captured temporarily at:
  `/tmp/frequentist_framework_tier2_full_gate.log`

### Current status / remaining items

- Verify that the development environment can be recreated from requirements-dev-lock.txt.
- Continue recording substantial Tier-2 changes as new dated sections.

### 2026-07-30 — Tier-2 completion status and remaining work

#### Objective

Consolidate the Tier-2 environment, dependency, formatting, verification, and Git-integration work completed to date, and define the remaining acceptance criteria required before Tier 2 can be marked complete.

#### Significant work completed

- Established a repository-local virtual environment using Python 3.12.13, satisfying the declared Python 3.11-or-newer project requirement.
- Installed the quality-tooling stack into the same active environment:
  - pytest 9.1.1
  - Ruff 0.16.0
  - Black 26.5.1
- Added version-controlled development dependency records:
  - `requirements-dev.txt`
  - `requirements-dev-lock.txt`
- Added `.gitignore` exceptions for the dependency records because the repository otherwise ignores files matching `*.txt`.
- Applied Ruff's safe fixes for import ordering and missing final newlines.
- Applied Black formatting to the explicit Tier-1 source and test targets.
- Resolved all previously reported Ruff diagnostics without an intended behavioural change.
- Verified that all 13 targeted Tier-1 regression tests pass.
- Verified that Ruff and Black checks pass over the configured targets.
- Verified that the complete quality gate exits with code 0 on LXPlus.
- Preserved unrelated working-tree content by using explicit Git paths.
- Kept generated `post_fit.pdf` outputs outside the current Tier-2 scope.

#### Verified environment

- Python: `Python 3.12.13`
- Python executable: `/afs/cern.ch/user/h/hhook/FrequentistFramework/.venv/bin/python`
- pytest: `pytest 9.1.1`
- Ruff: `ruff 0.16.0`
- Black: `python -m black, 26.5.1 (compiled: yes)`

#### Verification evidence

The complete quality gate was run with:

```bash
python scripts/quality_check.py --mode full
```

Results:

- Targeted tests: **13 passed**
- Ruff: **passed**
- Black check: **passed**
- Full quality-gate exit code: **0**

#### Remaining work required to complete Tier 2

1. **Update environment provenance**
   - Update `doc/TIER1_ENVIRONMENT_PROVENANCE.md` with the verified Python 3.12.13 project environment.
   - Record pytest 9.1.1, Ruff 0.16.0, and Black 26.5.1.
   - Preserve the previous Python 3.9.25 snapshot as historical evidence rather than describing it as the active project environment.

2. **Verify clean dependency-lock reproduction**
   - Create a fresh Python 3.12 virtual environment.
   - Install dependencies from `requirements-dev-lock.txt`.
   - Verify the installed Python, pytest, Ruff, and Black versions.
   - Run the complete quality gate in the clean environment.
   - Require a full-gate exit code of 0.

3. **Configure branch upstream tracking**
   - Fetch the remote branch list.
   - Determine whether `origin/tier-2-m365` exists.
   - If it exists, configure it as the upstream branch.
   - If it does not exist, publish the local branch with `git push -u origin tier-2-m365`.

4. **Synchronise the branch**
   - Pull remote changes using an explicit strategy such as `git pull --rebase`.
   - Confirm that all Tier-2 commits remain present after synchronisation.

5. **Perform final verification**
   - Activate the intended project virtual environment.
   - Run the complete quality gate again.
   - Record the final command output and exit code.

6. **Record final completion evidence**
   - Append a new dated activity-log section containing the clean-environment reproduction result, provenance update, branch status, and final gate result.
   - Mark Tier 2 complete only after both the clean reproduction environment and final project environment return full-gate exit code 0.

#### Deferred generated-output decision

The following generated files are not required for the current Tier-2 work:

- `run/fits/J100/run_481_3000_sixPar/post_fit.pdf`
- `run/fits/J50/run_344_2079_sixPar/post_fit.pdf`

Whether these files should remain tracked, be removed from tracking, or be ignored will be handled separately. Until then, avoid repository-wide staging commands such as `git add .` and `git commit -a`.

#### Tier-2 completion criteria

Tier 2 will be complete when:

- Python 3.11 or newer is active and documented;
- pytest, Ruff, and Black are reproducibly pinned;
- `requirements-dev-lock.txt` recreates a working clean environment;
- all 13 targeted tests pass;
- Ruff passes;
- Black check passes;
- the complete quality gate exits with code 0;
- `doc/TIER1_ENVIRONMENT_PROVENANCE.md` reflects the verified environment;
- `tier-2-m365` tracks the intended remote branch;
- final verification evidence is recorded in this activity log;
- unrelated generated outputs remain outside the Tier-2 change history.


### 2026-07-31 — Tier-2 completion: reproducible Python quality environment

#### Objective

Complete Tier 2 by proving clean dependency-lock reproduction, updating
environment provenance, configuring branch tracking, and verifying the
complete quality gate in both the clean reproduction environment and the
intended project environment.

#### Substantial changes completed

- Recreated a fresh Python 3.12 virtual environment outside the repository.
- Installed the development dependencies from `requirements-dev-lock.txt`.
- Verified that the locked dependencies reproduce the intended pytest,
Ruff, and Black toolchain.
- Configured `tier-2-m365` to track `origin/tier-2-m365`.
- Added a branch-specific `origin` fetch refspec for `tier-2-m365`.
- Verified that the local and remote branch tips were identical.
- Updated `doc/TIER1_ENVIRONMENT_PROVENANCE.md` with the current supported
environment and clean-reproduction evidence.
- Preserved the Python 3.9.25 environment as a historical pre-Tier-2
snapshot.
- Kept unrelated generated outputs outside the Tier-2 change set.

#### Clean-environment verification

- Verification timestamp: 2026-07-30T16:07:19+02:00
- Python executable:
`/tmp/hhook/tmp.2Vv9EivLbA/tier2-clean-venv/bin/python`
- Python: 3.12.13
- pytest: 9.1.1
- Ruff: 0.16.0
- Black: 26.5.1
- Dependency source: `requirements-dev-lock.txt`
- Targeted tests: 13 passed in 0.21 seconds
- Ruff check: passed
- Black check: passed
- Full quality-gate exit code: 0

#### Branch verification

- Local branch: `tier-2-m365`
- Upstream branch: `origin/tier-2-m365`
- Local commit at synchronization:
`a7e8db56408a2413122af0e4a6880b3580012f07`
- Upstream commit at synchronization:
`a7e8db56408a2413122af0e4a6880b3580012f07`
- Branch divergence: none

#### Final project-environment verification

- Python: 3.12.13
- pytest: 9.1.1
- Ruff: 0.16.0
- Black: 26.5.1
- Targeted tests: 13 passed
- Ruff check: passed
- Black check: passed
- Full quality-gate exit code: 0
- Gate output:
`/tmp/frequentist_framework_tier2_final_gate.log`

#### Completion status

Tier 2 is complete. The project now has a supported Python environment,
a reproducibly pinned development toolchain, a passing complete quality
gate, updated environment provenance, and a synchronized tracked branch.

CLs integration, broader structural refactoring, orchestration, and the
generated-output policy remain outside Tier 2.

### 2026-07-31 — Modular Tier-1 and Tier-2 checker LXPlus verification and scope correction

#### Objective

Verify the newly added modular Tier-1 and Tier-2 check framework on LXPlus using the supported project environment, identify checker-specific failures, and preserve the established Tier-2 quality scope.

#### Substantial changes and verification completed

- Copied the modular `tier_checks/` framework into the LXPlus repository checkout.
- Confirmed that the framework contains 26 Python files under `tier_checks/`.
- Confirmed that the separate framework test file, `tests/test_tier_checks.py`, was not copied and remains to be restored before the framework is marked complete.
- Activated the supported repository-local Python environment.
- Verified the active toolchain:
  - Python 3.12.13
  - pytest 9.1.1
  - Ruff 0.16.0
  - Black 26.5.1
- Confirmed that automatic discovery finds all 12 modular checks:
  - six Tier-1 checks;
  - six Tier-2 checks.
- Ran the complete fast check mode.
- Fast-mode result:
  - PASS: 7
  - FAIL: 0
  - WARN: 0
  - SKIP: 5
- The five skipped checks were the expected in-depth-only checks.

#### In-depth verification results

The complete in-depth suite was run on LXPlus.

The following Tier-1 checks passed:

- program locations;
- deterministic reference regeneration;
- frozen-reference schema;
- targeted regression tests;
- J100/J50 workflow input contracts;
- J100/J50 recorded workflow outputs.

The targeted Tier-1 regression suite passed with 13 tests.

The following recorded background-only output logs were found and were non-empty:

- `run/fits/J100/run_481_3000_sixPar/quickFitLog_anaFit_sixPar_bkgOnly.log`
- `run/fits/J50/run_344_2079_sixPar/quickFitLog_anaFit_sixPar_bkgOnly.log`

The following Tier-2 checks passed:

- development dependency files;
- supported Python environment;
- pinned pytest, Ruff, and Black versions;
- the existing complete quality gate.

The authoritative complete quality gate passed with:

- 13 targeted tests passed;
- Ruff passed;
- Black passed;
- exit code 0.

The initial modular in-depth result was:

- PASS: 10
- FAIL: 2
- WARN: 0
- SKIP: 0
- exit code: 1

#### Diagnosed modular-check failures

The two failures were confined to the newly added standalone Ruff and Black wrapper checks.

The Black wrapper invoked:

```text
python -m black --check .
```

This incorrectly expanded the check to the complete repository. It attempted to process unrelated legacy Python files, Markdown files, ROOT binary files, and other files outside the established Tier-2 scope.

The Ruff wrapper invoked:

```text
python -m ruff check .
```

This also inspected the complete repository and reported findings in files outside the established Tier-2 target set.

These failures do not indicate a failure of the established Tier-2 quality gate. The existing `scripts/quality_check.py` continued to pass because it uses the intended explicit list of seven Tier-1 source and test targets.

#### Partial correction performed

- Began correcting the modular Ruff and Black checks so that they use an explicit quality-target list rather than the repository root.
- Ran Black on the new `tier_checks/` directory.
- Black reformatted 16 new checker Python files.
- Black then exited with code 123 because `tier_checks/README.md` was also passed to Black and was incorrectly parsed as Python.
- No repository-wide formatting was applied.
- No unrelated legacy source files, ROOT files, or generated analysis outputs were modified by Black.
- The correction is not yet complete.

#### Current status and remaining work

The modular framework is operational, all Tier-1 checks pass on LXPlus, and the authoritative Tier-2 quality gate remains fully passing.

The following work remains before the modular checker can be marked complete:

- Update the Ruff wrapper to receive only the authoritative Tier-2 Python targets and explicit `*.py` files under `tier_checks/`.
- Update the Black wrapper to receive only the authoritative Tier-2 Python targets and explicit `*.py` files under `tier_checks/`.
- Ensure that neither wrapper receives `.` or the complete `tier_checks/` directory as a formatting target.
- Run Black against the explicit checker Python-file list.
- Run Ruff against the explicit checker Python-file list.
- Recompile the checker package.
- Confirm that all 12 checks remain discoverable.
- Rerun the Tier-2 in-depth suite.
- Rerun the complete Tier-1 and Tier-2 in-depth suite.
- Require a final result of 12 passed, 0 failed, 0 warnings, and 0 skipped.
- Restore `tests/test_tier_checks.py`.
- Run the framework-specific tests and require two tests to pass.
- Review all changes before staging.
- Keep temporary reports, copied archives, unrelated generated files, and `post_fit.pdf` outputs outside the commit.

#### Scope boundary

The checker did not launch the complete J100 or J50 fit workflows. Verification remained limited to recorded paths, input and output contracts, existing background-only outputs, deterministic reference regeneration, regression tests, development tooling, and the established quality gate.
