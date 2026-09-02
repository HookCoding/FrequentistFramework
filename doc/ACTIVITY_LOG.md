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

### 2026-07-31 — Tier-1 review feedback: strict reference validation

#### Objective

Resolve merge-review feedback for the Tier-1 analysis-reference validator and add regression coverage for the new failure modes.

#### Substantial changes completed

- Updated `python/analysis_reference.py` to reject unexpected top-level workflows in addition to missing required workflows.
- Updated workflow-payload validation to reject unexpected keys rather than silently discarding them.
- Updated optional `BHresults.json` handling to:
  - convert JSON decoding and file-read failures into clear `ValueError` exceptions;
  - reject valid JSON whose top-level payload is not an object;
  - preserve the existing validation of `pyBHresult` and `global_Pval`.
- Added five focused regression tests to `tests/test_analysis_reference.py` covering:
  - unexpected workflows;
  - unexpected workflow payload keys;
  - malformed BH JSON;
  - non-object BH JSON;
  - `OSError` while reading `BHresults.json`.
- Removed the accidentally added `test.md` file before merge.

#### Verification performed

- Black passed for the changed implementation and test files.
- Ruff passed for the changed implementation and test files.
- The complete targeted Tier-1 test set was run with:

  `python -m pytest tests/test_analysis_reference.py tests/test_compare_root_outputs.py tests/test_repo_utils.py -q`

- Result: **18 tests passed in 0.42 seconds**.
- The reviewed changes were committed as:
  - `74ef39bda848b558bf3eb74a5f4bd0c077f78a65`
  - `Address Tier-1 analysis reference review feedback`
- Pull request #4 was merged into `upstream/harry` at merge commit:
  - `cb691d7`

#### Scope

The changes are limited to Tier-1 reference validation, its regression tests, activity-log documentation, and removal of the accidental `test.md` file.

The authoritative J100/J50 background-only workflow lock remains unchanged. CLs integration remains deferred.

### 2026-08-20: Tier-1 executable characterization safety foundation

#### Objective

Prepare the authoritative J100 and J50 workflows for a trustworthy executable characterization gate.

The intended final gate must rerun:

- `scripts/run_anaFit_J100.sh`
- `scripts/run_anaFit_J50.sh`

in fresh isolated output directories, then extract and compare the newly generated scientific results against frozen references.

This work focused on preventing false-positive test results before attempting the full analysis reruns.

#### Substantial changes completed

- **Added isolated output-directory support**
  - Updated `scripts/run_anaFit_J100.sh`.
  - Updated `scripts/run_anaFit_J50.sh`.
  - Both launchers now use `ANAFIT_OUTPUT_DIR` when it is provided.
  - The existing default output root, `run/fits`, remains unchanged for normal user execution.
  - This allows future integration tests to write into fresh temporary directories instead of overwriting or reusing committed outputs.

- **Corrected analysis return-status propagation**
  - Updated `python/run_anaFit.py` so `main()` returns the result from `run_anaFit()`.
  - Previously, the return value was discarded, allowing a failed analysis to appear as a successful process exit.
  - Analysis failures can now propagate through Python to the shell launcher and eventually to pytest.

- **Added mandatory external-command validation**
  - Added `execute_required()` to `python/run_anaFit.py`.
  - The helper rejects:
    - commands that return a nonzero exit status;
    - commands that return success without creating their required output files.
  - This establishes a consistent contract for mandatory scientific commands and their artifacts.

- **Hardened XMLReader workspace generation**
  - XMLReader is now treated as mandatory.
  - A nonzero XMLReader exit status terminates the analysis.
  - A successful exit without the expected workspace file also terminates the analysis.
  - The previous warning-and-continue behavior was removed from this path.

- **Hardened quickFit execution**
  - quickFit is now treated as mandatory.
  - A nonzero quickFit exit status terminates the analysis.
  - A successful exit without the expected fit-result file or quickFit log also terminates the analysis.
  - This prevents later extraction from consuming missing, incomplete, or stale fit outputs.

- **Added launcher-level failure propagation**
  - Both authoritative shell launchers now inspect the exit status from `python/run_anaFit.py`.
  - A failed Python analysis causes the launcher to print an error and exit with the same nonzero status.
  - Later plotting commands are not allowed to hide an earlier analysis failure.

- **Added focused regression tests**
  - Added `tests/test_run_anaFit.py`.
  - Added the new test file to the explicit test targets in `scripts/quality_check.py`.
  - The tests use controlled dependency stubs and do not run ROOT, XMLReader, quickFit, BumpHunter, or the full J100/J50 workflows.
  - Current coverage verifies:
    - successful analysis-status propagation;
    - failed analysis-status propagation;
    - acceptance of a successful mandatory command with its required output;
    - rejection of a nonzero mandatory-command status;
    - rejection of a missing required output;
    - termination after XMLReader failure, before quickFit starts;
    - termination after quickFit failure, before ROOT-based extraction starts.

#### Verification performed

- Baseline branch:
  - `tier-2-m365`
- Pre-change baseline commit:
  - `d50e925a1dad14ebb9254f50c90afe88a0415964`

- Focused regression tests:
  - Command: `python -m pytest tests/test_run_anaFit.py -q`
  - Result: **7 passed**

- Python syntax validation:
  - Command: `python -m py_compile python/run_anaFit.py`
  - Result: exit code **0**
  - Six pre-existing invalid-regex-escape `SyntaxWarning` messages remain in the legacy analysis file.

- Ruff validation:
  - Checked `scripts/quality_check.py` and `tests/test_run_anaFit.py`.
  - Result: **passed**

- Black validation:
  - Checked `scripts/quality_check.py` and `tests/test_run_anaFit.py`.
  - Result: **passed**
  - Both files were already correctly formatted.

- Shell syntax validation:
  - `bash -n scripts/run_anaFit_J100.sh`
  - Result: exit code **0**
  - `bash -n scripts/run_anaFit_J50.sh`
  - Result: exit code **0**

#### Current status

The output-isolation and failure-propagation foundation is complete and covered by focused tests.

The authoritative executable characterization gate is **not yet complete**. No real J100 or J50 analysis rerun was performed as part of this activity.

The current tests prove that important failures can be detected and propagated, but they do not yet prove that the complete scientific workflows reproduce the frozen results.

#### Remaining Tier-1 work

Before the executable characterization gate can be accepted:

- Add launcher-level tests proving that a simulated Python analysis failure:
  - produces a nonzero launcher exit status;
  - prevents later plotting commands from running.
- Apply mandatory failure handling to generated binning and BumpHunter execution.
- Decide whether plotting commands are optional diagnostics or required workflow stages.
- Define the complete required-artifact set for fresh J100 and J50 runs.
- Add slow integration tests that:
  - use fresh temporary output directories;
  - execute the actual authoritative J100 and J50 launchers;
  - reject stale or missing outputs;
  - extract results only from newly generated artifacts;
  - compare those results with frozen references.
- Demonstrate that a deliberately perturbed scientific result causes the characterization comparison to fail.
- Run the complete Tier-1 and Tier-2 quality gates after integration.
- Address or explicitly account for the six pre-existing Python `SyntaxWarning` messages if the final acceptance gate requires zero warnings.

#### Scope boundary

This activity did not perform Tier-3 structural refactoring, add orchestration, change the established J100/J50 scientific configuration, or extend the frozen reference to CLs.

Tier 3 and Tier 4 remain blocked until the test system successfully reruns and validates the authoritative J100/J50 workflows.

- Complete established Tier-1/Tier-2 quality gate:
  - Command: `python scripts/quality_check.py --mode full`
  - Targeted tests: **25 passed in 0.20 seconds**
  - Ruff: **passed**
  - Black: **passed**
  - Warnings: **0**
  - Skipped tests: **0**
  - Full quality-gate exit code: **0**
### 2026-08-20: Tier-1 BumpHunter execution and result-validation hardening

#### Objective

Harden the conditional BumpHunter masking path before running the authoritative J100 and J50 workflows as executable characterization tests.

The goal was to prevent a failed BumpHunter invocation, stale output file, malformed JSON result, or invalid masking interval from reaching the masked-refit stage.

#### Substantial changes completed

- **Made BumpHunter execution mandatory**
  - Updated `python/run_anaFit.py` so the BumpHunter masking-window command uses the established `execute_required()` contract.
  - A nonzero BumpHunter process status now terminates the analysis.
  - A successful process status without the expected `BHresults.json` output also terminates the analysis.

- **Prevented stale BumpHunter output reuse**
  - The analysis now removes a pre-existing `BHresults.json` before starting a new BumpHunter calculation.
  - This prevents a failed invocation from silently reusing results from an earlier analysis run.
  - The masking path requires a newly generated JSON output.

- **Used the BumpHunter environment interpreter directly**
  - Replaced the shell sequence that activated the environment, ran BumpHunter, and then deactivated it.
  - The workflow now invokes `pyBumpHunter/pyBH_env/bin/python3` directly.
  - This ensures the captured return status belongs to `python/FindBHWindow.py` and cannot be hidden by a later shell command.

- **Added validated BumpHunter result loading**
  - Added `load_bumphunter_results()` to `python/run_anaFit.py`.
  - The loader rejects:
    - unreadable result files;
    - malformed JSON;
    - JSON values that are not objects;
    - missing `BlindRange`, `MaskMin`, or `MaskMax` fields;
    - non-integer-compatible mask limits;
    - mask ranges where `MaskMin` is equal to or greater than `MaskMax`;
    - empty or non-string `BlindRange` values.
  - Validated mask limits are converted to integers before the masked refit.
  - Invalid results stop the workflow before masked XML files or masked fit outputs are produced.

- **Confirmed canonical resolution-binning inputs**
  - Verified that both canonical resolution-binning files exist and are tracked:
    - `Input/data/dijetisrTLA/mjjResolutionBinning_481.root`
    - `Input/data/dijetisrTLA/mjjResolutionBinning_344.root`
  - These files are treated as required immutable inputs for the canonical J100 and J50 characterization runs.
  - The canonical tests will not regenerate or modify these tracked inputs.

- **Expanded focused regression coverage**
  - Extended `tests/test_run_anaFit.py` with BumpHunter result-validation tests.
  - Added coverage for:
    - acceptance of a valid BumpHunter payload;
    - rejection of malformed JSON;
    - rejection of missing required fields;
    - rejection of nonnumeric mask limits;
    - rejection of reversed mask limits;
    - rejection of zero-width mask ranges.

#### Verification performed

- Python syntax validation:
  - Command: `python -m py_compile python/run_anaFit.py`
  - Result: exit code **0**

- Existing safety regression suite after BumpHunter execution hardening:
  - Result: **9 passed**

- Formatting of the expanded test file:
  - Command: `python -m black tests/test_run_anaFit.py`
  - Result: **1 file reformatted successfully**

- Ruff validation:
  - Command: `python -m ruff check tests/test_run_anaFit.py`
  - Result: **passed**

- Expanded focused safety and BumpHunter validation suite:
  - Command: `python -m pytest tests/test_run_anaFit.py -q`
  - Result: **15 passed in 0.16 seconds**

#### Current status

The BumpHunter command and result-validation logic are now substantially safer and covered by focused tests.

The current tests validate the standalone BumpHunter result loader, but they do not yet exercise the complete conditional BumpHunter branch inside `run_anaFit()`.

No real J100 or J50 analysis rerun was performed as part of this activity.

#### Remaining Tier-1 work

Before attempting the authoritative analysis reruns:

- Add execution-path tests proving that:
  - a stale `BHresults.json` is removed before BumpHunter runs;
  - a BumpHunter process failure terminates the analysis;
  - a successful BumpHunter process without a fresh JSON output terminates the analysis;
  - invalid fresh BumpHunter output prevents the masked refit.
- Run the complete established Tier-1 and Tier-2 quality gate.
- Define the required fresh-output artifacts for J100 and J50.
- Execute both authoritative workflows in clean isolated output directories.
- Extract scientific results only from the fresh outputs.
- Compare the fresh results against the frozen references.
- Demonstrate that a deliberate scientific-result perturbation causes the comparison to fail.

#### Scope boundary

This activity did not change the canonical J100/J50 scientific configuration, enable CLs, perform Tier-3 structural refactoring, or add Tier-4 orchestration.

Tier 3 and Tier 4 remain blocked until the authoritative executable characterization gate passes.

#### BumpHunter execution-path and complete quality-gate verification

- Expanded focused executable-characterization safety suite:
  - Command: `python -m pytest tests/test_run_anaFit.py -q`
  - Result: **19 passed in 0.18 seconds**
  - Ruff: **passed**
  - Black: **passed**

- Complete established Tier-1/Tier-2 quality gate:
  - Command: `python scripts/quality_check.py --mode full`
  - Targeted tests: **37 passed in 0.23 seconds**
  - Ruff: **passed**
  - Black: **passed**
  - Warnings: **0**
  - Skipped tests: **0**
  - Full quality-gate exit code: **0**

The BumpHunter execution path is now covered for stale-output removal, process failure, missing fresh output, valid output loading, and invalid fresh output rejection.

This result verifies the executable-characterization safety foundation. It does not yet constitute the final Tier-1 executable characterization gate because the tests have not rerun and compared the real J100 and J50 analyses.

### 2026-08-20: Authoritative J100/J50 executable characterization gate passes

#### Objective

Complete the highest-priority Tier-1 safety requirement by proving that the test system reruns the actual authoritative J100 and J50 analysis workflows, validates newly generated artifacts, and compares fresh scientific results against the frozen reference.

#### Substantial changes completed

- Added the explicitly marked slow integration test:
  - `tests/test_analysis_workflows_integration.py`
- Registered the pytest markers:
  - `integration`
  - `requires_root`
- Kept the slow scientific gate separate from the established fast/full development-quality gate.
- The integration test:
  - executes `scripts/run_anaFit_J100.sh` through Bash;
  - executes `scripts/run_anaFit_J50.sh` through Bash;
  - redirects both workflows into a fresh pytest temporary output root;
  - requires the expected workspace, fit result, fit parameters, post-fit result, quickFit log, generated configurations, and `analysis_results.json`;
  - requires every scientific artifact to be fresh and nonempty;
  - rejects unexpected masked-fit or BumpHunter outputs;
  - builds the analysis payload exclusively from newly generated outputs;
  - compares the complete fresh J100/J50 payload against the frozen reference.

- Added machine-readable scientific result manifests:
  - `run/fits/J100/run_481_3000_sixPar/analysis_results.json`
  - `run/fits/J50/run_344_2079_sixPar/analysis_results.json`
- Updated the frozen reference with the accepted post-fit chi-square p-values:
  - J100: `0.018448750724012808`
  - J50: `0.07853114301666252`
- Preserved the current background-only scope:
  - no BumpHunter masking was triggered;
  - `p_bh` remains null;
  - `cls_limit_points` remains empty.

#### Executable characterization verification

- Command:

  `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`

- Result:
  - **1 passed**
  - Runtime: **175.18 seconds**
  - J100 authoritative workflow: **passed**
  - J50 authoritative workflow: **passed**
  - Fresh artifact validation: **passed**
  - Manifest-backed scientific extraction: **passed**
  - Frozen-reference comparison: **passed**

#### Scientific results protected by the gate

The executable characterization gate now protects:

- J100 background-only fit parameters;
- J50 background-only fit parameters;
- J100 post-fit chi-square p-value;
- J50 post-fit chi-square p-value;
- expected absence of BumpHunter output for the canonical successful unmasked runs;
- expected background-only reference schema;
- expected empty CLs list under the current scope lock;
- freshness and presence of the required scientific artifacts.

#### Current status

The test system now reruns the real authoritative J100 and J50 workflows instead of only rereading committed outputs.

The primary executable-characterization requirement has passed.

Before this Tier-1 slice is closed, remaining verification should prove that a deliberate scientific-result perturbation fails the comparison, rerun the complete established quality gate, and review repository hygiene and final diffs.

#### Known non-blocking findings

- The J100 and J50 launcher files are not executable in the current Git mode and are invoked through Bash by the integration test.
- The post-fit plotting macro attempts to open masked artifacts even when masking was not triggered.
- Those plotting messages do not affect the scientific fit result or executable characterization comparison.
- CLs remains outside the current background-only scope.

#### Scope boundary

No Tier-3 structural refactoring or Tier-4 orchestration was performed.

Tier 3 and Tier 4 remain blocked until final deliberate-drift verification and complete gate verification are recorded.

#### Final executable-characterization acceptance verification

The Tier-1 executable-characterization safety work received both scientific and development-gate verification.

##### Deliberate scientific-drift detection

A temporary copy of the frozen reference was modified by changing the protected J100 chi-square p-value:

- Original J100 `p_chi2`: `0.018448750724012808`
- Perturbed J100 `p_chi2`: `0.02844875072401281`

The comparison correctly rejected the perturbed reference.

Result:

- Deliberate scientific perturbation: **detected**
- Repository reference modified: **no**
- False acceptance of changed scientific output: **no**

##### Final established Tier-1/Tier-2 quality gate

Command:

`python scripts/quality_check.py --mode full`

Result:

- Targeted tests collected: **48**
- Targeted tests passed: **48**
- Failed: **0**
- Warnings: **0**
- Skipped: **0**
- Ruff: **passed**
- Black: **passed**
- Full quality-gate exit code: **0**
- Test runtime: **0.36 seconds**

##### Slow executable scientific gate

Command:

`python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`

Result:

- Integration tests passed: **1**
- Failed: **0**
- Runtime: **175.18 seconds**
- J100 authoritative workflow rerun: **passed**
- J50 authoritative workflow rerun: **passed**
- Fresh artifact validation: **passed**
- Manifest-backed fit-parameter extraction: **passed**
- Manifest-backed chi-square p-value extraction: **passed**
- Frozen-reference comparison: **passed**

##### Tier-1 acceptance status

The highest-priority executable-characterization requirement is now satisfied.

The test system reruns the actual authoritative J100 and J50 workflows in fresh isolated output directories. It no longer depends only on rereading committed analysis products.

The accepted scientific baseline now protects:

- J100 background-only fit parameters;
- J50 background-only fit parameters;
- J100 post-fit chi-square p-value;
- J50 post-fit chi-square p-value;
- expected unmasked workflow behavior;
- expected absence of BumpHunter output for the canonical runs;
- freshness and presence of required scientific artifacts;
- the current background-only schema with CLs intentionally deferred.

Tier 3 and Tier 4 may remain blocked until the complete change set is reviewed and committed, but the executable characterization gate itself is passing.

#### Final completion status

The previously listed remaining acceptance checks are now complete:

- deliberate scientific-result perturbation was detected successfully;
- the established full quality gate passed with 48 tests, 0 failures, 0 warnings, and 0 skipped;
- Ruff and Black passed;
- the full quality-gate exit code was 0;
- the authoritative executable characterization test passed after rerunning both J100 and J50 from fresh isolated outputs.

The Tier-1 executable characterization gate is complete and passing.

Earlier statements in this activity log describing the gate as incomplete record intermediate project checkpoints and are superseded by this final completion status.

Tier 3 and Tier 4 remain outside this change set. Any decision to begin Tier 3 should follow review and commit of this completed Tier-1 safety work.
### 2026-08-20: Tier-1 and Tier-2 explicit coverage audit and gate expansion

#### Objective

Audit the original Tier-1 and Tier-2 requirements bullet by bullet and require explicit automated evidence for each completed claim.

This activity expanded the test system beyond basic workflow characterization to cover:

- canonical scientific launcher arguments;
- observable-specific numerical tolerances;
- selected ROOT histogram comparison behavior;
- external dependency revisions;
- scientific runtime readiness;
- generated-output ownership;
- plotting independence;
- launcher permissions;
- clean development-environment reproduction;
- CI quality-gate policy;
- optional pre-commit policy;
- known installation and bootstrap deficiencies;
- initial building blocks for expanded machine-readable provenance.

#### Canonical scientific workflow coverage

The launcher tests now explicitly protect the canonical J100 and J50 analysis contracts.

For J100, the tests verify:

- input file:
  `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root`;
- histogram:
  `hists_yStar06_rejectEta_10_16/afterSelection/nominal/h_mjj`;
- fit range:
  `481` to `3000`;
- six-parameter background model;
- prefit enabled;
- mask threshold `0.01`;
- signal fitting disabled;
- limit setting disabled.

For J50, the tests verify:

- input file:
  `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root`;
- histogram:
  `hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj`;
- fit range:
  `344` to `2079`;
- six-parameter background model;
- prefit enabled;
- mask threshold `0.01`;
- signal fitting disabled;
- limit setting disabled.

Verification result:

- canonical launcher contract tests: **2 passed**;
- selected launcher tests deselected: **20**;
- Ruff: **passed**;
- Black: **passed**.

CLs remains intentionally deferred. The schema continues to require `cls_limit_points`, and both canonical background-only references continue to require an empty list.

#### Observable-specific scientific comparison policy

Added an explicit tolerance-aware comparison policy for analysis references.

Current provisional tolerances:

- fit-parameter relative tolerance: `1e-6`;
- fit-parameter absolute tolerance: `1e-8`;
- p-value relative tolerance: `1e-5`;
- p-value absolute tolerance: `1e-8`.

The comparison keeps exact structural checks for:

- workflow names;
- workflow payload keys;
- fit-parameter names;
- presence versus absence of BumpHunter p-values;
- CLs list structure and contents.

Focused tests prove that:

- identical payloads pass;
- small fit-parameter drift within tolerance passes;
- small p-value drift within tolerance passes;
- excessive fit-parameter drift fails;
- excessive p-value drift fails;
- changed parameter names fail;
- absent versus present BumpHunter results fail;
- changed CLs structure fails.

Verification result:

- explicit tolerance tests: **8 passed**;
- selected tests deselected: **16**.

The authoritative J100/J50 executable characterization test was updated to use the same tolerance-aware comparison policy.

Verification result:

- executable scientific gate: **1 passed**;
- runtime: **185.64 seconds**.

The tolerance values are technically explicit and tested but remain provisional until approved scientifically.

#### ROOT histogram-comparison coverage

Expanded `tests/test_compare_root_outputs.py` from low-level numerical helper coverage to explicit selected-histogram behavior.

The test suite now covers:

- exact numerical equality;
- exact numerical mismatch;
- absolute tolerance;
- relative tolerance;
- NaN handling;
- zero-reference relative differences;
- missing ROOT objects;
- rejection of non-histogram ROOT objects;
- nested ROOT object paths;
- histogram-class mismatches;
- differing bin counts;
- changed bin contents;
- changed bin errors;
- changed bin edges;
- accepted content drift within tolerance.

Verification result:

- ROOT comparator tests: **17 passed**;
- Ruff: **passed**;
- Black: **passed**.

The accurate capability boundary is that the comparator checks explicitly selected TH1 histogram paths, including nested paths. It does not automatically discover and recursively compare every object in a ROOT file.

#### Plotting separated from scientific acceptance

Added `ANAFIT_SKIP_PLOTS=1` support to both authoritative launchers.

Normal user execution continues to produce plots by default. The scientific integration gate now disables plots explicitly so scientific acceptance depends only on:

- generated configurations;
- workspace output;
- fit result;
- fit-parameter output;
- post-fit ROOT output;
- quickFit log;
- analysis result manifest;
- numerical comparison with the frozen reference.

The required-artifact contract explicitly excludes PDF and other visual outputs.

Verification results:

- successful J100 launcher with plots disabled: **passed**;
- successful J50 launcher with plots disabled: **passed**;
- scientific artifact contract excludes plots: **passed**;
- real no-plot J100/J50 characterization gate: **1 passed**;
- scientific-gate runtime: **163.31 seconds**.

Plotting warnings and missing diagnostic plots can no longer determine scientific acceptance.

#### Authoritative launcher permissions

The documented direct launcher commands previously failed because both scripts were tracked with mode `100644`.

Restored executable permissions for:

- `scripts/run_anaFit_J100.sh`;
- `scripts/run_anaFit_J50.sh`.

The integration test now invokes the launchers directly rather than through an explicit Bash command.

Added an automated test requiring both authoritative launchers to have an executable permission bit.

Verification result:

- launcher permission test: **passed**;
- direct-execution J100/J50 integration gate: **1 passed**;
- selected non-integration test: **1 deselected**;
- runtime: **182.97 seconds**.

The executable behavior now matches the commands documented in `doc/TIER1_SYSTEM.md`.

#### Generated-output ownership

Added explicit repository-policy tests to verify that routine generated outputs remain ignored.

The policy tests cover synthetic:

- ROOT files;
- PDF files;
- XML files;
- log files.

The tests also verify that only the two canonical result manifests are re-included:

- `run/fits/J100/run_481_3000_sixPar/analysis_results.json`;
- `run/fits/J50/run_344_2079_sixPar/analysis_results.json`.

Existing generated ROOT, PDF, XML, and log products under the canonical directories were confirmed to be tracked legacy fixtures rather than newly exposed files.

Verification results:

- narrow ignore-policy test: **passed**;
- no unexpected untracked generated products test: **passed**.

#### External dependency revision contract

Added explicit prepared-environment tests for:

- `xmlAnaWSBuilder`;
- `quickFit`;
- `workspaceCombiner`;
- `pyBumpHunter`.

Pinned revisions:

- `xmlAnaWSBuilder`:
  `6b84050f3c0206a6f30eb40b103cc101e68505cc`;
- `quickFit`:
  `0408030b6c8d74a2e2c27a864a02756132d08f5a`;
- `workspaceCombiner`:
  `7d484ad3f89c4075d2c567aa4503fc56e1bb9468`;
- `pyBumpHunter`:
  `91f49a622bd77622edb02a1a2788fc12835e5b72`.

The tests verify:

- every required checkout exists;
- every checkout is readable by Git;
- every checkout matches the pinned revision;
- no checkout contains tracked source modifications.

Untracked build and environment directories such as `cmake/`, `RooFitExtensions/`, and `pyBH_env/` are tolerated.

Verification result:

- prepared dependency tests: **2 passed**.

#### Installation and bootstrap deficiencies

Added explicit tests for the installation contract.

Passing checks:

- `install.sh` records every expected dependency revision;
- `.gitmodules` declares all four expected dependency paths.

Known deficiencies are represented by strict expected-failure tests:

- `.gitmodules` declares dependencies, but the top-level Git index has no corresponding `160000` gitlink entries;
- `install.sh` contains active destructive `rm -rf` operations.

Verification result:

- installation-policy tests passed: **2**;
- strict expected failures: **2**;
- deselected unrelated tests: **9**.

These expected failures keep the known installation deficiencies visible without falsely marking fresh-clone reproducibility as complete.

Fresh-clone dependency acquisition and non-destructive bootstrap behavior remain high-priority Tier-1 work.

#### Scientific runtime readiness

Verified the separation between the development-quality environment and the scientific analysis environment.

Development-quality environment:

- Python `3.12.13`;
- pytest `9.1.1`;
- Ruff `0.16.0`;
- Black `26.5.1`.

Scientific environment selected by `scripts/setup_buildAndFit.sh`:

- LCG release `LCG_102a`;
- platform `x86_64-centos9-gcc11-opt`;
- Python `3.9.12`;
- ROOT/PyROOT `6.26/08`.

Both `xmlAnaWSBuilder/setup_lxplus.sh` and `quickFit/setup_lxplus.sh` explicitly select the same LCG release.

Added an explicit runtime-readiness test covering:

- successful setup;
- scientific Python version;
- ROOT and PyROOT versions;
- executable XMLReader;
- executable quickFit;
- executable BumpHunter Python environment;
- both canonical J100/J50 data inputs;
- both canonical resolution-binning inputs.

Verification result:

- authoritative scientific-runtime readiness test: **1 passed**.

The earlier ROOT `6.40.02` observation describes the shell before authoritative setup. The actual J100/J50 analyses use ROOT `6.26/08`.

#### Test-gate separation

Registered the pytest marker:

- `requires_analysis_dependencies`.

Applied it only to the two external-checkout tests.

The ordinary fast and full gates now exclude those prepared-environment checks while retaining:

- repository-root checks;
- frozen snapshot checks;
- generated-output ownership checks;
- analysis-reference tests;
- ROOT comparator tests;
- launcher and BumpHunter safety tests.

Verification results:

- lightweight repository tests: **4 passed**, **2 deselected**;
- prepared dependency tests: **2 passed**, **4 deselected**;
- fast quality gate: **58 passed**, **2 deselected**, exit code **0**.

The authoritative gate commands are now separated as follows:

- lightweight development gate:
  `python scripts/quality_check.py --mode full`;
- prepared dependency gate:
  `python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`;
- scientific executable characterization gate:
  `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`.

#### CI policy

Expanded `.github/workflows/tier1-root-comparison.yml` into the Tier-1 and Tier-2 lightweight quality workflow.

The workflow now:

- uses `actions/checkout@v4`;
- uses `actions/setup-python@v5`;
- selects Python `3.12.13`;
- installs `requirements-dev-lock.txt`;
- runs `python scripts/quality_check.py --mode full`;
- covers `harry` and `tier-2-m365`;
- does not launch the CERN-only integration test;
- does not require prepared external dependency checkouts.

Added an explicit CI policy test.

Verification result:

- CI policy test: **1 passed**.

Local complete lightweight verification after the CI update:

- tests passed: **59**;
- prepared dependency tests deselected: **2**;
- Ruff: **passed**;
- Black: **passed**;
- exit code: **0**.

An actual hosted CI run remains pending until the workflow is committed and pushed.

#### Optional pre-commit policy

Documented pre-commit as optional and outside the authoritative Tier-2 acceptance gate.

Current policy:

- `pre-commit` is not installed or pinned;
- contributors are not required to install Git hooks;
- the authoritative quality command is:
  `python scripts/quality_check.py --mode full`;
- the current Ruff hook version does not match the pinned Tier-2 Ruff version;
- pre-commit remains follow-up work.

Added an explicit policy test.

Verification result:

- optional pre-commit policy test: **1 passed**.

#### Clean dependency-lock reproduction

Created a new temporary Python 3.12 virtual environment outside the repository.

Installed only from `requirements-dev-lock.txt`.

Reproduced versions:

- Python `3.12.13`;
- pytest `9.1.1`;
- Ruff `0.16.0`;
- Black `26.5.1`.

Clean full-gate result:

- tests collected: **62**;
- tests passed: **60**;
- prepared dependency tests deselected: **2**;
- Ruff: **passed**;
- Black: **passed**;
- exit code: **0**.

Clean-environment evidence:

- temporary root:
  `/tmp/frequentist-tier2-clean.p2RO1b`;
- full-gate log:
  `/tmp/frequentist-tier2-clean.p2RO1b/full-gate.log`.

The bootstrap upgraded pip to `26.2.1`. Pip itself is not pinned and remains a minor reproducibility follow-up.

#### Initial machine-readable provenance helpers

Added and tested foundational provenance helpers in `python/run_anaFit.py`.

Current helpers cover:

- repository-root discovery from `__file__`;
- deterministic SHA-256 file hashing;
- clear failure for missing files;
- Git revision lookup;
- validation of full 40-character Git revisions;
- clear failure for non-repositories;
- scientific Python version collection;
- scientific Python executable collection;
- active ROOT version collection;
- clear failure when the active ROOT version is unavailable.

Focused verification results:

- repository-root tests: **2 passed**;
- file SHA-256 tests: **2 passed**;
- Git revision tests: **2 passed**;
- scientific runtime collection tests: **2 passed**.

The canonical data and template hashes were also recorded during the audit.

J100 input SHA-256:

`f6336bc2d0a966559072241be2d547ecd6b4b5bcae11e3c33751e25ce2a5d0e6`

J50 input SHA-256:

`4d2e0184ac95ee23bf1e74fef0a15cc86bf4a1f8342d90f703441fe90fbab3ee`

Shared template SHA-256 values:

- top-level template:
  `4d6d73b0445ad0e9777fabb6c734ec49fed9317801ffc19aa86692a3cb911807`;
- category template:
  `69b23311719bbe8f5e6e49f951fc479235e6b2cd889d8ba201e059b2674862d0`;
- six-parameter background template:
  `7d3d322bbf79734b0c65f9d407ec7316cd84ee9cd471e97c1d73b773807dda10`;
- signal template:
  `d7ae0ebc4aa3a234cae5c99d21dc5092278d10b22463c67f3048447ee41be314`.

The provenance helpers are tested, but the canonical manifests remain at schema version 1 and do not yet embed full runtime, revision, hash, and invocation provenance.

#### Latest combined gate checkpoint

Latest lightweight full-gate result:

- tests collected: **84**;
- selected tests: **82**;
- tests passed: **80**;
- prepared dependency tests deselected: **2**;
- strict installation-policy expected failures: **2**;
- Ruff: **passed**;
- Black: **passed**;
- exit code: **0**.

Latest prepared-dependency gate result:

- tests passed: **2**;
- tests deselected: **11**;
- exit code: **0**.

#### Current status

The Tier-1 scientific characterization system is complete and passing for the current background-only J100/J50 scope.

The Tier-2 development-quality environment remains reproducible and passing.

The following items remain incomplete:

- functional Git submodule gitlinks or an equivalent checked-in dependency acquisition manifest;
- non-destructive separation of dependency bootstrap and build operations;
- complete provenance embedded in `analysis_results.json`;
- final provenance-backed regeneration of the J100/J50 manifests;
- actual hosted CI execution after push;
- actual CLs characterization, intentionally deferred;
- scientific approval of the provisional numerical tolerances.

Tier 3 and Tier 4 remain outside this change set. Tier 3 should not begin until the completed Tier-1/Tier-2 work is reviewed and committed, and the remaining installation-reproducibility risks are explicitly accepted or repaired.

### 2026-08-21: Schema-version-2 scientific provenance completed

#### Objective

Complete machine-readable provenance for the authoritative J100 and J50 background-only executable characterization workflows.

#### Substantial changes completed

- Upgraded `analysis_results.json` from schema version 1 to schema version 2.
- Preserved schema-version-1 reader compatibility for legacy manifests.
- Added strict schema-version-2 provenance validation.
- Added provenance records for:
  - repository commit;
  - active scientific Python version and executable;
  - active ROOT version;
  - `xmlAnaWSBuilder` revision;
  - `quickFit` revision;
  - `workspaceCombiner` revision;
  - `pyBumpHunter` revision;
  - input data path and SHA-256;
  - top-level configuration path and SHA-256;
  - category configuration path and SHA-256;
  - background configuration path and SHA-256;
  - signal configuration path and SHA-256;
  - data histogram;
  - fit-range bounds;
  - signal-enabled state;
  - limit-enabled state;
  - prefit-enabled state;
  - mask threshold.
- Added repository-aware path resolution for relative and absolute scientific inputs.
- Added deterministic file SHA-256 helpers.
- Added Git revision lookup and validation.
- Added scientific runtime collection.
- Connected provenance generation to the successful `run_anaFit()` path.
- Preserved atomic manifest writing.
- Failed analyses still cannot create a misleading success manifest.
- Promoted validated schema-version-2 manifests for both canonical workflows.

#### Canonical scientific manifests

J100:

- schema version: `2`
- status: `success`
- masked: `false`
- `p_chi2`: `0.018448750724012808`

J50:

- schema version: `2`
- status: `success`
- masked: `false`
- `p_chi2`: `0.07853114301666252`

Both canonical manifests pass the production provenance validator and reproduce the frozen scientific reference.

#### Focused verification

- Repository-root helper tests: **2 passed**
- Analysis-path resolution tests: **3 passed**
- File SHA-256 tests: **2 passed**
- File-provenance tests: **3 passed**
- Git revision tests: **2 passed**
- Scientific runtime tests: **2 passed**
- Complete provenance-payload test: **1 passed**
- Provenance-validator tests: **10 passed**
- Schema-version-1 and schema-version-2 manifest tests: **passed**
- Schema-version-2 writer tests: **3 passed**
- Successful unmasked provenance-wiring test: **1 passed**
- Complete `tests/test_run_anaFit.py` suite: **39 passed** before the final wiring test was added
- Ruff: **passed**
- Black: **passed**

#### Final scientific executable gate

Command:

`python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`

Result:

- authoritative J100 rerun: **passed**
- authoritative J50 rerun: **passed**
- fresh schema-version-2 manifest generation: **passed**
- strict provenance validation: **passed**
- fresh artifact validation: **passed**
- tolerance-aware frozen-reference comparison: **passed**
- selected integration tests passed: **1**
- deselected non-integration tests: **2**
- runtime: **116.02 seconds**
- exit code: **0**

#### Current completion status

Machine-readable provenance is complete for the canonical background-only J100 and J50 executable characterization scope.

The executable characterization gate now protects both scientific results and the runtime, dependency, input, configuration, and invocation identity associated with those results.

Remaining known limitations are:

- functional Git submodule gitlinks are still absent;
- `install.sh` remains destructive;
- hosted CI execution remains pending a commit and push;
- CLs characterization remains intentionally deferred;
- numerical tolerances remain provisional pending scientific approval.

Tier 3 and Tier 4 remain outside this change set.

#### Final schema-version-2 verification checkpoint

The complete verification sequence was rerun after promoting the canonical schema-version-2 J100 and J50 manifests.

##### Lightweight full gate

Command:

`python scripts/quality_check.py --mode full`

Result:

- tests collected: **105**;
- tests passed: **101**;
- prepared-dependency tests deselected: **2**;
- strict expected installation-policy failures: **2**;
- unexpected failures: **0**;
- Ruff: **passed**;
- Black: **passed**;
- exit code: **0**.

The two strict expected failures continue to document:

- missing Git index gitlinks for the declared external dependencies;
- destructive `rm -rf` operations in `install.sh`.

##### Prepared-dependency gate

Command:

`python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`

Result:

- tests passed: **2**;
- tests deselected: **11**;
- failures: **0**;
- exit code: **0**.

The prepared `xmlAnaWSBuilder`, `quickFit`, `workspaceCombiner`, and `pyBumpHunter` checkouts remain at their pinned revisions and contain no tracked source modifications.

##### Scientific executable gate

Command:

`python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`

Result:

- tests passed: **1**;
- tests deselected: **2**;
- failures: **0**;
- runtime: **116.02 seconds**;
- exit code: **0**.

The scientific gate successfully:

- reran J100 and J50 from fresh isolated outputs;
- generated fresh schema-version-2 manifests;
- validated complete runtime, dependency, input, configuration, and invocation provenance;
- validated required fresh scientific artifacts;
- reproduced the frozen fit parameters and chi-square p-values within the approved provisional comparison policy;
- remained on the expected unmasked background-only path;
- excluded diagnostic plotting from scientific acceptance.

##### Final status

Machine-readable provenance is complete and passing for the canonical J100 and J50 background-only executable characterization scope.

The remaining known Tier-1 limitations are dependency acquisition and installer safety. These are represented by strict expected-failure tests and must not be described as complete.

Hosted CI execution remains pending commit and push. CLs characterization remains intentionally deferred. Numerical tolerances remain provisional pending scientific approval.

#### Tier-1 and Tier-2 operating documentation synchronized

Updated the user-facing system documentation to match the final verified implementation:

- `doc/TIER1_SYSTEM.md`
- `doc/TIER2_SYSTEM.md`
- `doc/TIER1_ENVIRONMENT_PROVENANCE.md`

The documents now record:

- schema-version-2 J100 and J50 manifests;
- complete machine-readable scientific provenance;
- canonical numerical chi-square p-values;
- explicit fit-parameter and p-value tolerances;
- the current lightweight, prepared-dependency, runtime-readiness, and scientific gates;
- the Python 3.12.13 development environment;
- the Python 3.9.12 and ROOT 6.26/08 scientific environment;
- plotting independence and executable launcher permissions;
- CI and optional pre-commit policies;
- missing Git submodule gitlinks and destructive installer behavior as known limitations.

Obsolete descriptions of null canonical chi-square p-values, the historical 18-test baseline, unavailable Ruff and Black tooling, and Python 3.9.25 as the active quality environment were removed.

Verification:

- all three documents retain their established repository names;
- no `UPDATED_*` files remain under `doc/`;
- documentation-specific `git diff --check` passed;
- complete repository `git diff --check` passed.

### 2026-08-21: Hosted CI policy-test hardening and Node.js 24 action update

#### Objective

Correct the hosted lightweight quality-gate failure caused by brittle exact-text assertions against human-readable Tier-2 documentation, and update the GitHub Actions dependencies to Node.js 24-compatible releases.

#### Substantial changes completed

- Removed exact prose assertions against `doc/TIER2_SYSTEM.md` from `tests/test_repo_utils.py`.
- Replaced the documentation-wording test with a machine-verifiable policy test confirming that pre-commit is absent from both development dependency manifests.
- Preserved the policy that pre-commit is optional and outside the authoritative Tier-2 acceptance environment.
- Updated the CI policy test so supported GitHub Action versions can be upgraded without requiring obsolete exact versions.
- Updated the hosted workflow:
  - `actions/checkout@v4` to `actions/checkout@v6`;
  - `actions/setup-python@v5` to `actions/setup-python@v6`.
- Kept the hosted workflow limited to the locked lightweight quality gate.
- Made no changes to scientific analysis code, frozen references, provenance records, or J100/J50 workflow contracts.

#### Verification performed

Focused policy tests:

- `test_ci_runs_locked_lightweight_full_gate`: passed
- `test_precommit_is_not_a_locked_development_dependency`: passed
- Result: **2 passed**

Formatting and linting:

- Ruff: **passed**
- Black: **passed**

Complete lightweight quality gate:

- tests collected: **105**
- tests passed: **101**
- prepared-dependency tests deselected: **2**
- strict expected installation-policy failures: **2**
- unexpected failures: **0**
- Ruff: **passed**
- Black: **passed**

#### Current status

The local lightweight gate passes after removing the brittle Markdown prose assertions and updating the GitHub Actions versions.

The two strict expected failures continue to represent:

- missing Git submodule gitlinks;
- destructive `rm -rf` operations in `install.sh`.

The updated workflow must be committed and pushed so the corrected hosted GitHub Actions result can be verified.

#### Scope boundary

This change affects only lightweight repository-policy testing and hosted CI dependencies. It does not change the background-only scientific analysis, the authoritative J100/J50 workflows, numerical references, scientific provenance, or the accepted no-signal scope.

### 2026-08-21: External dependency Git gitlinks repaired

#### Objective

Repair the missing Git index gitlinks for the four declared scientific dependencies so that the parent repository records their verified pinned revisions.

#### Substantial changes completed

- Aligned the dependency URLs in `.gitmodules` with the repositories used by `install.sh` and the verified prepared checkouts:
  - `xmlAnaWSBuilder`: `https://github.com/tofitsch/xmlAnaWSBuilder.git`
  - `quickFit`: `https://github.com/tofitsch/quickFit.git`
  - `workspaceCombiner`: `https://github.com/tofitsch/workspaceCombiner.git`
  - `pyBumpHunter`: `https://github.com/scikit-hep/pyBumpHunter.git`
- Added mode-`160000` Git index gitlinks for:
  - `xmlAnaWSBuilder` at `6b84050f3c0206a6f30eb40b103cc101e68505cc`
  - `quickFit` at `0408030b6c8d74a2e2c27a864a02756132d08f5a`
  - `workspaceCombiner` at `7d484ad3f89c4075d2c567aa4503fc56e1bb9468`
  - `pyBumpHunter` at `91f49a622bd77622edb02a1a2788fc12835e5b72`
- Added `ignore = untracked` for `workspaceCombiner` so local build products do not make the parent repository appear dirty.
- Removed the obsolete strict `xfail` marker from the gitlink policy test.
- Preserved the gitlink test as a normal required passing test.
- Updated the current Tier-1, Tier-2, and environment-provenance documentation.
- Preserved historical activity-log statements describing the previously missing gitlinks.
- Made no changes to dependency source files, scientific results, frozen references, or the authoritative J100/J50 workflow contracts.

#### Verification performed

Gitlink policy test:

- `test_declared_submodules_have_gitlink_entries`: **passed**

Complete repository utility suite:

- tests passed: **12**
- strict expected failures: **1**
- unexpected failures: **0**

Prepared-dependency gate:

- tests passed: **2**
- tests deselected: **11**
- failures: **0**
- exit code: **0**

Complete lightweight quality gate:

- tests collected: **105**
- tests passed: **102**
- prepared-dependency tests deselected: **2**
- strict expected installation-policy failures: **1**
- unexpected failures: **0**
- Ruff: **passed**
- Black: **passed**
- exit code: **0**

Repository validation:

- all four dependency entries use Git index mode `160000`;
- all four entries record the verified pinned revisions;
- all prepared checkouts contain no tracked source modifications;
- `git diff --check` passed.

#### Current status

The missing Git submodule gitlinks limitation is resolved.

The remaining strict expected installation-policy failure documents the destructive `rm -rf` operations in `install.sh`.

Clean-clone scientific dependency acquisition has not yet been verified end to end. The existing prepared LXPlus scientific environment remains verified and unchanged.

#### Scope boundary

This change repairs dependency metadata and repository policy only. It does not modify the background-only scientific analysis, the authoritative J100/J50 workflows, numerical references, schema-version-2 provenance, or the accepted no-signal scope.

### 2026-08-21: Non-destructive installer validation checkpoint

#### Objective

Replace the destructive installer with a verified read-only installation contract and harden the dedicated pyBumpHunter installer.

#### Substantial changes completed

- Removed destructive deletion, direct cloning, pulling, and checkout operations from `install.sh`.
- Made `install.sh` executable and added a read-only `--check` mode.
- Added checks for dependency gitlinks, checked-out revisions, tracked source changes, nested RooFitExtensions revisions, and required files.
- Replaced the pyBumpHunter installer with a non-destructive LCG 102a implementation.
- The pyBumpHunter installer preserves a valid environment and refuses to overwrite an invalid environment.
- Removed unpinned package upgrades, the external virtualenv dependency, LCG 105, and deprecated setup.py installation.
- Added machine-verifiable installer policy tests.
- Removed the obsolete test requiring dependency revisions to be duplicated inside `install.sh`.
- Updated the current Tier-1, Tier-2, and environment-provenance documentation.

#### Verification performed

- `bash install.sh --check`: passed and preserved the repository state.
- pyBumpHunter isolated installation and import test: passed.
- Existing pyBumpHunter environment preservation check: passed.
- Repository utility suite: 13 passed.
- Prepared-dependency gate: 2 passed and 11 deselected.
- Full lightweight gate: 103 passed and 2 deselected.
- Expected failures: 0.
- Ruff: passed.
- Black: passed.
- Shell syntax checks: passed.
- `git diff --check`: passed.

#### Current status

The destructive installer behavior is resolved. The repository now has a verified read-only installation check and a non-destructive pyBumpHunter installer.

A complete non-destructive C++ dependency build mode is not yet enabled. Clean-clone acquisition and building remain to be verified end to end.

#### Scope boundary

This checkpoint changes dependency validation and installation safety only. It does not modify the J100 or J50 scientific workflows, scientific results, frozen references, provenance, or the background-only analysis scope.

### 2026-08-21: Non-destructive dependency build mode completed

#### Objective

Complete and verify the non-destructive dependency build mode for the prepared scientific environment.

#### Changes completed

- Added `install.sh --build`.
- The build runs the read-only dependency contract before compilation.
- Added strict positive-integer validation for `INSTALL_JOBS`.
- Reused existing build directories without deleting them.
- Rebuilt the three pinned RooFitExtensions checkouts.
- Rebuilt xmlAnaWSBuilder, quickFit, and workspaceCombiner.
- Validated XMLReader, quickFit, workspaceCombiner manager, and their required libraries.
- Copied only the required RooFitExtensions products into each parent dependency.
- Avoided `cmake --install` for RooFitExtensions and avoided writes to `/usr/local`.
- Preserved failed build directories for inspection.
- Validated the existing pyBumpHunter environment through the safe installer.
- Updated installer policy tests and removed obsolete build-pending assertions.
- Updated the Tier-1, Tier-2, and environment-provenance documentation.

#### Isolated build verification

- RooFitExtensions and xmlAnaWSBuilder: passed.
- RooFitExtensions and quickFit: passed.
- RooFitExtensions and workspaceCombiner: passed.
- All isolated build directories were removed after testing.
- No tracked dependency source modifications were introduced.

#### Prepared-checkout build verification

- Command: `INSTALL_JOBS=2 bash install.sh --build`.
- Build exit code: 0.
- All three RooFitExtensions copies built successfully.
- xmlAnaWSBuilder, quickFit, and workspaceCombiner built successfully.
- The pyBumpHunter environment validated successfully.
- All 12 protected C++ build artifacts remained present.
- All 12 post-build SHA-256 hashes matched the pre-build baseline exactly.
- Only generated artifact timestamps changed.
- No tracked source modifications were introduced in any dependency.

#### Post-build verification

- Runtime readiness: 1 passed, 2 deselected in 16.39 seconds.
- Authoritative J100/J50 scientific gate: 1 passed, 2 deselected in 152.86 seconds.
- Lightweight gate: 103 passed, 2 deselected.
- Expected failures: 0.
- Ruff: passed.
- Black: passed.
- All relevant exit codes: 0.

#### Current status

The prepared-checkout non-destructive dependency build mode is operational and scientifically verified.

Clean-clone submodule acquisition and building have not yet been verified end to end in a separate fresh checkout.

#### Scope boundary

This change affects installation and dependency build safety only. It does not change the J100 or J50 background-only scientific workflows, frozen references, numerical results, or schema-version-2 provenance.

### 2026-08-21: Redundant modular tier-check framework retired

#### Objective

Audit the experimental `tier_checks/` framework against the completed authoritative Tier-1 and Tier-2 system, remove it if it provided no unique acceptance coverage, and preserve the existing activity-log history unchanged.

#### Coverage audit completed

Every framework component and all 12 modular checks were reviewed against the authoritative tests and operating gates.

The audit found no unique accepted scientific, dependency, repository, installer, build, runtime, or CI protection in `tier_checks/`.

The framework had fallen behind the authoritative system:

- its targeted pytest check omitted `tests/test_run_anaFit.py`;
- its Ruff and Black target list also omitted `tests/test_run_anaFit.py`;
- its Ruff and Black checks targeted the complete `tier_checks/` directory rather than an explicit Python-file list;
- its workflow-input check was weaker than the accepted launcher-contract tests;
- its recorded-output check verified existing non-empty logs rather than fresh scientific execution;
- its reference contract was weaker than the production schema-version-2 provenance validator;
- its full-quality check directly invoked the authoritative `scripts/quality_check.py` gate;
- its in-depth mode duplicated pytest, Ruff, and Black execution;
- warnings and skipped checks counted as successful outcomes.

#### Removal completed

- Removed all 27 tracked files under `tier_checks/`.
- Removed ignored Python bytecode caches left under the retired directory.
- Confirmed that the `tier_checks/` directory no longer exists.
- Updated `doc/TIER2_SYSTEM.md` to record the retirement and identify the authoritative replacement gates.
- Corrected the optional pre-commit wording to refer to the authoritative lightweight quality gate.
- Preserved every existing activity-log entry unchanged.

#### Useful ideas retained for possible future work

- per-command subprocess timeouts;
- optional provenance-backed JSON quality reports;
- requirement-level duration reporting;
- concise failure-output summaries;
- active Python executable and version reporting;
- active tool-version verification derived from the dependency lock;
- non-empty presence checks for authoritative documentation.

These are optional enhancements to the authoritative system and do not require maintaining a second acceptance framework.

#### Verification performed

- Full lightweight gate: 103 passed and 2 prepared-dependency tests deselected.
- Ruff: passed.
- Black: passed.
- Full lightweight gate exit code: 0.
- Prepared-dependency gate: 2 passed and 11 deselected.
- Prepared-dependency gate exit code: 0.
- Repository diff validation: passed.

#### Current status

The repository now has one authoritative Tier-1 and Tier-2 acceptance system rather than two divergent implementations.

The authoritative interfaces remain the lightweight full gate, prepared-dependency gate, runtime-readiness gate, J100/J50 scientific integration gate, installer check mode, and non-destructive dependency build mode.

#### Scope boundary

This change removes redundant experimental checking infrastructure only. It does not modify the authoritative J100 or J50 workflows, scientific results, frozen references, schema-version-2 provenance, dependency revisions, installer behaviour, or accepted background-only analysis scope.

#### 2026-08-27: Copilot merge-review safety corrections

##### Objective

Resolve the ten findings reported by GitHub Copilot during review of pull request 5 before merging the Tier-1 and Tier-2 branch.

##### Changes completed

- Updated mandatory command execution to remove expected outputs before execution, preventing stale XMLReader or quickFit artifacts from satisfying a successful command.
- Added explicit rejection of non-finite values in tolerance-aware scientific comparisons.
- Updated Git provenance collection to reject repositories with staged or unstaged tracked modifications while permitting untracked build products.
- Aligned schema-version-2 production and validation for optional background and signal configuration files by recording absent values as null.
- Preserved validated stable provenance in analysis-reference payloads.
- Added exact comparison of runtime identity, dependency revisions, input identity, configuration identity, and invocation settings.
- Kept repository_commit in full manifests while excluding it from the frozen reference to avoid a self-referential commit cycle.
- Updated quickLimit failure handling so a failed requested limit returns a nonzero status before provenance or success-manifest generation.
- Updated run_injections_anaFit.py to return the run_anaFit status.
- Updated the pyBumpHunter installer to reject an existing environment whose Python version differs from the authoritative scientific Python version.
- Updated the frozen J100 and J50 reference with stable provenance.
- Added focused regression coverage for stale outputs, non-finite values, provenance drift, dirty repositories, quickLimit failure, injection-runner status propagation, nullable configuration provenance, and pyBumpHunter interpreter-version policy.

##### Verification performed

Focused Python suites:

- 105 tests passed.
- Failures: 0.

Authoritative lightweight gate:

- Tests collected: 122.
- Tests passed: 120.
- Prepared-dependency tests deselected: 2.
- Ruff: passed.
- Black: passed.
- Unexpected failures: 0.

Repository validation:

- git diff --check passed.
- Broad legacy formatting changes introduced during review were removed before final verification.
- The resulting change set remains limited to the reviewed safety corrections and their tests.

##### Remaining work

- Commit the reviewed safety corrections.
- Regenerate the canonical J100 and J50 schema-version-2 manifests from the resulting clean committed tree.
- Verify that each regenerated manifest records the new commit.
- Rerun the prepared-dependency, runtime-readiness, scientific characterization, and lightweight gates.
- Resolve the remaining upstream merge conflicts.

#### 2026-08-27: Canonical manifest provenance corrected

##### Objective

Complete the remaining GitHub Copilot review findings by regenerating the canonical J100 and J50 schema-version-2 manifests from a clean committed source revision.

##### Changes completed

- Moved provenance collection to the beginning of run_anaFit(), before generated outputs can modify tracked repository artifacts.
- Retained success-manifest writing at the end of the workflow so failed analyses cannot record success.
- Committed the provenance-ordering correction as:
  - 132a8b35e9e3a4042fe55a452c5806514cac8556
  - Capture provenance before analysis output generation
- Confirmed the repository was clean before scientific execution.
- Regenerated J100 and J50 in a temporary output root.
- Copied only the regenerated analysis_results.json manifests into the canonical tracked locations.
- Preserved all other tracked scientific artifacts unchanged.

##### Scientific regeneration results

J100:

- Global chi-square p-value: 0.018448750724012808.
- Workflow completed successfully.
- Manifest repository commit:
  - 132a8b35e9e3a4042fe55a452c5806514cac8556

J50:

- Global chi-square p-value: 0.07853114301666252.
- Workflow completed successfully.
- Manifest repository commit:
  - 132a8b35e9e3a4042fe55a452c5806514cac8556

##### Verification performed

- Both workflows completed successfully from temporary isolated outputs.
- Both regenerated manifests record the clean source revision used for execution.
- Only the two canonical analysis_results.json files were promoted.
- The canonical reference validation test passed:
  - 1 passed.
  - 43 deselected.
  - Failures: 0.

##### Review status

All ten GitHub Copilot review findings are now resolved at the implementation and canonical-evidence level. The two inaccurate manifest-revision findings are resolved by scientifically regenerating both canonical manifests from clean commit 132a8b35e9e3a4042fe55a452c5806514cac8556.

##### Remaining verification

- Rerun the prepared-dependency gate.
- Rerun scientific runtime readiness.
- Rerun the authoritative J100/J50 scientific characterization gate.
- Rerun the authoritative lightweight gate.
- Commit the regenerated manifests and this evidence entry.
- Resolve the upstream merge conflicts.

#### 2026-08-27: Copilot review corrections final verification

##### Final verification

Prepared-dependency gate:

- 2 passed.
- 11 deselected.
- Failures: 0.

Scientific runtime-readiness gate:

- 1 passed.
- 2 deselected.
- Runtime: 22.63 seconds.
- Failures: 0.

Authoritative J100/J50 scientific characterization gate:

- 1 passed.
- 2 deselected.
- Runtime: 208.62 seconds.
- Both workflows completed successfully.
- Stable provenance matched the frozen reference.
- Failures: 0.

Authoritative lightweight gate:

- Tests collected: 122.
- Tests passed: 120.
- Prepared-dependency tests deselected: 2.
- Ruff: passed.
- Black: passed.
- Unexpected failures: 0.

Repository state:

- The working tree remained clean after final scientific verification.
- Both canonical manifests record source revision 132a8b35e9e3a4042fe55a452c5806514cac8556.
- All ten GitHub Copilot review findings are resolved and verified.

#### 2026-08-28: GitHub-hosted scientific runtime probe implemented

##### Objective

Begin evaluating whether the authoritative FrequentistFramework scientific runtime can execute on a GitHub-hosted Linux runner before enabling dependency builds or the complete J100/J50 characterization analysis.

##### Changes completed

- Added `.github/workflows/scientific-analysis.yml`.
- Kept the hosted scientific probe separate from the existing Tier-1 and Tier-2 lightweight quality workflow.
- Configured manual execution through `workflow_dispatch`.
- Selected the fixed `ubuntu-24.04` GitHub-hosted runner image.
- Restricted workflow permissions to read-only repository contents.
- Added per-branch concurrency control and a 30-minute job timeout.
- Configured recursive submodule checkout without persisted Git credentials.
- Added CernVM-FS setup for:
  - `atlas.cern.ch`;
  - `sft.cern.ch`.
- Pinned the CernVM-FS action to immutable commit:
  - `10197e000cc0add8e54ac4fb73d3ed44e2de72b4`.
- Added clean-checkout, recursive submodule, and `install.sh --check` validation.
- Added CernVM-FS repository probes.
- Added inspection of the hosted operating system, architecture, Python executable, Python version, ROOT version, and PyROOT version.
- Added execution of the existing scientific runtime-readiness pytest gate.
- Deliberately excluded dependency compilation and the complete J100/J50 scientific characterization gate from this initial probe.

##### Local verification

- Confirmed that the workflow contains no literal HTML line-break elements.
- YAML syntax validation passed.
- `git diff --check` passed.
- Reviewed the staged workflow diff.
- The existing lightweight GitHub Actions workflow remains unchanged.

##### Current status

The runtime-probe workflow is implemented locally but has not yet been executed on GitHub Actions. Its first hosted run must determine whether the existing `LCG_102a` `x86_64-centos9-gcc11-opt` scientific environment is compatible with the GitHub-hosted Ubuntu 24.04 runner.

Dependency building, the authoritative J100/J50 scientific characterization gate, caching, scheduled execution, and required-check status remain deferred until the hosted runtime probe passes.

##### Hosted trigger correction

- The initial manual workflow could not be started while it existed only on the feature branch.
- Added a temporary push trigger limited to `github-actions-analysis`.
- Retained `workflow_dispatch` for manual execution after the workflow becomes available from the repository default branch.
- The temporary branch trigger will be removed or revised after the hosted probe has been verified.

##### First hosted probe result and cleanliness-policy adjustment

- GitHub Actions run `33164486810` started successfully from commit `6ca611d51c5a4114c25f86a79ba530d5dbc6bb09`.
- Recursive checkout completed with all four top-level dependencies at their recorded pinned revisions.
- CernVM-FS setup completed before repository validation.
- The job stopped because the CernVM-FS action created an untracked `apt_cache/` directory and the workflow treated any non-clean repository status as fatal.
- Changed the general repository-cleanliness check from a fatal assertion to a GitHub Actions warning with the detected status printed in the log.
- Retained recursive submodule reporting and mandatory `install.sh --check` validation.
- Scientific runtime compatibility remains untested because the first job stopped before the CernVM-FS repository probes and LCG runtime steps.

##### Nested RooFitExtensions acquisition added

- The second hosted probe passed top-level gitlink validation for `xmlAnaWSBuilder`, `quickFit`, `workspaceCombiner`, and `pyBumpHunter`.
- `install.sh --check` then failed because `xmlAnaWSBuilder/RooFitExtensions` was absent.
- Confirmed that none of the three parent dependency revisions records `RooFitExtensions` as a Git gitlink.
- Confirmed that the prepared LXPlus checkouts use the publicly readable repository:
  - `https://gitlab.cern.ch/atlas_higgs_combination/software/RooFitExtensions.git`
- Confirmed that the required revision is available:
  - `ba94bfcbfa4f4a4e3541ade09580399e409e8514`
- Added a workflow step that acquires separate RooFitExtensions checkouts for `xmlAnaWSBuilder`, `quickFit`, and `workspaceCombiner`.
- Each checkout is detached at the exact recorded revision and verified before `install.sh --check` runs.
- Kept acquisition outside `install.sh` so its `--check` mode remains read-only.
- LCG and ROOT compatibility remain untested because the second hosted run stopped during dependency validation.

##### Scientific setup shell compatibility corrected

- The next hosted probe reached `scripts/setup_buildAndFit.sh`.
- Scientific setup stopped because the workflow enabled Bash nounset mode and `_DIRXMLWSBUILDER` is intentionally unset before initial environment setup.
- Changed only the two workflow steps that source the scientific setup script from `set -euo pipefail` to `set -eo pipefail`.
- Retained immediate command-failure and pipeline-failure handling.
- Dependency acquisition and validation progressed beyond the previous missing RooFitExtensions failure.
- LCG and ROOT compatibility remain pending the corrected hosted rerun.

##### ATLAS setup errexit compatibility corrected

- The next hosted probe reached ATLAS local environment setup.
- `atlasLocalSetup.sh` refused to continue because Bash errexit mode was enabled by the GitHub Actions shell.
- Updated both scientific setup steps to follow the established `install.sh` pattern:
  - disable errexit and nounset while sourcing `scripts/setup_buildAndFit.sh`;
  - capture the setup exit status;
  - restore errexit;
  - fail explicitly if scientific environment setup returns a nonzero status.
- Setup failures remain fatal and are reported through a GitHub Actions error annotation.
- LCG and ROOT compatibility remain pending the corrected hosted rerun.

##### Ubuntu-compatible LCG platform override added

- The hosted runtime probe established the LCG 102a CentOS 9 view but could not execute its binaries on Ubuntu 24.04.
- Observed missing host-library failures included:
  - `libicuuc.so.67`;
  - `libcrypt.so.2`.
- Confirmed that CVMFS provides the LCG 102a platform:
  - `x86_64-ubuntu2204-gcc11-opt`.
- Added an opt-in `ANAFIT_LCG_PLATFORM` override to `scripts/setup_buildAndFit.sh`.
- Preserved `x86_64-centos9-gcc11-opt` as the default when the override is unset, retaining the established LXPlus scientific environment.
- Configured the GitHub-hosted runtime-probe job to use:
  - `ANAFIT_LCG_PLATFORM=x86_64-ubuntu2204-gcc11-opt`.
- The override configures the selected LCG view and reproduces the XMLReader and quickFit path and library setup without modifying the pinned dependency checkouts.
- Shell syntax validation passed.
- Hosted Python, ROOT, dependency-build, and scientific compatibility with the Ubuntu LCG view remain pending rerun.
- The frozen J100/J50 references still record the CentOS 9 Python executable path. Hosted provenance comparison must be addressed before enabling the complete characterization gate.

##### Hosted Ubuntu LCG runtime verified and build phase added

- The hosted probe successfully established the Ubuntu-compatible LCG 102a view.
- Verified scientific runtime:
  - Python 3.9.12;
  - ROOT and PyROOT 6.26/08;
  - Python executable under `x86_64-ubuntu2204-gcc11-opt`.
- The runtime-readiness test reached its required-artifact checks and failed because the scientific dependencies had not yet been built.
- The first missing executable was:
  - `xmlAnaWSBuilder/build/bin/XMLReader`.
- Added the authoritative non-destructive dependency build command:
  - `INSTALL_JOBS=2 bash install.sh --build`.
- Added post-build `install.sh --check` validation.
- Added the prepared-dependency pytest gate after the build.
- Increased the hosted job timeout from 30 to 90 minutes.
- The complete runtime-readiness gate remains pending the first hosted dependency build.
- A ROOT compiler include-path diagnostic was observed and will be evaluated only if it causes an actual build or runtime failure.

##### Hosted CMake compatibility correction

- The first hosted dependency build established Python 3.9.12 and ROOT 6.26/08 and passed the complete installation-contract check.
- `xmlAnaWSBuilder/RooFitExtensions` configured and built successfully.
- ROOT emitted compiler include-path and C++ standard-library mismatch diagnostics, but the RooFitExtensions build completed.
- The subsequent `xmlAnaWSBuilder` configuration failed because CMake 4.2.1 removed compatibility with projects declaring a minimum CMake version below 3.5.
- Added `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` to both centralized CMake configuration paths in `install.sh`:
  - nested RooFitExtensions configuration;
  - parent C++ dependency configuration.
- The pinned external dependency sources remain unchanged.
- Shell syntax validation and `git diff --check` passed.
- Completion of the three RooFitExtensions builds, parent dependency builds, runtime-readiness gate, and scientific characterization gate remains pending the corrected hosted rerun.

##### Hosted dependency build completed

- The corrected hosted run completed all three nested RooFitExtensions builds and the parent scientific dependency builds.
- Post-build `install.sh --check` passed with all top-level gitlinks and nested RooFitExtensions revisions verified.
- The post-build prepared-dependency pytest gate initially used `/usr/bin/python` because GitHub Actions starts each step in a fresh shell.
- The system Python did not provide pytest.
- Updated the post-build verification step to restore `scripts/setup_buildAndFit.sh` and validate its status before invoking pytest.
- The verification step now uses the LCG 102a Python 3.9.12 environment.
- The prepared-dependency pytest gate and runtime-readiness gate remain pending the corrected rerun.

##### Hosted build and runtime foundation verified

- GitHub Actions run `33168104641` passed at commit:
  - `eb59c6824fd1fafc1db2175f685a79ef2876a687`.
- Total workflow duration was 5 minutes 58 seconds.
- CernVM-FS probes passed for `atlas.cern.ch` and `sft.cern.ch`.
- Verified hosted scientific runtime:
  - Python 3.9.12;
  - ROOT and PyROOT 6.26/08;
  - LCG platform `x86_64-ubuntu2204-gcc11-opt`.
- All three RooFitExtensions checkouts were acquired at revision:
  - `ba94bfcbfa4f4a4e3541ade09580399e409e8514`.
- All nested RooFitExtensions builds completed.
- `xmlAnaWSBuilder`, `quickFit`, and `workspaceCombiner` built successfully.
- The pyBumpHunter environment was created and validated.
- The complete non-destructive dependency build passed.
- Prepared-dependency gate:
  - 2 passed;
  - 11 deselected;
  - failures: 0.
- Scientific runtime-readiness gate:
  - 1 passed;
  - 2 deselected;
  - runtime: 4.13 seconds;
  - failures: 0.
- ROOT compiler include-path and C++ standard-library mismatch diagnostics remained non-fatal during the successful build.

##### Authoritative hosted characterization added

- Added execution of the existing authoritative J100/J50 scientific characterization gate after the hosted build and runtime-readiness gates.
- The workflow invokes:
  - `tests/test_analysis_workflows_integration.py`;
  - marker expression `integration and requires_root`.
- No scientific comparison or provenance validation has been weakened.
- The first hosted characterization run will determine whether the Ubuntu LCG build reproduces the canonical J100/J50 scientific results.
- The frozen reference currently records the CentOS 9 LCG Python executable path, so an exact stable-provenance mismatch may occur even if the numerical results reproduce.

##### First hosted J100 characterization failure diagnosed

- The hosted characterization gate reached the real J100 workflow.
- XMLReader completed and generated the J100 workspace.
- quickFit was invoked but did not create:
  - `FitResult_anaFit_sixPar_bkgOnly.root`.
- The analysis correctly returned a nonzero status and the integration test failed.
- The failure occurred before manifest generation and frozen-reference comparison.
- Build and runtime logs showed that the dependencies were compiled with Ubuntu GCC 13.3 while the selected LCG platform is `x86_64-ubuntu2204-gcc11-opt`.
- ROOT also reported an inability to extract GCC 11 standard-library include paths and a possible C++ standard-library mismatch.
- Added failure-only diagnostics to the hosted characterization step.
- On failure, the workflow now prints:
  - available compiler commands and versions;
  - all generated quickFit logs;
  - any generated fit-result and fit-parameter files.
- The workflow preserves and returns the original characterization failure status.
- No scientific acceptance or provenance validation was weakened.

##### Hosted compiler toolchain aligned with LCG

- Expanded failure diagnostics confirmed that the Ubuntu 24.04 runner provided GCC and G++ 13.3.0.
- The selected LCG platform expects the GCC 11 toolchain.
- `x86_64-linux-gnu-g++-11` was unavailable.
- The generated quickFit log was empty and no fit-result files were created, indicating failure during early executable or ROOT initialization.
- Added installation of `gcc-11` and `g++-11` before CernVM-FS setup.
- Added explicit checks that both installed compilers report major version 11.
- Added a check that `x86_64-linux-gnu-g++-11` is available.
- Set the hosted job environment:
  - `CC=gcc-11`;
  - `CXX=g++-11`.
- This aligns dependency compilation with the `x86_64-ubuntu2204-gcc11-opt` LCG platform and provides the compiler executable ROOT attempts to invoke.
- The authoritative J100/J50 characterization gate remains pending the GCC 11 hosted rerun.

##### Hosted quickFit executable diagnostics expanded

- Installing GCC 11 provided `x86_64-linux-gnu-g++-11`, but the hosted J100 quickFit invocation still exited before producing output.
- The redirected quickFit log remained empty and no fit-result files were created.
- Added failure-only diagnostics for:
  - compilers recorded in each dependency CMake cache;
  - quickFit executable metadata;
  - dynamic-library resolution through `ldd`;
  - a bounded direct `quickFit --help` startup probe;
  - the direct startup-probe exit status.
- Existing compiler, quickFit-log, and generated-fit-file diagnostics remain enabled.
- The characterization gate continues to return its original failing status.
- No scientific acceptance criteria were changed.

##### Portable quickFit redirection implemented

- Raw Unicode code-point inspection confirmed that the quickFit command used the Bash-specific `&>` redirection operator.
- The command is executed through `subprocess.call(..., shell=True)`, which uses `/bin/sh` rather than guaranteeing Bash.
- On the GitHub-hosted Ubuntu runner, `/bin/sh` did not apply the intended combined stdout and stderr redirection.
- This allowed the shell command to return before the expected quickFit output and log files were created.
- Replaced the Bash-specific operator with portable POSIX-compatible redirection:
  - `> quickFitLog.log 2>&1`.
- Added regression coverage that verifies:
  - portable stdout and stderr redirection is present;
  - the Bash-specific combined-redirection operator is absent.
- Raw code-point inspection verified the resulting redirection characters unambiguously.
- Focused regression result:
  - 1 passed;
  - 47 deselected.
- Complete `tests/test_run_anaFit.py` result:
  - 48 passed.
- Ruff passed for `tests/test_run_anaFit.py`.
- Black passed for `tests/test_run_anaFit.py` with no changes required.
- `python/run_anaFit.py` compiled successfully.
- Six existing invalid-escape `SyntaxWarning` messages remain in legacy code and are unrelated to this correction.
- The authoritative hosted J100/J50 characterization gate remains pending rerun.

##### Hosted J100/J50 scientific results reproduced

- The portable quickFit redirection correction allowed both authoritative workflows to complete on the GitHub-hosted runner.
- J100 and J50 created their required fit-result and fit-parameter artifacts.
- The hosted results reproduced the canonical fit parameters and chi-square p-values.
- The characterization comparison reached the final provenance check.
- The only difference was the scientific Python executable path:
  - LXPlus baseline: `x86_64-centos9-gcc11-opt/bin/python`;
  - GitHub-hosted runtime: `x86_64-ubuntu2204-gcc11-opt/bin/python`.
- Python remained version 3.9.12.
- ROOT and PyROOT remained version 6.26/08.
- Tool revisions, input hashes, configuration hashes, invocation settings, fit parameters, and p-values matched the frozen reference.
- Added an explicit allowlist containing only the CentOS 9 and Ubuntu 22.04 LCG 102a Python executable paths.
- Added `ANAFIT_EXPECTED_PYTHON_EXECUTABLE` support to the integration test.
- The environment override is rejected unless it exactly matches one of the approved paths.
- When no override is supplied, the existing frozen CentOS 9 reference remains unchanged.
- Configured the hosted workflow to select the approved Ubuntu LCG Python executable.
- Exact comparison of all remaining provenance and scientific values remains unchanged.
- Ruff and Black passed for the updated integration test.
- Final hosted characterization verification remains pending rerun.

##### Final GitHub-hosted scientific verification

GitHub Actions run `33173767689` completed successfully.

Complete workflow:

- Status: passed.
- Total duration: 7 minutes 51 seconds.
- GitHub-hosted runner: Ubuntu 24.04.
- Scientific LCG platform: `x86_64-ubuntu2204-gcc11-opt`.
- Scientific Python: 3.9.12.
- ROOT and PyROOT: 6.26/08.
- Compiler: GCC and G++ 11.

The workflow successfully completed:

- recursive checkout of the four pinned top-level dependencies;
- acquisition of the three pinned RooFitExtensions checkouts;
- CernVM-FS setup and repository probes;
- read-only installation-contract validation;
- non-destructive compilation of RooFitExtensions and the three C++ dependencies;
- pyBumpHunter environment creation and validation;
- prepared-dependency verification;
- scientific runtime-readiness verification;
- authoritative J100 and J50 workflow execution;
- required fresh-artifact validation;
- schema-version-2 provenance validation;
- frozen scientific-reference comparison.

Authoritative J100/J50 characterization gate:

- 1 passed.
- 2 deselected.
- Runtime: 127.70 seconds.
- Failures: 0.
- J100 completed successfully.
- J50 completed successfully.
- Fit parameters reproduced the frozen reference.
- Chi-square p-values reproduced the frozen reference.
- Tool revisions, input hashes, configuration hashes, and invocation settings matched.
- The approved Ubuntu LCG Python executable was recorded and validated.

##### Completion status

The GitHub-hosted scientific analysis workflow is operational and passing. It provides clean hosted dependency acquisition, non-destructive dependency building, runtime verification, and complete J100/J50 scientific characterization.

The existing lightweight Python 3.12 quality workflow remains separate and unchanged.

The branch-specific push trigger remains temporary while the workflow is under review. Before final integration, review whether to retain manual execution only, add scheduled execution, or run the hosted scientific gate for selected trusted branch changes.

##### Single complete hosted test job implemented

- Expanded the passing GitHub-hosted scientific workflow into one complete test job.
- Renamed the workflow to:
  - `Complete hosted analysis test suite`.
- Renamed the job to:
  - `Complete lightweight and scientific test suite`.
- Added the locked development environment to the beginning of the same job:
  - Python 3.12.13;
  - dependencies from `requirements-dev-lock.txt`.
- Added the authoritative complete lightweight quality gate:
  - `python scripts/quality_check.py --mode full`.
- The single job now runs, in sequence:
  - the complete lightweight pytest suite;
  - Ruff;
  - Black;
  - scientific dependency acquisition;
  - installation-contract validation;
  - non-destructive scientific dependency building;
  - the prepared-dependency pytest gate;
  - the scientific runtime-readiness pytest gate;
  - the authoritative J100/J50 characterization pytest gate.
- The development and scientific Python environments remain separated within the job.
- The scientific steps continue to restore LCG 102a Python 3.9.12 and ROOT 6.26/08 explicitly.
- The workflow remains automatic for pushes to `github-actions-analysis` and can also be invoked manually.
- YAML syntax validation and `git diff --check` passed.
- Final execution of the expanded single job remains pending.

##### Tracked repository modifications changed from fatal to warning

- Changed scientific Git provenance collection so staged or unstaged tracked modifications no longer stop the analysis.
- `get_git_revision()` now:
  - determines the current full Git revision;
  - checks for tracked modifications;
  - prints a warning when tracked modifications are present;
  - prints the tracked Git status;
  - returns the current revision so the analysis can continue.
- Untracked files remain permitted as before.
- Failures to determine the Git revision or inspect repository status remain fatal.
- The manifest continues to record the current 40-character repository commit.
- A warning indicates that the recorded commit does not fully describe the modified working tree.
- Updated regression coverage for both staged and unstaged tracked modifications.
- Focused regression result:
  - 2 passed;
  - 46 deselected.
- Complete `tests/test_run_anaFit.py` result:
  - 48 passed.
- Ruff passed for `tests/test_run_anaFit.py`.
- Black passed for `tests/test_run_anaFit.py`.
- `python/run_anaFit.py` compiled successfully.
- Six existing invalid-escape `SyntaxWarning` messages remain in legacy code and are unrelated to this change.
- Hosted verification of the revised provenance behavior remains pending.

##### README installation and validation instructions corrected

- Replaced the unsafe sourced installer command:
  - `. install.sh`
- Documented the supported non-destructive build command:
  - `bash install.sh --build`
- Added an explicit warning that sourcing `install.sh` can terminate the active shell when the installer reaches an `exit` command.
- Reformatted the installation, setup, run, file, and validation instructions as structured Markdown.
- Replaced the outdated quality-check description with the current Tier 1 and Tier 2 validation model.
- Documented the locked Python development-environment setup.
- Documented the authoritative complete lightweight quality command:
  - `python scripts/quality_check.py --mode full`
- Added links to:
  - `doc/TIER1_SYSTEM.md`;
  - `doc/TIER2_SYSTEM.md`;
  - `doc/TIER1_ENVIRONMENT_PROVENANCE.md`.
- `git diff --check` passed.

#### 2026-09-01: GitHub-hosted analysis branch merged into tier-2-m365

##### Merge completed

- Merged `github-actions-analysis` into `tier-2-m365` using an explicit merge commit.
- The merge completed without conflicts.
- The merged change set includes:
  - the complete GitHub-hosted lightweight and scientific test workflow;
  - CVMFS and Ubuntu-compatible LCG 102a setup;
  - hosted dependency acquisition and non-destructive building;
  - GCC 11 and CMake 4 compatibility;
  - portable quickFit output redirection;
  - approved cross-platform runtime provenance;
  - warning-only handling for tracked repository modifications;
  - updated installation and validation documentation;
  - associated regression tests and activity-log evidence.

##### Post-merge lightweight verification

Command: `python scripts/quality_check.py --mode full`

Result:

- Tests collected: 122.
- Tests selected: 120.
- Tests passed: 120.
- Prepared-dependency tests deselected: 2.
- Unexpected failures: 0.
- Ruff: passed.
- Black: passed.
- Black files unchanged: 8.
- Existing legacy `SyntaxWarning` messages: 6.

##### Current status

The local `tier-2-m365` branch contains the verified merge and is ahead of `origin/tier-2-m365`. The merged target branch has not yet been pushed.

## 2026-09-02: Tier-3 pre-flight baseline (Chunk 0)

### Objective

Begin executing `doc/TIER3_COMPLETION_PLAN.md`. Per the plan's Chunk 0,
prove the branch is in the fully-passing state the plan's Section 2
baseline claims before any Tier 3 extraction PR is opened, so any later
gate failure can be attributed to a Tier 3 change and not to a
pre-existing condition.

### Branch

- Created `tier-3-completion` from `tier-3-claude` at commit `5cb6a32`
  (`updated workflow to current branch`).
- Committed `doc/TIER3_COMPLETION_PLAN.md` as `3f025cc` (`Add Tier 3
  completion plan`) — the plan document only; no production code changed.
- Two pre-existing, unrelated local modifications carried over from
  `tier-3-claude` (`.github/workflows/scientific-analysis.yml`,
  `.github/workflows/tier1-root-comparison.yml`) remain uncommitted and
  untouched; they are out of Tier 3 scope and were not staged.

### Pre-change state

Per the plan's Section 2 baseline: Tier 1 and Tier 2 are complete and
verified on this branch's ancestry; `python/run_anaFit.py` is still a
single 901-line module; no Tier 3 extraction has begun.

### Verification performed

All three gates from `doc/TIER3_COMPLETION_PLAN.md` Section 7, run with
nothing else staged, at commit `3f025cc`:

1. `python scripts/quality_check.py --mode full`
   - Tests collected: 122; selected: 120; passed: 120; prepared-dependency
     tests deselected: 2; unexpected failures: 0.
   - Ruff: passed. Black: passed (8 files unchanged).
   - Six pre-existing legacy `SyntaxWarning` messages in `run_anaFit.py`
     (invalid escape sequences), unrelated to this baseline, unchanged
     from prior entries.
   - Exit code: 0.

2. `python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`
   - 2 passed, 11 deselected.
   - Exit code: 0.

3. `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
   - Real authoritative J100/J50 rerun from fresh isolated output
     directories, fresh schema-version-2 manifests, tolerance-aware
     frozen-reference comparison.
   - 1 passed, 2 deselected, runtime 126.12s.
   - Exit code: 0.

- `git status -sb`: only the two pre-existing, unrelated workflow-file
  modifications noted above; no untracked artifacts left by test
  execution.
- `git diff --check`: passed (exit 0).

### Current status

The Chunk 0 baseline is established and fully passing. `tier-3-completion`
is ready for Chunk 1 (`run_execution.py`) PR A (characterization tests for
`execute`/`execute_required`, no production-code changes) per
`doc/TIER3_COMPLETION_PLAN.md`.

### Remaining open chunks

All of Chunks 1 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open.
None has started.

## 2026-09-02: Tier-3 refactoring — Chunk 1.A: characterization tests for `execute`/`execute_required`

### Objective

Pin down the current, unmodified behavior of `execute()` and
`execute_required()` in `python/run_anaFit.py` before extracting them into
`run_execution.py`, per `doc/TIER3_COMPLETION_PLAN.md` Chunk 1.

### Pre-change state

`execute_required()` already had four direct tests
(`test_execute_required_accepts_success_with_expected_output`,
`test_execute_required_rejects_stale_expected_output`,
`test_execute_required_rejects_nonzero_command_status`,
`test_execute_required_rejects_missing_expected_output`), but every one of
them replaces `execute` itself via `monkeypatch.setattr(module, "execute",
...)` before calling anything. `execute()` — the function that actually
prints `"EXECUTE: {cmd}"` and calls `subprocess.call(cmd, shell=True)` —
had never been called for real by any existing test.

### Target functions — inputs and outputs (as they exist today)

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `execute(cmd)` | `cmd: str` | `int` (subprocess return code) | runs `cmd` via `subprocess.call(shell=True)`; prints `"EXECUTE: {cmd}"` |
| `execute_required(cmd, description, expected_outputs=())` | `cmd: str`, `description: str`, `expected_outputs: Sequence[str]` | `bool` | deletes any pre-existing `expected_outputs` before running; prints error diagnostics on failure |

### Tests added

- `test_execute_returns_the_real_subprocess_return_code` — calls the real
  `execute()` with `"exit 0"` and `"exit 3"`, asserts the return value is
  the shell's actual exit code both times (not a boolean or a hardcoded
  value).
- `test_execute_prints_the_command_before_running_it` — calls the real
  `execute("echo hello")` with `capsys` capturing stdout, asserts both
  `"EXECUTE: echo hello"` (the function's own print) and `"hello"` (the
  child process's own output) are present, proving a real subprocess ran.

### What this PR does NOT do

No production file was modified. `git diff --stat -- python/run_anaFit.py`
was empty throughout this change — only `tests/test_run_anaFit.py` was
touched.

### Verification performed

- `python -m pytest tests/test_run_anaFit.py -k execute -v` → 6 passed
  (the 4 existing `execute_required` tests plus the 2 new `execute`
  tests).
- `python -m pytest tests/test_run_anaFit.py -q` → 50 passed (full-file
  regression check).
- `python -m ruff check tests/test_run_anaFit.py` → passed.
- `python -m black --check tests/test_run_anaFit.py` → passed, unchanged.
- `git diff --stat -- python/run_anaFit.py` → empty.
- A manual, uncaptured replay of the same three `execute()` calls
  (`exit 0`, `exit 3`, `echo hello`) was run directly against the loaded
  module to trace exactly what each assertion checks, independent of
  pytest's own output capturing.

### Compliance review (Section 8, Characterization checklist)

1. Base commit for these tests: `365460e` (Chunk 0 baseline) — matches the
   file's state at the time the tests were written; `run_anaFit.py` was
   not touched afterward either.
2. Every new test asserts a real output/side-effect (return-code
   passthrough for two distinct exit codes; two distinct printed strings),
   not just "no exception."
3. `git diff --stat` shows no production file touched.
4. Tests were run and read by the user (repository owner), not only
   reported passing by the author.
5. Human-verification checkpoint: confirmed by the user in this session
   ("i agree lets continue") after reviewing the test code, the manual
   trace of `execute()`'s real output, and a full line-by-line walkthrough
   of both new tests and the shared `_load_run_anafit_module` helper.

### Remaining open chunks

Chunk 1.B (extraction of `run_execution.py`) and Chunks 2 through 12 are
open.

## 2026-09-02: Tier-3 refactoring — Chunk 1.B: extract `run_execution.py`

### Objective

Move `execute()` and `execute_required()`, characterized in Chunk 1.A
(commit `7029a46`), out of `python/run_anaFit.py` into a new
`python/run_execution.py`, per `doc/TIER3_COMPLETION_PLAN.md` Chunk 1.

### What changed

- `python/run_execution.py` created, containing `execute()` and
  `execute_required()` moved verbatim from `python/run_anaFit.py`
  (identical bodies; only the `os`/`subprocess`/`sys` imports they
  actually need were added at module top level), then formatted with
  `python -m black python/run_execution.py` once it was added to the
  Tier 2 target list (one whitespace-only change: a list comprehension
  collapsed to one line — no logic change).
- `python/run_anaFit.py`: the two function definitions removed; replaced
  with `from run_execution import execute, execute_required` (flat
  sibling-import style, matching the file's existing
  `from ExtractPostfitFromWS import PostfitExtractor`-style imports and
  how Python resolves imports when the script is run directly in
  production). Every existing call site (`execute_required(...)` in the
  XMLReader/quickFit/BumpHunter paths, `execute(...)` for the `.dtd`
  symlink, `plot_edm.py`, the resolution-binning generator, and the
  `quickLimit` call) is unchanged — only the definitions moved, not the
  call sites.
- `tests/test_run_anaFit.py`: added a blocking prerequisite fix to
  `_load_run_anafit_module` — `monkeypatch.syspath_prepend(str(module_path.parent))`
  before `exec_module`, so the file can resolve `run_anaFit.py`'s new
  `from run_execution import ...` line the same way Python's interpreter
  already does automatically in production (the script's own directory is
  auto-added to `sys.path` when run directly; loading via
  `importlib.util.spec_from_file_location` does not get that for free).
  Confirmed this was in fact required: adding the import before this fix
  reproduced the exact `ModuleNotFoundError` the plan predicted.
- `tests/test_run_execution.py` created: the six relocated tests, using
  the plain `from python import run_execution` style (no `ROOT`/sibling
  stubbing needed — this module touches neither).
- `scripts/quality_check.py`: added `python/run_execution.py` to
  `python_targets` and `tests/test_run_execution.py` to `test_targets`.

### A real integration issue the acceptance check caught

Relocating the tests was not a purely mechanical import-line swap. The
four original `execute_required` tests patch `execute` via
`monkeypatch.setattr(module, "execute", fake)`, where `module` was the
loaded `run_anaFit` module. Before this chunk, `execute_required` and
`execute` were defined in the *same* module, so patching `execute` there
correctly intercepted `execute_required`'s internal call. After the move,
`execute_required` lives in `run_execution.py` and looks up `execute` in
*that* module's own globals — patching the old location (`module.execute`
on the loaded `run_anaFit` object) no longer reaches it. Running the tests
immediately after moving the code (before relocating the tests) reproduced
this exactly: `test_execute_required_accepts_success_with_expected_output`
failed with `/bin/sh: line 1: analysis: command not found` (exit 127),
because `execute_required` was calling the real, unpatched `execute`. The
relocated tests in `tests/test_run_execution.py` patch
`run_execution.execute` directly instead — the correct target now that
both functions share that module's namespace — and all six pass. This
required changing more than the Test Relocation Rule's "import statement
only" baseline (the monkeypatch *target* and the direct-call *receiver*
also changed from `module.X` to `run_execution.X`), but no assertion,
fixture value, or expected outcome was altered — the correction is a
necessary consequence of the functions changing which module's namespace
they live in, not a hidden behavior change.

### Confirm: no scientific behavior changed

`execute()`/`execute_required()`'s bodies are byte-for-byte identical to
before the move (aside from Black's one whitespace-only reformat, applied
after the move). Every call site in `run_anaFit.py` is untouched.

### Verification performed

- `python -m pytest tests/test_run_execution.py tests/test_run_anaFit.py -v`
  → 6 + 44 = 50 passed (same total as before the move: the six execute
  tests moved out of `test_run_anaFit.py`, into `test_run_execution.py`,
  net count unchanged).
- `grep -n "^def execute\b\|^def execute_required\b" python/run_anaFit.py`
  → no output (definitions fully removed).
- `python scripts/quality_check.py --mode full` → 122 passed, 2
  deselected; Ruff passed; Black passed (after the one-file reformat
  above); exit code 0.
- `python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`
  → 2 passed, 11 deselected.
- `git status -sb` → only this chunk's five changed/new files, plus the
  two pre-existing unrelated workflow-file modifications carried over
  since Chunk 0.
- `git diff --check` → passed.
- No integration-gate rerun performed for this chunk — Chunk 1 does not
  touch a real branch condition or template-generation logic (unlike
  Chunks 4, 5, 8, where it is mandatory), only relocates two
  already-isolated pure functions.

### Compliance review (Section 8, Extraction checklist)

1. Chunk 1, PR B (this entry).
2. PR A is merged (`7029a46`) and referenced above.
3. No scientific constants, references, tolerances, dependency revisions,
   or canonical workflow arguments touched.
4. Relocated tests' diffs are not import-line-only, as noted above — the
   monkeypatch target and call receiver also changed, explicitly because
   the code moved between module namespaces; no assertion or expected
   value changed.
5. New/moved functions are all covered (relocated tests + no new
   functions were introduced this chunk).
6. Confirmed by grep: `run_anaFit.py` actually imports and never
   redefines `execute`/`execute_required`.
7. Only the six intended files were staged for this chunk (the two
   pre-existing workflow-file diffs remain unstaged, not part of this
   commit).
8. All required Section 7 gates ran and passed, output captured above.
9. `git diff --check` passed.
10. This activity-log entry appended (not a rewrite of any existing
    section).
11. Chunks 2 through 12 remain open, listed below.
12. No other branch's Tier 3 work was consulted.

### Remaining open chunks

Chunks 2 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open. Chunk 1
(both PR A and PR B) is complete and verified.

## 2026-09-02: Chunk 1.B supplementary verification — authoritative J100/J50 gate

### Objective

`doc/TIER3_COMPLETION_PLAN.md` Section 7 does not list the integration
gate as mandatory for Chunk 1 (only Chunks 4, 5, 8, and before 12). At the
user's explicit request, run it anyway after Chunk 1.B (commit `c68585b`)
as extra confidence, since real production code did change — including
the exact import mechanism (`from run_execution import execute,
execute_required`) that only gets exercised for real when the launcher
scripts invoke `run_anaFit.py` directly as a script, not through the test
suite's simulated `sys.path` fix.

### Verification performed

Command: `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`

Result:

- 1 passed, 2 deselected.
- Runtime: 168.02s.
- Both J100 and J50 reran from fresh isolated output directories using
  the real authoritative launcher scripts.
- Fresh schema-version-2 manifests generated and validated.
- Fit parameters and chi-square p-values matched the frozen reference
  within the established tolerances.
- Exit code: 0.

`git status -sb` after the run: only the two pre-existing, unrelated
workflow-file modifications carried since Chunk 0; no untracked artifacts
left by the run. `git diff --check`: passed.

### Current status

Chunk 1's extraction is now confirmed both by the fast unit-test gate
(recorded in the Chunk 1.B entry above) and by a real end-to-end rerun of
the actual production launcher scripts — the new module boundary and
import mechanism work correctly outside the test harness, not only inside
it. No scientific result changed.

## 2026-09-02: Housekeeping — remove duplicate `subprocess` import in `python/run_anaFit.py`

### Objective

Fix a pre-existing duplicate import identified by the user during review
of Chunk 1.B: `python/run_anaFit.py` imported `subprocess` twice — once as
part of the combined `import os,sys,re,argparse,subprocess,shutil` line,
and again as a standalone `import subprocess` line immediately before
`import ROOT`. This predates Tier 3 (present in the original,
unmodified file); Chunk 1.B's edit happened to touch the surrounding
lines (replacing the old `execute`/`execute_required` definitions with
`from run_execution import execute, execute_required`) without removing
the pre-existing duplicate.

### Change

Removed the standalone `import subprocess` line. The combined import on
line 4 already provides it; `subprocess.run(...)` (used in
`get_git_revision`, two call sites) is otherwise unaffected. Zero
behavior change — Python treats a duplicate `import` as a harmless no-op,
so this is a pure readability fix, not a bug fix.

### Verification performed

- `python -m py_compile python/run_anaFit.py` → compiles (only the six
  pre-existing, unrelated legacy `SyntaxWarning` messages remain).
- `grep -n "^import subprocess\|subprocess\."` confirms exactly one
  import and both existing `subprocess.run(...)` call sites unchanged.
- `python -m pytest tests/test_run_anaFit.py tests/test_run_execution.py -q`
  → 50 passed.
- `python scripts/quality_check.py --mode full` → 122 passed, 2
  deselected, Ruff/Black clean, exit code 0.
- `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
  → 1 passed, 164.10s, frozen reference reproduced exactly.
- `git status -sb` → only `python/run_anaFit.py` touched (1 line
  removed); `git diff --check` passed.

### Current status

This is a standalone housekeeping fix, not tied to a specific
`doc/TIER3_COMPLETION_PLAN.md` chunk. All chunk status is unchanged:
Chunks 2 through 12 remain open.

## 2026-09-02: Persist repository dirty state in schema-version-2 provenance (code + tests)

### Objective

Address a GitHub Copilot review finding on `python/run_anaFit.py`'s
`get_git_revision()`: when the main repository has tracked modifications,
the function prints a console warning and continues, but
`analysis_results.json` still records only `repository_commit`, with no
persisted, machine-verifiable indication that the tree was dirty at
generation time. Once the warning scrolls off, a manifest looks like a
clean, fully-provenance-tracked result even when it wasn't.

This is not new: an earlier Copilot review (2026-08-27, "Copilot
merge-review safety corrections") made dirty tracked trees **fatal**; that
was deliberately relaxed to a warning-only path the same day
("Tracked repository modifications changed from fatal to warning") to
avoid blocking the hosted CI environment. Copilot is now correctly
pointing out that the warning-only path never actually fixed the
underlying provenance-integrity gap it was already known to create — it
only stopped it from being fatal. This change resolves that gap properly:
keep the analysis non-fatal on a dirty tree (preserving the CI
compatibility the 2026-08-27 relaxation was for), but persist the dirty
state as a first-class, validated field in the manifest.

### Scope decision: main repository only, not the four pinned tool checkouts

`get_git_revision()` is also called for `xmlAnaWSBuilder`, `quickFit`,
`workspaceCombiner`, and `pyBumpHunter`. Their dirty state is **not**
added to the provenance schema, because it is already covered by an
existing, dedicated, always-run check:
`tests/test_repo_utils.py::test_external_dependency_checkouts_have_no_tracked_source_changes`
(part of the `requires_analysis_dependencies` gate). Duplicating that
signal inside the provenance payload would be redundant. `tool_revisions`
therefore keeps its existing shape (`dict[str, str]`) unchanged.

### Changes completed

- `python/run_anaFit.py`:
  - `get_git_revision()` now returns `(revision, dirty)` instead of just
    `revision`. The warning-and-continue behavior is unchanged; `dirty`
    is simply the boolean the function already computed to decide whether
    to print the warning.
  - `build_analysis_provenance()` unpacks the main repository's
    `(repository_commit, repository_dirty)` and adds `repository_dirty`
    as a new top-level key in the returned payload. The four tool-checkout
    calls now take `get_git_revision(path)[0]`, discarding their dirty
    flag per the scope decision above.
- `python/analysis_reference.py`:
  - `_validate_analysis_provenance()`: `repository_dirty` added to
    `required_keys` and validated as a boolean.
  - `_build_workflow_payload()`: `repository_dirty` is popped from the
    "stable" provenance used for the frozen-reference comparison,
    alongside the existing `repository_commit` pop — same
    self-referential-identity reasoning: both fields describe the specific
    run instance, not the scientific result, so neither belongs in a
    cross-run/cross-environment comparison. **This means the frozen
    reference (`tests/references/analysis_reference.json`) requires no
    change** — it never included `repository_commit` and correspondingly
    never includes `repository_dirty`.
- `tests/test_run_anaFit.py`:
  - Updated `test_get_git_revision_returns_clean_repository_commit`,
    `test_get_git_revision_warns_for_tracked_modifications` (both
    parametrized cases), and `test_get_git_revision_ignores_untracked_files`
    to unpack the new `(revision, dirty)` return value and assert the
    correct `dirty` boolean for each case (clean, staged/unstaged dirty,
    untracked-only).
  - Updated `test_build_analysis_provenance_records_runtime_inputs_tools_and_invocation`'s
    stub and expected payload to include `repository_dirty: False`.
  - Added `test_build_analysis_provenance_records_dirty_repository_state`:
    asserts that when the main repository is dirty but all four tool
    checkouts are clean, the payload records `repository_dirty: True`
    while `tool_revisions` correctly contains only revision strings with
    no leaked dirty state.
- `tests/test_analysis_reference.py`:
  - `_valid_analysis_provenance()` fixture updated with
    `"repository_dirty": False`.
  - `test_analysis_reference_comparison_rejects_provenance_drift` updated
    to pop `repository_dirty` alongside `repository_commit` from both
    sides, matching the production exclusion above.
  - `test_validate_analysis_provenance_accepts_complete_payload` asserts
    `repository_dirty is False`.
  - `test_validate_analysis_provenance_rejects_invalid_payload` gained a
    new parametrized case: a non-boolean `repository_dirty` value is
    rejected with `"repository_dirty must be boolean"`.

### Known, expected, temporary failure at this exact commit

`tests/test_analysis_reference.py::test_analysis_reference_matches_frozen_output`
calls `build_analysis_reference()` with no `repo_root` override, i.e.
against the **real, tracked** `run/fits/J100/.../analysis_results.json`
and `run/fits/J50/.../analysis_results.json` files. Those files were
generated by the pre-change code and do not yet have `repository_dirty`,
so `_validate_analysis_provenance()` now correctly rejects them as missing
a required key. This is the exact ordering problem the 2026-08-21
schema-version-2 rollout and the 2026-08-27 "Canonical manifest provenance
corrected" entry already hit and solved the same way: commit the code
first, then regenerate the two canonical manifests from that clean commit,
then commit the regenerated manifests separately. That regeneration is the
immediately following activity-log entry, not deferred.

### Verification performed

- `python -m py_compile python/run_anaFit.py python/analysis_reference.py`
  → compiles (same six pre-existing, unrelated legacy `SyntaxWarning`
  messages).
- `python -m pytest tests/test_run_anaFit.py -k "git_revision or build_analysis_provenance" -v`
  → 7 passed.
- `python -m pytest tests/test_run_anaFit.py -q` → 45 passed (44 + 1 new
  test).
- `python -m pytest tests/test_analysis_reference.py -v` → **44 passed, 1
  failed** (`test_analysis_reference_matches_frozen_output`, explained
  above — every other test, including the four new/updated provenance
  validation cases, passes).
- `python scripts/quality_check.py --mode full` → **123 passed, 1 failed,
  2 deselected**, same single expected failure; Ruff and Black were run
  separately against every touched file
  (`python/run_execution.py`, `tests/test_run_execution.py`,
  `tests/test_run_anaFit.py`, `python/analysis_reference.py`,
  `tests/test_analysis_reference.py`) since the gate's own Ruff/Black
  steps don't run after a pytest failure: both passed, no changes needed.
- `git diff --check` → passed.
- No integration-gate rerun yet — it is run as part of manifest
  regeneration in the next entry, since that rerun *is* the regeneration.

### Remaining open work

Regenerate and commit the two canonical manifests (immediately following
entry). Until that lands, `quality_check.py --mode full` is expected to
show exactly the one failure described above — this is not an unrelated
regression if seen at this specific commit.

## 2026-09-02: Canonical manifest provenance regenerated for repository_dirty

### Objective

Resolve the known, expected failure left by the previous entry
(`test_analysis_reference_matches_frozen_output`) by regenerating the two
canonical J100/J50 manifests from the clean commit that introduced
`repository_dirty` (`a83e888`), matching the established
2026-08-27 "Canonical manifest provenance corrected" precedent for this
exact kind of schema change.

### Procedure

- Confirmed the working tree was clean at commit `a83e888` before
  execution (`git status -sb`).
- Ran both authoritative launchers into a fresh, isolated temporary output
  root (`ANAFIT_OUTPUT_DIR`), with `ANAFIT_SKIP_PLOTS=1`:
  - `bash scripts/run_anaFit_J100.sh` — completed successfully, 2m1s,
    `p(chi2)=0.018` printed.
  - `bash scripts/run_anaFit_J50.sh` — completed successfully, 1m36s,
    `p(chi2)=0.079` printed.
- Inspected both fresh `analysis_results.json` manifests before promoting
  them: both recorded `"repository_commit": "a83e888c59bb..."` (exact
  match for the commit used), `"repository_dirty": false` (correctly
  clean), `p_chi2` values exactly matching the frozen reference
  (`0.018448750724012808` and `0.07853114301666252`), and every other
  provenance field (tool revisions, input/configuration hashes,
  invocation settings) unchanged from the previously committed manifests.
- Copied only the two regenerated `analysis_results.json` files into their
  canonical tracked locations, overwriting the previous ones. No other
  tracked scientific artifact was touched. Confirmed via `git diff
  --stat`: exactly 2 files, 3 lines each
  (`repository_commit` value changed, `repository_dirty` line added).

### Verification performed

- `python scripts/quality_check.py --mode full` → **124 passed, 2
  deselected**, exit code 0 (the previously-failing test now passes).
- `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
  → 1 passed, 190.39s. Both J100 and J50 reran from fresh isolated
  outputs a second time (independent of the regeneration run above) and
  matched the frozen reference within tolerance — confirming the
  regenerated canonical manifests are consistent with a completely
  independent fresh run, not just self-consistent with themselves.
- `python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`
  → 2 passed, 11 deselected.
- `git status -sb` → only the two manifest files; no untracked artifacts.
- `git diff --check` → passed.

### Current status

The Copilot-flagged provenance gap is fully resolved and verified:
`analysis_results.json` now persists a validated, machine-checkable
`repository_dirty` field for every future run, the two canonical
manifests reflect the current clean commit, and every established gate
(lightweight, dependency, and the real scientific characterization gate)
passes. This closes the finding; no further Tier 3 chunk work is implied
or affected by this change. Chunks 2 through 12 remain open.

## 2026-09-02: Propagate scientific setup failures instead of silently continuing

### Objective

Address a second GitHub Copilot review finding, on
`scripts/setup_buildAndFit.sh` lines 12-14: `source
"${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh"`, `lsetup "views
LCG_102a ..."`, and `lsetup cmake` had no exit-status check. Because every
caller that sources this script deliberately disables `errexit` first
(required, since ATLAS's own setup machinery isn't nounset/errexit-safe —
see the 2026-08-28 "ATLAS setup errexit compatibility corrected" entry), a
failed setup command was silently followed by the script's remaining
`export`/`mkdir` lines succeeding, so the sourced script still returned 0
overall. A caller checking that return code would see success and
potentially build or fit against the host environment instead of the
pinned LCG_102a view.

### Scope: both branches, and the two callers that don't check the sourcing's own exit status

Reading the complete file (not just the three lines Copilot's comment
quoted) found the identical pattern in the `else` branch (the *default*
LXPlus path used whenever `ANAFIT_LCG_PLATFORM` is unset — the path this
very development session has been exercising on lxplus975 all along, not
just the hosted-CI override path Copilot's comment happened to point at):
`source setup_lxplus.sh` for both `xmlAnaWSBuilder` and `quickFit` had the
same unguarded-failure problem.

Separately, guarding `setup_buildAndFit.sh` alone is necessary but not
sufficient: `scripts/run_anaFit_J100.sh` and `scripts/run_anaFit_J50.sh`
have no `set -e` anywhere and never checked the exit status of `.
"$setup_script"` — so even a correctly-`return 1`-ing setup script would
have been silently ignored by the two authoritative launchers, which is
exactly the concern Copilot's own wording ("The workflow then treats a
failed scientific setup as successful") points at. The hosted CI
workflow (`.github/workflows/scientific-analysis.yml`) already checks
this correctly (`setup_status=$?` after each `source
scripts/setup_buildAndFit.sh`, per the same 2026-08-28 precedent) and did
not need changing.

### Changes completed

- `scripts/setup_buildAndFit.sh`:
  - `ANAFIT_LCG_PLATFORM` branch: `source atlasLocalSetup.sh`, both
    `lsetup` calls now `|| return 1`.
  - Default LXPlus branch: `source setup_lxplus.sh` (both
    `xmlAnaWSBuilder` and `quickFit`) now has its exit status captured
    explicitly and checked *after* the following `cd .. || return 1` —
    not `|| return 1` directly on the `source` line, which would have
    returned before restoring the working directory, leaving the calling
    shell inside `xmlAnaWSBuilder/`/`quickFit/` on failure. Verified this
    ordering matters: an earlier draft of this fix using the naive `||
    return 1` form was caught by a directory-restoration test before being
    corrected (see Tests below).
  - Verified the success path is unaffected: sourced the corrected script
    directly on this LXPlus session (the same default branch every
    integration-gate run in this session has been exercising) — exit
    status 0, `_DIRXMLWSBUILDER`/`_DIRFIT` both correctly exported, `pwd`
    correctly back at the repository root afterward.
- `scripts/run_anaFit_J100.sh`, `scripts/run_anaFit_J50.sh`: added a
  `setup_status=$?` check immediately after `. "$setup_script"`, printing
  an error and exiting with that status on failure — the exact same idiom
  already used later in both scripts for `run_anaFit.py`'s own
  `analysis_status`.

### Tests added

- `test_setup_build_and_fit_propagates_setup_lxplus_failure_and_restores_cwd`
  (new, first direct test of `setup_buildAndFit.sh` itself — no prior
  test exercised its own logic in isolation): sources the real script
  against an isolated fake directory tree with a deliberately-failing
  `xmlAnaWSBuilder/setup_lxplus.sh`, asserts the source reports exit
  status 1 **and** that the calling shell's working directory is
  correctly restored, not left inside `xmlAnaWSBuilder/`. Caught the
  cwd-leak regression described above during development of this fix.
- `test_launcher_propagates_setup_failure_before_running_analysis`
  (new, parametrized over both launchers, mirroring the existing
  `test_launcher_propagates_analysis_failure_before_plotting` pattern):
  stubs `ANAFIT_SETUP_SCRIPT` with a script that fails, asserts the
  launcher exits with that failure code and that the (separately stubbed)
  analysis runner is never invoked and no plot output is produced.

A note on a test-authoring pitfall hit and fixed while writing the first
new test: the fake failing `setup_lxplus.sh` initially used `exit 1`.
Because `setup_lxplus.sh` is always *sourced*, never executed, `exit`
terminates the entire calling shell rather than just the source
operation — which silently killed the whole test harness process instead
of exercising the intended failure path. Confirmed the real external
`xmlAnaWSBuilder/setup_lxplus.sh` and `quickFit/setup_lxplus.sh` already
correctly use `return 1`, and fixed the fake fixture to match.

### Verification performed

- `bash -n` on all three changed scripts → syntax OK.
- `python -m pytest tests/test_run_anaFit.py -k "setup_build_and_fit or launcher" -v`
  → 7 passed (2 new + 5 existing, all unaffected).
- `python -m pytest tests/test_run_anaFit.py -q` → 48 passed.
- `python scripts/quality_check.py --mode full` → 127 passed, 2
  deselected, Ruff/Black clean, exit code 0.
- `python -m pytest tests/test_analysis_workflows_integration.py -v -m "requires_root or integration"`
  → **2 passed**, 238.75s: both the authoritative J100/J50
  characterization gate (real rerun, frozen reference reproduced) and
  `test_authoritative_setup_provides_scientific_runtime` (which directly
  sources the now-corrected `setup_buildAndFit.sh` to establish the real
  scientific environment) passed — confirming the fix does not break real
  environment setup, only closes the silent-failure gap.
- `python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`
  → 2 passed, 11 deselected.
- `git status -sb` → only the four intended files; `git diff --check`
  passed.

### Current status

Both GitHub Copilot findings raised on this PR are now resolved and
verified. This change is standalone, not tied to a `doc/TIER3_COMPLETION_PLAN.md`
chunk. Chunks 2 through 12 remain open.

## 2026-09-02: Correct wrong PATH/LD_LIBRARY_PATH in the ANAFIT_LCG_PLATFORM branch

### Objective

Address a third GitHub Copilot review finding, on
`scripts/setup_buildAndFit.sh` lines 18-21: the `ANAFIT_LCG_PLATFORM`
branch exported `_BIN_PATH="${_DIRXMLWSBUILDER}/bin"` and
`_LIB_PATH="${_DIRXMLWSBUILDER}/lib"`, but `install.sh` actually builds
XMLReader and `libxmlAnaWSBuilder.so` into `xmlAnaWSBuilder/build/bin` and
`xmlAnaWSBuilder/build/lib`.

### Independent verification of the claim (not taken on faith)

Directly inspected the real checkout before changing anything:

- `xmlAnaWSBuilder/bin/` — **does not exist**.
- `xmlAnaWSBuilder/build/bin/XMLReader` — the real, built executable.
- `xmlAnaWSBuilder/lib/` — exists and holds the copied
  `libRooFitExtensions.so` (a real, separate dependency — this is the
  directory Copilot's suggested fix correctly retains rather than
  discards).
- `xmlAnaWSBuilder/build/lib/libxmlAnaWSBuilder.so` — the real library,
  entirely absent from the old `LD_LIBRARY_PATH`.

Copilot's finding and suggested fix (union both lib directories, point
bin at `build/bin`) were both confirmed correct.

### The identical, unflagged bug in the parallel quickFit block

Reading the whole file (not just the quoted lines) found the same pattern
one block down, for `quickFit`, which Copilot's comment did not mention:
`_BIN_PATH="${_DIRFIT}/bin"` (exists but is **empty**) and
`_LIB_PATH="${_DIRFIT}/lib"` (has `libRooFitExtensions.so` but not
`libquick.so`). quickFit's actual build output is flat in `quickFit/build/`
(`quickFit`, `quickLimit`, `quickAsimov`, `libquick.so` all sit directly
there, confirmed via `ls` and via `install.sh`'s own build-verification
step), not nested under `build/bin`/`build/lib` the way xmlAnaWSBuilder is.
Fixed with the equivalent, layout-adjusted correction.

### Impact analysis — precise, not assumed

Before concluding this was purely defensive, checked what actually
depends on the broken values:

- `readelf -d` on the real built `XMLReader`/`quickFit` binaries shows
  both have **RPATH baked in** at build time (absolute paths into this
  checkout's own `build/lib` / `build` and `RooFitExtensions/build`), and
  `ldd` confirms both resolve their own shared libraries via that RPATH
  already. So on this checkout, the `LD_LIBRARY_PATH` gap was likely
  inert for XMLReader/quickFit specifically — and `run_anaFit.py` invokes
  both via **hardcoded relative paths**
  (`xmlAnaWSBuilder/build/bin/XMLReader`, `quickFit/build/quickFit`), so
  the broken `PATH` never mattered for those two either.
- `quickLimit` is different: `run_anaFit.py` invokes it via a **bare
  command name** (`execute("quickLimit -f ...")`, `python/run_anaFit.py:782`,
  no path prefix at all) — this genuinely depends on `PATH` alone to find
  `quickFit/build/quickLimit`. Under the old, broken
  `_BIN_PATH="${_DIRFIT}/bin"` (empty directory), any `dolimit=True` run
  under `ANAFIT_LCG_PLATFORM` would have failed with "command not found."
  This was never caught by the passing hosted CI run because the
  canonical J100/J50 background-only gate always has `dolimit=False` and
  never exercises `quickLimit`.

This is reported precisely rather than claiming the fix "unbroke the
hosted pipeline" (it likely didn't, for the tested background-only path)
or dismissing the finding as harmless (it was a real, silent gap for the
untested `dolimit=True` path, exactly the kind of defect Copilot review
exists to surface before it's hit in practice).

### Changes completed

- `scripts/setup_buildAndFit.sh`:
  - `ANAFIT_LCG_PLATFORM` branch: `_BIN_PATH`/`_LIB_PATH` corrected for
    both `xmlAnaWSBuilder` (`build/bin`; `build/lib:lib`) and `quickFit`
    (`build`; `build:lib`, since quickFit's build output has no nested
    `bin`/`lib`).
  - `ATLAS_LOCAL_ROOT_BASE` changed from unconditionally hardcoded to
    `"${ATLAS_LOCAL_ROOT_BASE:-/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase}"`
    — honors an existing value instead of always overwriting it. This is
    what makes the new test below possible at all: it is the same
    override-if-unset convention already used throughout this repo's
    scripts (`ANAFIT_SETUP_SCRIPT`, `ANAFIT_RUNNER`, `ANAFIT_OUTPUT_DIR`,
    etc.), applied here for the same reason. Zero behavior change in
    production, where this variable is never pre-set.

### Tests added

- `test_setup_build_and_fit_lcg_platform_branch_exposes_build_directories`
  (new): exercises the **real** `ANAFIT_LCG_PLATFORM` branch end-to-end,
  using a fake `ATLAS_LOCAL_ROOT_BASE` tree containing a stub
  `atlasLocalSetup.sh` that defines a no-op `lsetup` function (avoids
  needing genuine CVMFS/Ubuntu infrastructure, which isn't available on
  this lxplus session for this specific platform branch). Asserts the
  resulting `PATH` contains the real `xmlAnaWSBuilder/build/bin` and
  `quickFit/build` directories, `LD_LIBRARY_PATH` contains all four real
  library directories (`xmlAnaWSBuilder/build/lib`, `xmlAnaWSBuilder/lib`,
  `quickFit/build`, `quickFit/lib`), and explicitly that the old, wrong
  `xmlAnaWSBuilder/bin` path never reappears.

### Verification performed

- `bash -n scripts/setup_buildAndFit.sh` → syntax OK.
- `python -m pytest tests/test_run_anaFit.py -k "setup_build_and_fit or launcher" -v`
  → 8 passed (1 new + 7 existing, all unaffected).
- `python -m pytest tests/test_run_anaFit.py -q` → 49 passed.
- `python scripts/quality_check.py --mode full` → 128 passed, 2
  deselected, Ruff/Black clean, exit code 0.
- `python -m pytest tests/test_analysis_workflows_integration.py -v -m "requires_root or integration"`
  → 2 passed, 183.14s (both the authoritative J100/J50 characterization
  gate and the runtime-readiness gate) — confirms the unchanged default
  LXPlus branch (the one actually exercised on this session's own
  environment) and the rest of the script are unaffected by this fix.
  The `ANAFIT_LCG_PLATFORM` branch itself is validated by the new
  isolated unit test above plus, going forward, the existing hosted
  `scientific-analysis.yml` workflow, which is the only environment that
  genuinely exercises that branch for real.
- `python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`
  → 2 passed, 11 deselected.
- `git status -sb` → only the two intended files; `git diff --check`
  passed.

### Current status

All three GitHub Copilot findings raised on this PR are now resolved and
verified. Standalone change, not tied to a `doc/TIER3_COMPLETION_PLAN.md`
chunk. Chunks 2 through 12 remain open.

## 2026-09-02: Revise the plan's PR model to match the workflow actually used

### Objective

Address a fourth GitHub Copilot review finding, on
`doc/TIER3_COMPLETION_PLAN.md` guardrail 7 ("One PR = one step of one
chunk"): the actual PR opened for this branch bundles the pre-flight
baseline, Chunk 1's characterization and extraction, and several unrelated
standalone fixes together, which is exactly what guardrail 7 said never to
do. Copilot correctly identified that this means the plan's stated
mechanism for enforcing "tests written and human-verified before
production files are modified" — a separately merged characterization PR,
required before the extraction PR can even be opened — was not actually
happening.

### Root cause: the plan's guardrail 7 never matched the workflow the user chose

Earlier in this branch's history (Chunk 1's characterization checkpoint),
the user was explicitly asked whether to verify each step locally in
conversation or push a branch and open a real GitHub PR per step, and
chose local conversational verification. That choice is fundamentally
incompatible with guardrail 7's literal wording, which assumes a
separately-merged PR exists between every characterization and extraction
step. The plan document was never updated to reflect that choice at the
time it was made — this entry is that update, prompted by Copilot
correctly noticing the gap between the document and the practice.

### What was preserved vs. what changed

The safety **substance** guardrail 7 exists for was, in fact, honored for
Chunk 1: the characterization tests were reviewed (test code read, a real
unmocked trace of `execute()`'s output shown, a full line-by-line
walkthrough given) and explicitly confirmed by the user ("i agree lets
continue") *before* `run_anaFit.py` was touched. What was missing was the
GitHub **artifact** of that — a separately merged PR — not the
verification itself.

`doc/TIER3_COMPLETION_PLAN.md` is revised accordingly, offered to and
selected by the user from three options (rewrite the guardrail to match
reality; keep the guardrail and literally split into per-step PRs from
here on; retroactively split the already-open PR too). The chosen
approach:

- Section 5 ("The PR-chunk delivery model") retitled "The chunk delivery
  model," with a "Revision note" at its start explaining this exact
  history transparently, and rewritten throughout: each chunk is still
  delivered as two ordered, individually-verifiable steps (renamed
  "Step A"/"Step B" throughout the whole document, replacing "PR A"/"PR
  B"), each its own commit, but the human-verification checkpoint between
  them happens in session before Step B's commit is made, not via a
  separately merged PR. A new subsection, "What actually gets reviewed on
  GitHub," states plainly that individual steps are not each their own PR
  — work accumulates as ordered commits, and a PR is opened per chunk or
  a small labeled batch for final review, with the Step A/Step B ordering
  verifiable by reading the commit history within it.
- Guardrails 2, 3, 7, and 8 (Section 1) reworded to reference commits and
  the in-session verification checkpoint instead of PR merges.
- Section 8 retitled "Per-step compliance checklist," both checklist
  variants reworded (e.g. "is PR A merged" → "did Step A's commit precede
  this one in the branch history").
- Section 6 chunk-by-chunk text: every "PR A"/"PR B" label renamed to
  "Step A"/"Step B"; "single PR" chunk headers (0, 8, 12) renamed "single
  commit"; stray "PR content"/"PR description"/"opened and merged as its
  own tiny PR" phrasing corrected throughout.
- Section 7 and Section 9 updated similarly (gate-comment wording, the
  completion definition's "both its PRs... merged" → "both its steps'
  commits... made").

No guardrail was weakened: every substantive requirement (tests before
code, human verification of characterization before extraction, explicit
recording of that verification, append-only activity log, no scope
creep) is unchanged. Only the mechanism for the human-verification
checkpoint and the artifact structure around it changed, to describe what
this project actually does.

### Verification performed

- `grep -n "single PR\|PR's\|PR provides\|PR description\|PR content\|PR is not ready\|PR is marked\|two-PR\|characterization PR\|extraction PR\|PR A\|PR B\|PRs\b" doc/TIER3_COMPLETION_PLAN.md`
  → only two intentional, correct remaining matches (the Revision Note's
  historical reference to "the resulting single PR" Copilot reviewed, and
  "What actually gets reviewed on GitHub"'s description of the real,
  eventual PR's own commit history) — confirmed both are appropriate, not
  leftover stale wording.
- `grep -nE '[[:blank:]]+$' doc/TIER3_COMPLETION_PLAN.md` → clean.
- `git diff --check` → passed.
- No code, test, or gate changes in this entry — documentation only.

### Current status

`doc/TIER3_COMPLETION_PLAN.md`'s process description now matches the
workflow this branch has actually been using since Chunk 1. Going
forward, chunks continue to follow the same Step A → human verification →
Step B sequence as before; only the document's account of how that gets
reviewed on GitHub changed. Chunks 2 through 12 remain open.

## 2026-09-02: Activity-log completeness audit — three missing entries backfilled

### Objective

The user asked directly whether every change on this branch had been
recorded in this log. Rather than assume yes, cross-checked every commit
on `tier-3-completion` since it branched from `tier-3-claude` (`git log
--oneline 5cb6a32..HEAD`) against every dated section header in this file.
Found three commits with no corresponding entry. This entry backfills all
three, appended here per guardrail 2 (append-only; new entries go at the
end, existing ones are never reordered or edited) — the same approach
this log's own 2026-07-29 "Activity-log correction" entry used for an
identical situation.

### Gap 1 — `3f025cc`: "Add Tier 3 completion plan"

This is the commit that added `doc/TIER3_COMPLETION_PLAN.md` itself (1,318
lines) to this branch — the authoritative, from-scratch Tier 3 execution
plan described in this file's own preceding entries. No production code
was changed. This predates the Chunk 0 baseline entry immediately
following it in this log and was the first commit made on
`tier-3-completion` after branching.

### Gap 2 — `e3379fc`: "Enable hosted CI on tier-3-completion"

Added `tier-3-completion` to the branch-trigger lists in both
`.github/workflows/tier1-root-comparison.yml` (`pull_request` trigger) and
`.github/workflows/scientific-analysis.yml` (`push` trigger), matching the
same trigger coverage already present for `harry`, `tier-2-m365`, and
`tier-3-claude`. This commit also included a pre-existing, uncommitted
local edit (from the prior "updated workflow to current branch" session,
made by the user, not by this session) adding `tier-3-claude` to both
files and removing `tier1-root-comparison.yml`'s separate `push` trigger
for `harry`/`tier-2-m365` — both changes were already present, uncommitted,
in the working tree when this session began, and were committed together
since they touched the same lines. This commit is what made the hosted
`scientific-analysis.yml` push-triggered workflow actually run against
this branch for the first time; its first resulting run
(`https://github.com/HookCoding/FrequentistFramework/actions/runs/33629659100`)
passed.

### Gap 3 — `0da38fd`: "Potential fix for pull request finding"

Not a commit made by this session — authored and committed directly by
the user (Harry Hook) via GitHub's web UI, accepting a Copilot Autofix
suggestion on PR #6. Discovered when this session found the branch had
diverged from `origin/tier-3-completion` shortly after the push that
enabled hosted CI, and rebased Gap 2's follow-on commit onto it. Changes
`tests/test_analysis_workflows_integration.py`: merges two adjacent
Python string literals in `APPROVED_SCIENTIFIC_PYTHON_EXECUTABLES` (the
LCG_102a CentOS9/Ubuntu Python executable path strings) into one literal
each — a Copilot-flagged readability finding about relying on implicit
string-literal concatenation. Zero behavioral change (the concatenated
and single-literal forms produce identical string values); confirmed by
this session's full quality gate passing unchanged immediately after the
rebase.

### Verification performed

- `git log --oneline 5cb6a32..HEAD` (13 commits) cross-referenced against
  `grep -n "^## 2026-09-02" doc/ACTIVITY_LOG.md` (10 entries before this
  one) — confirmed exactly these three gaps and no others.
- Commit timestamps checked directly (`git log --reverse --format="%h %ad
  %s" --date=iso-strict`) to confirm claims in this entry against the
  actual record rather than memory: `0da38fd` (13:52:52+01:00, i.e.
  14:52:52 in this session's own +02:00 commits) postdates `e3379fc`
  (14:19:23+02:00), confirming it was authored on GitHub after the push
  that created the branch there, and predates `351b7d7` (14:59:04+02:00),
  confirming the rebase placed it correctly. This also caught a drafting
  error before commit: an earlier draft of this entry cited "Chunk 1.B
  supplementary verification" (`abfde43`, committed 14:09:51+02:00 —
  before `0da38fd` existed) as having verified Gap 3's change, which is
  impossible by timestamp alone. The commit that actually verified it is
  "Housekeeping — remove duplicate `subprocess` import," whose real
  J100/J50 integration-gate run (164.10s) ran after the rebase and
  exercises `APPROVED_SCIENTIFIC_PYTHON_EXECUTABLES` (the constant
  `0da38fd` edited) directly, since that test validates the runtime
  Python executable against it during the actual rerun.
- No code, test, or gate changes in this entry — documentation only,
  backfilling the record for commits already made, pushed, and verified
  by their own contemporaneous gate runs (Gap 1: no code to verify; Gap 2:
  verified by the hosted CI run cited above; Gap 3: verified as described
  immediately above).
- `git diff --check` → passed.

### Current status

All 13 commits currently on `tier-3-completion` (branch point through
`16f61fc`) now have a corresponding activity-log entry. Chunks 2 through
12 remain open.

## 2026-09-02: Tier-3 refactoring — Chunk 2.A: characterization tests for `write_analysis_results`

### Objective

Pin down the current, unmodified behavior of `write_analysis_results()` in
`python/run_anaFit.py` before extracting it into `run_manifest.py`, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 2.

### Pre-change state

`write_analysis_results()` already had three direct tests
(`test_write_analysis_results_writes_success_manifest`,
`test_write_analysis_results_records_masked_fit`,
`test_write_analysis_results_atomically_replaces_existing_manifest`),
covering the success payload, the masked-fit payload, and atomic
replacement of a pre-existing manifest. All three pass native `bool`/
`float` values for `masked`/`p_chi2`, so none of them exercises the
function body's explicit `bool(masked)` and `float(p_chi2)` coercion
calls — a real gap, since a value that is merely truthy (not already a
`bool`) or an int (not already a `float`) was never used to prove the
coercion is what actually produces the JSON-native type, as opposed to
the value simply already being the right type.

### Target function — inputs and outputs (as it exists today)

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `write_analysis_results(folder, p_chi2, masked, provenance)` | `folder: str`, `p_chi2: float`, `masked: bool`, `provenance: dict` | `str` (path to the written manifest) | atomically writes `<folder>/analysis_results.json` (schema v2) via a temp file + `os.replace`; deletes no pre-existing state itself (the atomic replace handles that) |

### Tests added

- `test_write_analysis_results_coerces_masked_and_p_chi2_to_json_native_types`
  — calls the real `write_analysis_results()` with `p_chi2=1` (an `int`)
  and `masked=1` (a truthy `int`, not a `bool`), then asserts the written-
  and-reread JSON payload has `p_chi2` as a Python `float` (`1.0`, via
  `isinstance`) and `masked` as the Python `bool` `True` (via `is True`
  and `isinstance`) — proving the function's `bool()`/`float()` calls are
  load-bearing, not redundant.

### What this commit does NOT do

No production file was modified. `git diff --stat -- python/run_anaFit.py`
was empty throughout this change — only `tests/test_run_anaFit.py` was
touched (one new test, 29 lines).

### Verification performed

- `python -m pytest tests/test_run_anaFit.py -v -k write_analysis_results`
  → 4 passed (the 3 existing tests plus the new coercion test), run
  against the unmodified `python/run_anaFit.py`.
- `python -m pytest tests/test_run_anaFit.py -v` → 50 passed (full-file
  regression check).
- `python scripts/quality_check.py --mode full` → 129 passed, 2
  deselected; ruff clean; black clean (10 files unchanged).
- `git diff --stat` → only `tests/test_run_anaFit.py` touched.
- `git diff --check` → passed (no whitespace errors).

### Compliance review (Section 8, Characterization checklist)

1. Chunk 2, Step A.
2. `git diff --stat` shows only `tests/test_run_anaFit.py` — zero
   production files touched.
3. The new test asserts real output values and their concrete Python
   types (`isinstance` checks), not merely "does not raise."
4. Tests were run against the unmodified target file before any
   production change; results reported in full above for review.
5. Human-verification checkpoint: presented to the user in session for
   confirmation before Step B's commit is made (recorded per Step B's own
   activity-log entry once given).

### Remaining open chunks

Chunk 2.B (extraction of `run_manifest.py`) and Chunks 3 through 12 are
open.

## 2026-09-02: Tier-3 refactoring — Chunk 2.B: extract `run_manifest.py`

### Objective

Move `write_analysis_results()`, characterized in Chunk 2.A (commit
`639b94d`), out of `python/run_anaFit.py` into a new
`python/run_manifest.py`, per `doc/TIER3_COMPLETION_PLAN.md` Chunk 2.

### What changed

- `python/run_manifest.py` created, containing `write_analysis_results()`
  moved verbatim from `python/run_anaFit.py` (identical body; only the
  `json`/`os` imports it actually needs were added at module top level).
- `python/run_anaFit.py`: the function definition removed; replaced with
  `from run_manifest import write_analysis_results` (flat sibling-import
  style, added directly below the existing
  `from run_execution import execute, execute_required` line). The single
  call site (inside `run_anaFit()`, assembling the success manifest) is
  unchanged — only the definition moved, not the call site.
- `tests/test_run_anaFit.py`: the `_example_analysis_provenance()` helper
  and all four `write_analysis_results` tests (the three original plus
  Chunk 2.A's new coercion test) removed.
- `tests/test_run_manifest.py` created: the four relocated tests plus
  their `_example_analysis_provenance()` helper, using the plain
  `from python import run_manifest` style (no `ROOT`/sibling stubbing
  needed — this module touches neither) and calling
  `run_manifest.write_analysis_results(...)` directly instead of through
  the `_load_run_anafit_module`/`monkeypatch` machinery, which these tests
  no longer need at all.
- `scripts/quality_check.py`: added `python/run_manifest.py` to
  `python_targets` and `tests/test_run_manifest.py` to `test_targets`.

### Test Relocation Rule: no exception needed this time

Unlike Chunk 1.B (where `execute_required`'s internal call to `execute`
broke the old `monkeypatch.setattr(module, "execute", ...)` target once
the two functions were split across module namespaces),
`write_analysis_results` does not call, or get called by, any other
relocated function — it is called directly by `run_anaFit()`, which stays
in `python/run_anaFit.py`. The two coordinator-level tests
(`test_run_anafit_writes_provenance_for_successful_unmasked_fit`,
`test_run_anafit_quicklimit_failure_prevents_success_manifest`) already
patch `write_analysis_results` via
`monkeypatch.setattr(module, "write_analysis_results", fake)`, where
`module` is the loaded `run_anaFit` object — since `run_anaFit()` still
resolves that name from its own module's globals (now bound there via the
new `from run_manifest import write_analysis_results` line), this
continues to intercept correctly with no change. Confirmed by running
both tests unchanged after the move: both pass. The four relocated tests'
own diff genuinely is import-statement-and-call-site-only, exactly as the
Test Relocation Rule's baseline describes.

### Confirm: no scientific behavior changed

`write_analysis_results()`'s body, including the `bool(masked)`/
`float(p_chi2)` coercion Chunk 2.A's new test specifically exercises, is
byte-for-byte identical to before the move. The one call site in
`run_anaFit()` is untouched.

### Verification performed

- `python -m pytest tests/test_run_manifest.py tests/test_run_anaFit.py -v`
  → 4 + 46 = 50 passed (same total as before the move: the four
  `write_analysis_results` tests moved out of `test_run_anaFit.py`, into
  `test_run_manifest.py`, net count unchanged).
- `grep -n "^def write_analysis_results" python/run_anaFit.py` → no
  output (definition fully removed).
- `python scripts/quality_check.py --mode full` → 129 passed, 2
  deselected; Ruff passed; Black passed (no reformatting needed); exit
  code 0.
- `git diff --check` → passed.
- No integration-gate rerun performed for this chunk — Chunk 2 is not one
  of the chunks Section 7 marks mandatory (4, 5, 8, and always before 12);
  `write_analysis_results` touches no branch condition or template logic,
  only relocates one already-isolated pure function.

### Compliance review (Section 8, Extraction checklist)

1. Chunk 2, Step B (this entry).
2. Step A is committed (`639b94d`) and referenced above.
3. No scientific constants, references, tolerances, dependency revisions,
   or canonical workflow arguments touched.
4. Relocated tests' diffs are import-statement-and-call-site-only, as
   confirmed above — no monkeypatch-target exception was needed this
   time.
5. The one relocated function is covered by its four relocated tests; no
   new functions were introduced this chunk.
6. Confirmed by grep: `run_anaFit.py` actually imports and never
   redefines `write_analysis_results`.
7. Only this chunk's five changed/new files were staged.
8. All required Section 7 gates ran and passed, output captured above.
9. `git diff --check` passed.
10. This activity-log entry appended (not a rewrite of any existing
    section).
11. Chunks 3 through 12 remain open, listed below.
12. No other branch's Tier 3 work was consulted.

### Remaining open chunks

Chunks 3 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open. Chunk 2
(both Step A and Step B) is complete and verified.
