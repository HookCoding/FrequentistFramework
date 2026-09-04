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

## 2026-09-02: Tier-3 refactoring — Chunk 3.A: characterization tests for the provenance pipeline

### Objective

Pin down the current, unmodified behavior of all seven functions in the
repository-discovery -> path-resolution -> hashing -> Git-revision ->
runtime-collection -> payload-assembly pipeline in `python/run_anaFit.py`
before extracting them into `run_provenance.py`, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 3.

### Pre-change state

All seven target functions already had direct tests (18 test functions,
19 cases counting the `warns_for_tracked_modifications` parametrization):
`get_repository_root` (2), `resolve_analysis_path` (3),
`calculate_file_sha256` (2), `build_file_provenance` (3),
`get_git_revision` (4 cases), `collect_scientific_runtime` (2),
`build_analysis_provenance` (2). All 19 pass unmodified.

Reviewing each function's contract against its tests found one real gap,
duplicated across two functions: both `resolve_analysis_path(path,
repository_root=None)` and `build_file_provenance(path,
repository_root=None)` have a documented `repository_root=None` fallback
branch (`if repository_root is None: repository_root =
get_repository_root()`) that no existing test exercises — every existing
test, and every real call site in `build_analysis_provenance` (confirmed
by `grep -n "resolve_analysis_path(\|build_file_provenance("
python/run_anaFit.py`), always passes `repository_root` explicitly. This
fallback is not currently reached in production, but it is part of each
function's documented signature, and both functions become independently
importable from `python/run_provenance.py` after this chunk, at which
point any future direct caller could reasonably omit it.

### Target functions — inputs and outputs (as they exist today)

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `get_repository_root()` | none | `Path` | raises `RuntimeError` if no `.git` found |
| `resolve_analysis_path(path, repository_root=None)` | `path: str`, optional `repository_root` | `Path` | raises `FileNotFoundError` if missing |
| `calculate_file_sha256(path)` | `path` | `str` (hex digest) | reads the file in chunks |
| `build_file_provenance(path, repository_root=None)` | as above | `dict {"path", "sha256"}` | — |
| `get_git_revision(repository_path)` | `repository_path` | `(str, bool)` (40-hex SHA, dirty flag) | runs `git rev-parse HEAD` + `git status --porcelain`; warns (does not fail) on a dirty tree |
| `collect_scientific_runtime()` | none | `dict {"python_version","python_executable","root_version"}` | requires `ROOT` importable |
| `build_analysis_provenance(...)` | 12 named arguments | full provenance `dict` | calls all of the above |

### Tests added

- `test_resolve_analysis_path_uses_get_repository_root_when_omitted` —
  patches `get_repository_root` to return a controlled `tmp_path`, calls
  `resolve_analysis_path("Input/data.root")` with `repository_root`
  omitted, asserts the file is resolved relative to the patched root —
  proving the fallback branch actually calls and uses
  `get_repository_root()`.
- `test_build_file_provenance_uses_get_repository_root_when_omitted` —
  same proof for `build_file_provenance`.

### What this commit does NOT do

No production file was modified. `git diff --stat -- python/run_anaFit.py`
was empty throughout this change — only `tests/test_run_anaFit.py` was
touched (two new tests, 43 lines).

### Verification performed

- `python -m pytest tests/test_run_anaFit.py -v -k "sha256 or
  git_revision or scientific_runtime or repository_root or
  resolve_analysis_path or build_file_provenance or
  build_analysis_provenance"` → 21 passed (19 pre-existing cases plus the
  2 new gap tests), run against the unmodified `python/run_anaFit.py`.
- `python -m pytest tests/test_run_anaFit.py -v` → 48 passed (full-file
  regression check).
- `python scripts/quality_check.py --mode full` → 131 passed, 2
  deselected; ruff clean; black clean (12 files unchanged).
- `git diff --stat` → only `tests/test_run_anaFit.py` touched.
- `git diff --check` → passed.

### Compliance review (Section 8, Characterization checklist)

1. Chunk 3, Step A.
2. `git diff --stat` shows only `tests/test_run_anaFit.py` — zero
   production files touched.
3. Both new tests assert a real resolved path / provenance dict produced
   from a controlled fixture, not merely "does not raise."
4. Tests were run against the unmodified target file before any
   production change; results reported in full above for review.
5. Human-verification checkpoint: presented to the user in session for
   confirmation before Step B's commit is made (recorded per Step B's own
   activity-log entry once given).

### Remaining open chunks

Chunk 3.B (extraction of `run_provenance.py`) and Chunks 4 through 12 are
open.

## 2026-09-02: Tier-3 refactoring — Chunk 3.B: extract `run_provenance.py`

### Objective

Move all seven functions of the provenance pipeline, characterized in
Chunk 3.A (commit `640e6f7`), out of `python/run_anaFit.py` into a new
`python/run_provenance.py`, per `doc/TIER3_COMPLETION_PLAN.md` Chunk 3.
This is the largest extraction by line count so far (227 lines removed
from the coordinator).

### What changed

- `python/run_provenance.py` created, containing `get_repository_root`,
  `resolve_analysis_path`, `calculate_file_sha256`, `build_file_provenance`,
  `get_git_revision`, `collect_scientific_runtime`, and
  `build_analysis_provenance`, moved verbatim, **with the one narrow
  exception the plan explicitly sanctions**: `get_repository_root()` now
  computes its base path via `repo_utils.find_repo_root()` (flat import:
  `from repo_utils import find_repo_root`) instead of its own independent
  `Path(__file__).resolve().parents[1]`, then layers the same `.git`
  existence check and `RuntimeError` on top, unchanged. Both expressions
  were already identical in value (both files live directly under
  `python/`), so this removes a real duplication with no behavior change
  to the function's signature, return value, or exception. Formatted with
  `python -m black python/run_provenance.py` once added to the Tier 2
  target list (one whitespace-only change: two adjacent string literals
  in `get_repository_root`'s error message joined onto one physical line
  — no logic change, same message text).
- `collect_scientific_runtime()`'s `import ROOT` moved from
  `run_anaFit.py`'s module top level to inside the function body itself
  (Section 4.2's import-placement table) — it is the only one of the
  seven functions that touches ROOT at all, so every other function in
  the new module is now plainly importable with zero stubbing.
- `python/run_anaFit.py`: all seven function definitions removed;
  replaced with `from run_provenance import build_analysis_provenance`
  (flat sibling-import style). The one call site inside `run_anaFit()`
  is unchanged. File size: 847 -> 622 lines (225 lines removed net: 226
  deleted for the seven function bodies and their spacing, plus 1 added
  for the new import line).
- `tests/test_run_provenance.py` created: the 18 relocated test
  functions (19 cases) plus Chunk 3.A's 2 new gap tests (20 functions, 21
  cases total), using the plain `from python import run_provenance` style.
- `scripts/quality_check.py`: added `python/run_provenance.py` to
  `python_targets` and `tests/test_run_provenance.py` to `test_targets`.

### A real infrastructure gap the acceptance check caught

Running the acceptance check immediately after writing
`tests/test_run_provenance.py` failed at collection:
`ModuleNotFoundError: No module named 'repo_utils'`, raised from
`run_provenance.py`'s own `from repo_utils import find_repo_root` line.
Cause: `from python import run_provenance` (the plain, no-stubbing import
style established in Chunks 1-2) only works because `pyproject.toml`'s
`pythonpath = ["."]` puts the **repository root** on `sys.path`, making
`python` importable as a namespace package — it never puts `python/`
itself on `sys.path`. Chunks 1 and 2's new modules (`run_execution.py`,
`run_manifest.py`) never hit this because neither imports another sibling
module; `run_provenance.py` is the first new module to import a sibling
(`repo_utils`) using the same flat style production requires. In
production this is not a problem — `python/` is `sys.path[0]` for the
whole process once `run_anaFit.py` is invoked directly, so `run_provenance.py`'s
own flat import resolves the same way `run_anaFit.py`'s already-flat
sibling imports do. The gap is purely in how the *test* loads the module.

Fix: added `"python"` to `pyproject.toml`'s `pythonpath` list
(`pythonpath = [".", "python"]`), so `python/` is on `sys.path` for every
test in the suite, alongside the repository root. This is a one-line,
general, forward-looking fix rather than a per-file `sys.path` hack in
`tests/test_run_provenance.py` alone — the plan's own Chunk 6 already
anticipates `run_fit.py` needing flat imports from `run_execution.py`
(the same pattern), so this would have recurred. Re-ran the full
acceptance check after the fix: collection succeeded, all tests passed.

### Two more Test Relocation Rule exceptions, both anticipated in Chunk 3.A

1. `test_get_repository_root_rejects_missing_git_directory` — the
   original faked a missing-`.git` directory by patching the loaded
   module's `__file__` attribute, which only worked because
   `get_repository_root()` used to compute `Path(__file__)` against its
   *own* module. Once it delegates to `find_repo_root()` (now living in
   `repo_utils.py`, with its own separate `__file__`), that patch target
   no longer reaches anything. Rewritten to patch
   `run_provenance.find_repo_root` directly (as looked up in
   `run_provenance`'s own namespace) — same `RuntimeError`/message
   asserted, simpler fixture (no longer needs to fabricate a nested
   `python/run_anaFit.py` file, just a directory without `.git`).
2. `test_collect_scientific_runtime_records_python_and_root` and
   `test_collect_scientific_runtime_rejects_missing_root_version` — the
   originals patched `module.ROOT.gROOT`, relying on `run_anaFit.py`'s
   top-level `import ROOT`. With the import deferred inside the function,
   there is no module-level `run_provenance.ROOT` attribute to patch —
   the function does its own local `import ROOT` on every call. Rewritten
   to install a fake module directly via
   `monkeypatch.setitem(sys.modules, "ROOT", fake_root_module)` before
   calling the function, which is exactly what the function's own local
   `import ROOT` statement finds (Python checks `sys.modules` before
   doing any real import work). Same assertions, same expected values.

Neither is a hidden behavior change to the function under test — both are
necessary, transparent consequences of where the code and its ROOT
dependency now live, exactly as already documented for Chunk 1.B's
`execute`/`execute_required` monkeypatch-target change.

### No exception needed for the other four relocated functions' cross-calls

`build_analysis_provenance`'s tests patch `get_repository_root`,
`get_git_revision`, `collect_scientific_runtime`, and
`build_file_provenance` via `monkeypatch.setattr(run_provenance, ...)` —
mechanically the same pattern as before (`module.X` -> `run_provenance.X`),
since all seven functions moved into the *same* new module together and
call each other exactly as they did inside `run_anaFit.py`. Confirmed by
running both `build_analysis_provenance` tests unchanged in logic after
the move: both pass. Likewise, the two coordinator-level tests in
`tests/test_run_anaFit.py` that patch `module.build_analysis_provenance`
continue to work unchanged, for the same reason as Chunk 2.B's
`write_analysis_results`: `run_anaFit()` didn't move, and still resolves
that name from its own module globals (now bound there via the new
`from run_provenance import build_analysis_provenance` line).

### Deliberately deferred: three now-dead imports in `run_anaFit.py`

`hashlib` and `platform` (previously used only by `calculate_file_sha256`
and `collect_scientific_runtime`) and `subprocess` (previously used only
by `get_git_revision`; its one other appearance in the file is a comment,
not code — confirmed by `grep -n "\bsubprocess\." python/run_anaFit.py`)
are now unused in `run_anaFit.py`. Left in place deliberately rather than
removed as part of this chunk: `run_anaFit.py` is not yet registered in
`scripts/quality_check.py` (so ruff's unused-import check does not run
against it today), and Chunk 8 ("Coordinator slimming and
dependency-direction verification") explicitly exists to re-read the
coordinator top-to-bottom, register it with the quality gate, and fix
whatever ruff then finds — bundling this cleanup into Chunk 3.B now would
widen this chunk's diff beyond "move these seven functions" for a
one-chunk-early version of Chunk 8's own stated job. Flagged here so
Chunk 8 does not need to rediscover it.

### Confirm: no scientific behavior changed

Every function's body is byte-for-byte identical to before the move
(aside from the one Black whitespace-only reformat noted above and the
sanctioned `find_repo_root()` substitution, which is value-identical).
Ran the real, authoritative J100/J50 integration gate as supplementary
verification (not strictly mandatory for Chunk 3 per Section 7, but this
chunk changes the actual code path that computes `repository_commit` for
`analysis_results.json`, so extra confidence was warranted, matching the
same judgment call made for Chunk 1.B): both workflows matched the frozen
reference exactly.

### Verification performed

- `python -m pytest tests/test_run_provenance.py tests/test_run_anaFit.py -v`
  → 48 passed (21 cases in `test_run_provenance.py` + 27 remaining in
  `test_run_anaFit.py` = 48, matching the pre-move total of 48 exactly).
- `grep -n "^def get_repository_root\|^def resolve_analysis_path\|^def calculate_file_sha256\|^def build_file_provenance\|^def get_git_revision\|^def collect_scientific_runtime\|^def build_analysis_provenance" python/run_anaFit.py`
  → no output (all seven definitions fully removed).
- `python scripts/quality_check.py --mode full` → 131 passed, 2
  deselected; ruff clean; black clean (14 files unchanged after the one
  reformat above); exit code 0.
- `python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`
  → 2 passed, 11 deselected (run because the new module now imports from
  `repo_utils.py`).
- `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
  → 1 passed in 181.04s — the real J100/J50 authoritative pipeline run,
  matched against the frozen reference exactly.
- `git diff --check` → passed.

### Compliance review (Section 8, Extraction checklist)

1. Chunk 3, Step B (this entry).
2. Step A is committed (`640e6f7`) and referenced above.
3. No scientific constants, references, tolerances, dependency revisions,
   or canonical workflow arguments touched.
4. Relocated tests' diffs are import-statement-and-call-site-only for the
   17 functions with no cross-module dependency change; two genuine
   exceptions (`find_repo_root` patch target, `sys.modules["ROOT"]`
   stubbing) documented above as necessary consequences, not hidden
   behavior changes.
5. All seven relocated functions are covered by their relocated tests; no
   new functions were introduced this chunk.
6. Confirmed by grep: `run_anaFit.py` actually imports and never
   redefines any of the seven functions.
7. Only this chunk's six changed/new files were staged (`pyproject.toml`,
   `python/run_anaFit.py`, `python/run_provenance.py`,
   `scripts/quality_check.py`, `tests/test_run_anaFit.py`,
   `tests/test_run_provenance.py`).
8. All required Section 7 gates ran and passed, plus two supplementary
   gates (dependency-facing, authoritative integration), output captured
   above.
9. `git diff --check` passed.
10. This activity-log entry appended (not a rewrite of any existing
    section).
11. Chunks 4 through 12 remain open, listed below.
12. No other branch's Tier 3 work was consulted.

### Remaining open chunks

Chunks 4 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open. Chunk 3
(both Step A and Step B) is complete and verified.

## 2026-09-02: Tier-3 refactoring — Chunk 4.A: characterization tests for `load_bumphunter_results`/`run_bumphunter`

### Objective

Pin down the current, unmodified behavior of `load_bumphunter_results()`
and `run_bumphunter()` in `python/run_anaFit.py` before extracting them
into `run_masking.py`, per `doc/TIER3_COMPLETION_PLAN.md` Chunk 4.
`should_mask()` is a new function with no prior behavior to characterize
(per the plan's own explicit carve-out), so it has no Step A tests —
those are written fresh in Step B under guardrail 4.

### Pre-change state

Both target functions already had eight direct tests (ten cases counting
`rejects_invalid_mask_limits`'s three-way parametrization). All ten pass
unmodified. Reviewing `load_bumphunter_results()`'s four validation
branches against its four existing tests found two branches with no
coverage at all: the `if not isinstance(results, dict)` check (every
fixture is already a dict) and the `BlindRange` non-empty-string check
(every fixture already uses `"500,600"` or `"stale"`).

### A discrepancy between the plan's rationale and the actual code, found while re-reading `run_anaFit()`

The plan's Chunk 4 rationale states "both call sites already use the
exact same `>` comparison," citing `if pval_global > maskthreshold` and
`if pval_masked > maskthreshold`. Re-reading the coordinator directly
found a **third** occurrence of the identical `pval_global > maskthreshold`
sub-expression, reused inside a compound condition at what is currently
line 530: `if dolimit and dosignal and pval_global > maskthreshold:`
(gates whether `quickLimit` runs). This is exactly the kind of
duplication-that-drifts-unnoticed the chunk exists to eliminate, and
leaving it as a bare `>` comparison while the other two sites call
`should_mask()` would defeat the point. Step B will replace all three
occurrences, not the two the plan's rationale text named -
`test_run_anafit_quicklimit_failure_prevents_success_manifest` already
exercises this exact branch (`dosignal=True, dolimit=True, pval_global=0.25`
mocked, `maskthreshold=0.01`), so it doubles as the regression check for
this third call site's rewrite with no new test needed.

### A second Test Relocation Rule exception anticipated for Step B

`run_bumphunter()` calls `execute_required(...)`, which lives in
`run_execution.py`, a different module from where `run_bumphunter` is
moving (`run_masking.py`). Its four tests currently patch
`module.execute_required` (`module` = the loaded `run_anaFit` object) -
this only works today because both functions are defined in the same
module. Once `run_bumphunter` moves, `execute_required` will be looked up
in `run_masking`'s own namespace (via its own `from run_execution import
execute_required`), so the relocated tests will need to patch
`run_masking.execute_required` directly - the same necessary-consequence
pattern already documented for Chunk 1.B's `execute`/`execute_required`
split and Chunk 3.B's `find_repo_root`/`ROOT` cases.

### Target functions — inputs and outputs (as they exist today)

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `load_bumphunter_results(results_file)` | `results_file: str` | `dict {"BlindRange","MaskMin","MaskMax"}` | raises `ValueError` on malformed input |
| `run_bumphunter(postfitfile, folder)` | `postfitfile: str`, `folder: str` | same shape as above | deletes stale `BHresults.json`; runs the BumpHunter subprocess; raises `RuntimeError` on failure |

### Tests added

- `test_load_bumphunter_results_rejects_non_dict_payload` — a JSON array
  instead of an object, asserts `"must be a JSON object"`.
- `test_load_bumphunter_results_rejects_invalid_blind_range` (parametrized
  `["", "   "]`) — asserts `"BlindRange must be a non-empty string"`.

### What this commit does NOT do

No production file was modified. `git diff --stat -- python/run_anaFit.py`
was empty throughout this change — only `tests/test_run_anaFit.py` was
touched (two new tests, 38 lines).

### Verification performed

- `python -m pytest tests/test_run_anaFit.py -v -k "load_bumphunter_results
  or run_bumphunter"` → 13 passed (10 pre-existing cases plus the 3 new
  gap-test cases), run against the unmodified `python/run_anaFit.py`.
- `python -m pytest tests/test_run_anaFit.py -v` → 30 passed (full-file
  regression check).
- `python scripts/quality_check.py --mode full` → 134 passed, 2
  deselected; ruff clean; black clean (14 files unchanged).
- `git diff --stat` → only `tests/test_run_anaFit.py` touched.
- `git diff --check` → passed.

### Compliance review (Section 8, Characterization checklist)

1. Chunk 4, Step A.
2. `git diff --stat` shows only `tests/test_run_anaFit.py` — zero
   production files touched.
3. Both new tests assert the real, specific `ValueError` message for
   their branch, not merely "does not raise."
4. Tests were run against the unmodified target file before any
   production change; results reported in full above for review.
5. Human-verification checkpoint: presented to the user in session for
   confirmation before Step B's commit is made (recorded per Step B's own
   activity-log entry once given).

### Remaining open chunks

Chunk 4.B (extraction of `run_masking.py`) and Chunks 5 through 12 are
open.

## 2026-09-02: Tier-3 refactoring — Chunk 4.B: extract `run_masking.py`

### Objective

Move `load_bumphunter_results()` and `run_bumphunter()`, characterized in
Chunk 4.A (commit `4930636`), out of `python/run_anaFit.py` into a new
`python/run_masking.py`, add the new `should_mask(p_value, threshold)`
predicate, and replace all three coordinator-level `> maskthreshold`
comparisons with calls to it, per `doc/TIER3_COMPLETION_PLAN.md` Chunk 4.

### What changed

- `python/run_masking.py` created, containing `load_bumphunter_results()`
  and `run_bumphunter()` moved verbatim, plus the new
  `should_mask(p_value, threshold)`, returning `p_value <= threshold` -
  `True` exactly when the coordinator's original `if pval_global >
  maskthreshold` branch would **not** be taken, matching its existing `>`
  convention precisely.
- `python/run_anaFit.py`: both function definitions removed; replaced
  with `from run_masking import run_bumphunter, should_mask` (flat
  sibling-import style; `load_bumphunter_results` is not imported here -
  it is called only internally by `run_bumphunter`, confirmed by
  `grep -n "load_bumphunter_results(\|run_bumphunter(" python/run_anaFit.py`
  before the move). All **three** `> maskthreshold` call sites rewritten,
  per Chunk 4.A's finding:
  - `if pval_global > maskthreshold` -> `if not should_mask(pval_global, maskthreshold)`
  - `if pval_masked > maskthreshold` -> `if not should_mask(pval_masked, maskthreshold)`
  - `if dolimit and dosignal and pval_global > maskthreshold` -> `if dolimit and dosignal and not should_mask(pval_global, maskthreshold)`
  Each preserves the exact original control flow (`p > t` is logically
  `not (p <= t)`, i.e. `not should_mask(p, t)`).
- `tests/test_run_masking.py` created: the ten relocated test functions
  (13 cases) plus the new `test_should_mask_matches_coordinator_convention_at_exact_threshold`
  (parametrized: exact threshold, clearly below, clearly above), using
  the plain `from python import run_masking` style.
- `scripts/quality_check.py`: added `python/run_masking.py` to
  `python_targets` and `tests/test_run_masking.py` to `test_targets`.

### The anticipated Test Relocation Rule exception, confirmed

`run_bumphunter`'s four tests patch `execute_required` - as flagged in
Chunk 4.A, this now targets `run_masking.execute_required` (the name
bound in `run_masking`'s own namespace via its own `from run_execution
import execute_required`), not the old `module.execute_required`. Same
pattern as Chunk 1.B and Chunk 3.B: a necessary consequence of
`execute_required` living in a different module from where it is called,
not a hidden behavior change. `run_bumphunter`'s own intra-module call to
`load_bumphunter_results` needed no such change - both moved into
`run_masking.py` together.

### A second dead-import discovery, fixed immediately this time (unlike Chunk 3.B's deferral)

`python scripts/quality_check.py --mode full` failed ruff (`F401 'json'
imported but unused`) on `tests/test_run_anaFit.py`: relocating all six
`load_bumphunter_results` tests removed every remaining use of `json.` in
that file. Unlike Chunk 3.B's `hashlib`/`platform`/`subprocess` dead
imports in `python/run_anaFit.py` (deliberately deferred to Chunk 8,
because that file is not yet registered with the quality gate at all),
`tests/test_run_anaFit.py` **is already** in `test_targets` - ruff runs
against it on every gate today, so this was not a "some later chunk will
clean it up" situation but a real, immediate gate failure caused directly
by this chunk's own test relocation. Fixed by removing the now-unused
`import json` line. Re-ran the full gate afterward: clean.

### Confirm: scientific behavior preserved, including the newly-discovered third call site

Both `load_bumphunter_results()` and `run_bumphunter()`'s bodies are
byte-for-byte identical to before the move. The three rewritten
comparisons are logically equivalent to the originals (confirmed by
inspection, not just by test result). Ran the full targeted acceptance
check plus the **mandatory** integration gate (per Section 7, this chunk
changes real branch conditions):
`test_run_anafit_quicklimit_failure_prevents_success_manifest`
(`dosignal=True, dolimit=True, pval_global=0.25 mocked, maskthreshold=0.01`)
passed unchanged, directly exercising the third call site's rewrite. The
real, authoritative J100/J50 pipeline also passed, matching the frozen
reference exactly - both canonical workflows still take the unmasked
accept path through all three rewritten conditions.

### Verification performed

- `grep -n "maskthreshold" python/run_anaFit.py` → confirms all three
  comparisons now call `should_mask()`; the other five matches are the
  argparse definition, kwarg passthroughs, and a print statement,
  unaffected.
- `python -m pytest tests/test_run_masking.py tests/test_run_anaFit.py -v`
  → 33 passed (16 cases in `test_run_masking.py` + 17 remaining in
  `test_run_anaFit.py` = 33, matching the pre-move total of 30 plus the 3
  new `should_mask` cases exactly).
- `python scripts/quality_check.py --mode full` → 137 passed, 2
  deselected; ruff clean (after the `json` import fix); black clean (16
  files unchanged); exit code 0.
- `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
  → 1 passed in 150.66s - the real J100/J50 authoritative pipeline run,
  **mandatory** for this chunk per Section 7, matched against the frozen
  reference exactly.
- `git diff --check` → passed.

### Compliance review (Section 8, Extraction checklist)

1. Chunk 4, Step B (this entry).
2. Step A is committed (`4930636`) and referenced above.
3. No scientific constants, references, tolerances, dependency revisions,
   or canonical workflow arguments touched. The three rewritten branch
   conditions are logically equivalent to the originals, verified by both
   unit and integration tests.
4. Relocated tests' diffs are import-statement-and-call-site-only except
   the one documented, anticipated `execute_required` patch-target
   change.
5. `should_mask()` (the one new function) is covered by three cases
   (exact threshold, clearly below, clearly above), per the plan's
   explicit requirement.
6. Confirmed by grep: `run_anaFit.py` actually imports and never
   redefines `run_bumphunter`/`should_mask`; all three comparisons now
   call `should_mask()`.
7. Only this chunk's five changed/new files were staged.
8. All required Section 7 gates ran and passed, including the mandatory
   integration gate, output captured above.
9. `git diff --check` passed.
10. This activity-log entry appended (not a rewrite of any existing
    section).
11. Chunks 5 through 12 remain open, listed below.
12. No other branch's Tier 3 work was consulted.

### Remaining open chunks

Chunks 5 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open. Chunk 4
(both Step A and Step B) is complete and verified.

## 2026-09-02: Tier-3 refactoring — Chunk 5.A: first-ever characterization tests for the templating/prefit block

### Objective

Write the **first direct tests ever** for `replaceinfile()` and the
~150-line inline templating/prefit block inside `run_anaFit()`, before
extracting them into `python/run_templates.py`, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 5. Per the plan's own framing, this
is a genuine characterization step, not a formality: this logic has never
been pinned down at the unit level before, only indirectly through the
full J100/J50 integration gate.

### Finalizing `prepare_run_templates(...)`'s exact signature (the plan's own draft table needed correction)

The plan's Chunk 5 module table listed a draft input list explicitly
flagged "finalize the exact set while reading the current block." Doing
that reading directly against the source (not the draft) found:

- `nbkg` and `nsig` are **missing from the plan's draft input list** but
  are genuinely required: `nbkg` is read and conditionally reassigned
  (by the `doprefit` branch) before being substituted into the category
  file; `nsig` is read as a substitution value. Both must be parameters.
- `nbkg`'s prefit-reassignment does **not** need to be returned to the
  coordinator: `grep -n "\bnbkg\b" python/run_anaFit.py` confirms it is
  never read again after the block's own final `replaceinfile` call.
- `signame` never changes inside the block - it is a pass-through
  substitution value, not something the block "derives." No output
  needed for it, contrary to the draft table's "any poi/signame derived
  values" phrasing.
- `poi` is decided by a **separate**, unrelated piece of coordinator
  logic (`if dosignal: poi = ... else: poi = None`) immediately after the
  block, which touches no template file and calls neither
  `replaceinfile` nor `PreFitter`. It is out of this chunk's scope
  (Chunk 6's concern, since it only feeds `build_fit_extract`), not part
  of `prepare_run_templates`.
- `tmptopfile`, `tmpcategoryfile`, `xml_categoryfile`, and `xml_wsfile`
  **are** read again after the block (in the masking branch, to stage the
  masked-refit XML copies) - confirmed by
  `grep -n "tmpcategoryfile\|xml_categoryfile\|xml_wsfile" python/run_anaFit.py`.
  These four must be the function's return value.
- `covariancedict` is a `run_anaFit()` parameter but is **entirely
  unused** in live code today - every reference to it is inside a
  commented-out block. It will not be threaded into
  `prepare_run_templates` in Step B; there is no live behavior depending
  on it.

Final signature for Step B:
`prepare_run_templates(folder, topfile, categoryfile, backgroundfile,
signalfile, signame, wsfile, sigmean, sigwidth, datafile, datahist,
rangelow, rangehigh, nbkg, nsig, doprefit, systdict)` returning
`(tmptopfile, tmpcategoryfile, xml_categoryfile, xml_wsfile)`.

### A real, previously-undocumented quirk found while hand-verifying the prefit test

Writing `test_run_anafit_prefit_seeds_background_file_from_fitted_parameters`
first assumed the PAR-substitution loop replaces each whole `[PARn,lo,hi]`
range annotation with the fitted value. Running the test against the
unmodified file disproved this: the loop is a plain
`replaceinfile(tmpbackgroundfile, [("PAR%d" % (i+1), str(initPars[i]))])`
per parameter - a naive substring/regex swap of the literal text `PARn`,
not a replacement of the surrounding annotation. The `[...,lo,hi]`
brackets survive in the output file with only the `PARn` token inside
them replaced (e.g. `[PAR1,-5,5]` becomes `[11.0,-5,5]`, not `11.0`) -
and because `replaceinfile` operates over the whole file text, this
happens even inside HTML/XML comments (`<!-- ... [PAR1,-99,99] ... -->`
becomes `<!-- ... [11.0,-99,99] ... -->`). This is real, current,
unrelated-to-doprefit-testing-before-now behavior; the test now pins it
down exactly as observed rather than as originally assumed. Step B must
preserve it exactly - it is exactly the kind of thing an implementer
"fixes" by accident while moving code.

### Target functions — inputs and outputs

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `replaceinfile(f, old_new_list)` | `f: str`, `old_new_list: list[tuple[str,str]]` | `None` | rewrites `f` in place, applying each `re.sub` in order (substitutions chain against the already-modified text) |
| `prepare_run_templates(...)` (new in Step B) | see finalized signature above | `(tmptopfile, tmpcategoryfile, xml_categoryfile, xml_wsfile)` | copies/edits XML template files on disk; runs `PreFitter` when `doprefit` is set |

### Tests added (all new — this block had zero direct tests before)

- `test_replaceinfile_applies_ordered_regex_substitutions` — chains
  `PLACEHOLDER_A -> PLACEHOLDER_B -> final_value` to prove substitutions
  apply in order against the already-modified text, not independently
  against the original.
- `test_run_anafit_stages_templates_for_a_representative_case` —
  `doprefit=False`, `signalfile=None`; asserts the exact generated
  `tmptopfile`/`tmpcategoryfile` content, including that the
  `SIGNALFILE` placeholder is substituted with a computed path even
  though no signal file was provided (confirmed real: `tmpsignalfile`/
  `xml_signalfile` are computed unconditionally in production).
- `test_run_anafit_prefit_seeds_background_file_from_fitted_parameters` —
  `doprefit=True`, a background file name containing "six" (nPars=6), a
  background file with two real `[PARn,lo,hi]` `<ModelItem>` lines (one
  commented out, correctly excluded from range parsing) and a
  `FakePreFitter` test double; asserts the exact `parRangeLow`/
  `parRangeHigh` passed to `PreFitter`, the exact seeded background-file
  content (including the quirk above), and the exact `NBKG` string
  format derived from the fitted value.
- `test_run_anafit_prefit_npars_detection_matching_both_three_and_four_resolves_to_four` —
  the plan's required regression test: a background file path containing
  both `"three"` and `"four"`; asserts `PreFitter` is constructed with
  `nPars=4`, pinning down the standalone-`if`-then-separate-`elif`-chain
  quirk exactly as it exists today.
- `test_run_anafit_stages_signal_template_with_systematic_placeholders` —
  a populated `systdict`; asserts the exact seeded signal-file content,
  including both named systematic sources substituted and an unlisted
  `[MAG_SCALE_UNLISTED]` placeholder caught by the catch-all pattern and
  replaced with `[0]`.

### What this commit does NOT do

No production file was modified. `git diff --stat -- python/run_anaFit.py`
was empty throughout this change — only `tests/test_run_anaFit.py` was
touched (five new tests, 402 lines).

### Verification performed

- `python -m pytest tests/test_run_anaFit.py -v -k "replaceinfile or
  stages_templates or prefit_seeds or npars_detection or
  systematic_placeholders"` → 5 passed, run against the unmodified
  `python/run_anaFit.py`. One assertion (the PAR-substitution content)
  was corrected after the first run disproved the initial hand-derived
  expectation, per the quirk documented above — a real characterization
  correction, not a retrofit to make a test pass.
- `python -m pytest tests/test_run_anaFit.py -v` → 22 passed (full-file
  regression check).
- `python scripts/quality_check.py --mode full` → 142 passed, 2
  deselected; ruff clean; black clean after one whitespace/quote-style
  reformat (`python -m black tests/test_run_anaFit.py`, no logic change).
- `git diff --stat` → only `tests/test_run_anaFit.py` touched.
- `git diff --check` → passed.

### Compliance review (Section 8, Characterization checklist)

1. Chunk 5, Step A.
2. `git diff --stat` shows only `tests/test_run_anaFit.py` — zero
   production files touched.
3. Every new test asserts exact generated file content or exact
   `PreFitter` constructor arguments, not merely "does not raise."
4. Tests were run against the unmodified target file before any
   production change; results (including the corrected assertion)
   reported in full above for review.
5. Human-verification checkpoint: presented to the user in session for
   confirmation before Step B's commit is made, with the extra weight the
   plan calls for given these are first-ever tests, not a relocation —
   recorded per Step B's own activity-log entry once given.

### Remaining open chunks

Chunk 5.B (extraction and internal decomposition of `run_templates.py`)
and Chunks 6 through 12 are open.

## 2026-09-02: Tier-3 refactoring — Chunk 5.B: extract and decompose `run_templates.py`

### Objective

Move `replaceinfile()` and the ~150-line inline templating/prefit block,
characterized in Chunk 5.A (commit `8d614ee`), out of `run_anaFit()` into
a new `python/run_templates.py`, decomposed into the two private helpers
the plan names plus one public entry point (not moved intact as one
function), per `doc/TIER3_COMPLETION_PLAN.md` Chunk 5. This is the
biggest and, per the plan's own framing, riskiest extraction so far
(199 lines net removed from the coordinator).

### What changed

- `python/run_templates.py` created with three functions:
  - `replaceinfile(f, old_new_list)`, moved verbatim.
  - `_seed_prefit_parameters(datafile, datahist, rangelow, rangehigh,
    backgroundfile, tmpbackgroundfile, nbkg)` (private) — the `doprefit`
    sub-block: the `nPars` if/then-separate-elif-chain detection (copied
    exactly, per Chunk 5.A's regression test), the `[PARn,lo,hi]`
    range-parsing regex, the `PreFitter` call, and the background-file
    PAR substitution loop. Returns the updated `nbkg`. `from PreFit
    import PreFitter` is deferred inside this function (Section 4.2's
    import-placement rule) — it is the only place in the module that
    touches a ROOT-facing tool.
  - `_stage_xml_templates(...)` (private) — everything else: the `.dtd`
    symlink, path computation, file copies, top/category-file
    substitution, calling `_seed_prefit_parameters` when
    `backgroundfile and doprefit`, the final category-file substitution,
    and the signal-file substitution (including the `systdict`-driven
    placeholders and the catch-all). Returns `(tmptopfile,
    tmpcategoryfile, xml_categoryfile, xml_wsfile)` — the finalized
    signature from Chunk 5.A's analysis.
  - `prepare_run_templates(...)` (public) — a thin entry point that calls
    `_stage_xml_templates(...)` and returns its result. This is the one
    public function `run_anaFit()` now calls.
  - All original comments preserved verbatim, including the dead,
    commented-out alternative implementations (the two alternate `.dtd`
    symlink commands, the commented `replaceinfile(tmpsignalfile,
    [SIGMEAN, SIGWIDTH])` block, and the entire commented-out
    `covariancedict` block) - dropping inert comments was judged an
    unnecessary editorial decision for a chunk whose job is to move code,
    not curate it.
- `python/run_anaFit.py`: `replaceinfile()`'s definition and the inline
  block both removed; replaced with `from run_templates import
  prepare_run_templates, replaceinfile` (flat sibling-import style) and a
  single call to `prepare_run_templates(...)`, unpacking its four return
  values. `replaceinfile` itself is still imported (not just
  `prepare_run_templates`) because `run_anaFit()`'s masking branch calls
  it directly for the masked-refit XML copies (`tmptopfilemasked`/
  `tmpcategoryfilemasked`) - confirmed by `grep -n "replaceinfile("
  python/run_anaFit.py` before editing, which is why this wasn't
  mentioned in Chunk 5.A's signature analysis (that only covered the
  block being moved, not this separate downstream call site).
- `tests/test_run_templates.py` created with the 5 tests from Chunk 5.A,
  **rewritten to call `run_templates.prepare_run_templates(...)` and
  `run_templates.replaceinfile(...)` directly** rather than through
  `run_anaFit()` end-to-end (see below) - all assertions and expected
  values are unchanged from Chunk 5.A, only what gets called changed.
- `scripts/quality_check.py`: added `python/run_templates.py` to
  `python_targets` and `tests/test_run_templates.py` to `test_targets`.

### Necessary test-relocation adaptation: direct calls, not `run_anaFit()` end-to-end

Chunk 5.A's tests called `module.run_anaFit(...)` end-to-end (mocking
away `build_fit_extract`/`build_analysis_provenance`/
`write_analysis_results`) because no standalone function existed yet to
call directly - that was the whole point of Chunk 5.A being a genuine
first-ever characterization, not a relocation. Now that
`prepare_run_templates()` exists as a real, directly-callable function,
the plan's own text says the relocated tests should scope ROOT/PreFitter
stubbing "only to the `_seed_prefit_parameters` calls (the rest of the
module needs none)" - this is only true if the tests call into
`run_templates.py` directly, not through `run_anaFit.py` (which still
does a top-level `import ROOT` regardless of what `run_templates.py`
itself needs). Rewriting the 4 end-to-end tests as direct
`prepare_run_templates(...)` calls confirmed this: none of the mocking
of `build_fit_extract`/`build_analysis_provenance`/`write_analysis_results`
is needed anymore, and only the two `doprefit=True` tests need any
stubbing at all - not `sys.modules["ROOT"]`, but
`sys.modules["PreFit"]` (a fake module with a fake `PreFitter` class),
since `_seed_prefit_parameters`'s `from PreFit import PreFitter` is
function-local and resolves via `sys.modules` on every call, exactly
like Chunk 3.B's `collect_scientific_runtime`/`ROOT` case. All five
tests' assertions and expected values are byte-for-byte the same as
Chunk 5.A wrote them - only the call mechanism changed, confirmed by
running them against the moved code and getting identical results
(including the quirky PAR-substitution content).

### A third dead import, deferred like Chunk 3.B's (not fixed like Chunk 4.B's)

`grep -n "\bre\." python/run_anaFit.py` after the move returns nothing:
`re` (part of the combined `import os,sys,re,argparse,subprocess,shutil`
line) is now unused - both of its uses (`replaceinfile`'s `re.sub` and
the prefit block's `re.findall`) moved with the code. Unlike Chunk 4.B's
`tests/test_run_anaFit.py` `json` import (a live gate failure, fixed
immediately because that file is already quality-gated), `re` joins
`hashlib`/`platform`/`subprocess` in `run_anaFit.py`, which is still not
registered in `scripts/quality_check.py` - left in place for Chunk 8's
coordinator-slimming pass, per the same reasoning as Chunk 3.B.

### Confirm: no scientific behavior changed

Every moved line of logic is byte-for-byte identical (aside from the
ruff/black-driven fixes below, all verified whitespace/syntax-only). Ran
the **mandatory** integration gate (per Section 7, explicitly required
for this chunk): the real, authoritative J100/J50 pipeline passed,
matching the frozen reference exactly - the strongest available
confirmation that the decomposition did not change the generated XML in
any way that matters to the fit.

### Ruff/Black fixes required to register the new file (mechanical, zero behavior change)

Registering `run_templates.py` in `python_targets` surfaced pre-existing
issues in the moved code that were never checked while it lived inside
the un-gated `run_anaFit.py`:
- `E722` bare `except:` in `replaceinfile` -> `except Exception:` (does
  not change what the `try` block can raise: `re.sub` never raises
  `SystemExit`/`KeyboardInterrupt`).
- `E713`/`E711` -> `"<!--" not in line` and `systdict is not None`,
  syntactically equivalent rewrites.
- `W605` (9 instances) -> the `[PARn,...]`-parsing and `MAG_*`
  substitution regex patterns changed from plain to raw string literals
  (`r"..."`); the resulting string values are byte-identical either way
  (`\[`, `\d`, `\-` are not valid Python escapes in a plain string, so
  Python already treated them as literal backslash+character - `r"..."`
  just stops the interpreter's `SyntaxWarning`).
- A few `E501` (line too long) wraps, including two multi-line splits of
  dead comment text.
- `python -m black python/run_templates.py`: one further whitespace-only
  reformat.

### Verification performed

- `python -m pytest tests/test_run_templates.py -v` → 5 passed, in
  isolation, confirming zero `ROOT`/`PreFit` stubbing is needed for 3 of
  the 5 tests and only `sys.modules["PreFit"]` (not `ROOT`) for the other
  2.
- `python -m pytest tests/test_run_templates.py tests/test_run_anaFit.py -v`
  → 22 passed (5 + 17, matching the pre-move total of 22 exactly).
- `python scripts/quality_check.py --mode full` → 142 passed, 2
  deselected; ruff clean; black clean (18 files unchanged); exit code 0.
- `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
  → 1 passed in 123.97s - **mandatory** for this chunk, matched against
  the frozen reference exactly.
- `git diff --check` → passed.

### Compliance review (Section 8, Extraction checklist)

1. Chunk 5, Step B (this entry).
2. Step A is committed (`8d614ee`) and referenced above.
3. No scientific constants, references, tolerances, dependency revisions,
   or canonical workflow arguments touched.
4. Relocated tests' diffs are not import-line-only - the call target
   changed from `module.run_anaFit(...)` to
   `run_templates.prepare_run_templates(...)`/`replaceinfile(...)`
   directly, documented above as a necessary, anticipated consequence of
   the function now existing standalone; no assertion or expected value
   changed.
5. All three new/moved functions are covered: `replaceinfile` (1 test),
   `prepare_run_templates`/`_stage_xml_templates` (3 tests covering the
   representative, signal-systematics, and nPars-regression cases), and
   `_seed_prefit_parameters` (2 tests, including the nPars regression).
6. Confirmed by grep: `run_anaFit.py` actually imports and never
   redefines `prepare_run_templates`/`replaceinfile`.
7. Only this chunk's five changed/new files were staged.
8. All required Section 7 gates ran and passed, including the mandatory
   integration gate, output captured above.
9. `git diff --check` passed.
10. This activity-log entry appended (not a rewrite of any existing
    section).
11. Chunks 6 through 12 remain open, listed below.
12. No other branch's Tier 3 work was consulted.

### Remaining open chunks

Chunks 6 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open. Chunk 5
(both Step A and Step B) is complete and verified - the plan's riskiest
single extraction is done.

## 2026-09-02: Fix should_mask() to preserve NaN behavior (GitHub Copilot review, PR #6)

### What Copilot found

On Chunk 4.B's `should_mask(p_value, threshold)`, implemented as
`return p_value <= threshold`: this looks equivalent to the coordinator's
original `not (p_value > threshold)` gating for ordinary floats, but is
not equivalent for NaN. Under IEEE 754 comparison rules, both
`nan > threshold` and `nan <= threshold` are `False`. So the original
code (`if pval_global > maskthreshold: <success> else: <masking>`) would
take the masking branch for a NaN p-value (a real possibility from a
degenerate fit), while `not should_mask(nan, threshold)` (`not (nan <=
threshold)` = `not False` = `True`) would take the *success* branch
instead - silently skipping masking/BumpHunter for a NaN fit result.

### Verification performed before fixing

Confirmed directly in Python rather than taking the claim on faith:
`nan > 0.01` is `False` and `nan <= 0.01` is `False` too - so the two
candidate implementations of `should_mask()` genuinely disagree for a
NaN input: the buggy `p_value <= threshold` gives `False` (so `not
should_mask(nan, t)` is `True`, taking the coordinator's success
branch), while the correct `not (p_value > threshold)` gives `True` (so
`not should_mask(nan, t)` is `False`, taking the masking branch) -
matching what the original inline `if pval_global > maskthreshold:`
would have done before Chunk 4 extracted it. Traced through
`run_anaFit()`'s three call sites (`not should_mask(pval_global, ...)`,
`not should_mask(pval_masked, ...)`, `dolimit and dosignal and not
should_mask(pval_global, ...)`) to confirm all three would be affected
identically by a NaN p-value with the buggy implementation.

### Fix

`python/run_masking.py`: `should_mask()` changed from `p_value <=
threshold` to `not (p_value > threshold)` - byte-for-byte the
coordinator's original gating condition, negated, with a comment
explaining why the two forms are not interchangeable. This is not a
convention change (both forms give identical results for every ordinary
float); it only changes behavior for NaN, which is exactly the point.

`tests/test_run_masking.py`:
`test_should_mask_treats_nan_p_value_as_requiring_masking` added -
asserts `should_mask(float("nan"), 0.01) is True`, which fails against
the old `p_value <= threshold` implementation (confirmed by the Python
check above) and passes against the fix.

### Verification performed

- `python -m pytest tests/test_run_masking.py -v -k should_mask` → 4
  passed (3 pre-existing cases plus the new NaN case).
- `python -m pytest tests/test_run_masking.py tests/test_run_anaFit.py -v`
  → 34 passed (33 + 1 new test).
- `python scripts/quality_check.py --mode full` → 143 passed, 2
  deselected; ruff clean; black clean (18 files unchanged).
- `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
  → 1 passed in 117.12s - the real J100/J50 pipeline, rerun as
  supplementary confirmation since this touches the exact masking
  predicate at the heart of the coordinator's branch logic (matching the
  same judgment call made for Chunk 1.B and Chunk 3.B); the canonical
  workflows produce well-behaved, non-NaN p-values, so this confirms the
  non-NaN path is unaffected by the fix, as expected.
- `git diff --check` → passed.

### Scope

Only `python/run_masking.py` and `tests/test_run_masking.py` touched.
Not folded into any later chunk's work - a review finding on already-
pushed Chunk 4 work, fixed immediately as its own commit, per this
project's established practice for Copilot review findings.

## 2026-09-03: Tier-3 refactoring — Chunk 6.A: characterization tests for `build_fit_extract`

### Objective

Pin down the current, unmodified behavior of `build_fit_extract()` in
`python/run_anaFit.py` before extracting it into `run_fit.py`, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 6.

### Pre-change state

Two failure-path tests already existed
(`test_build_fit_extract_stops_after_xmlreader_failure`,
`test_build_fit_extract_stops_after_quickfit_failure`), both passing
unmodified. Per the plan's Section 2 baseline, these only cover the two
`execute_required` failure branches — no test exercised the successful
path at all: the `ROOT.TFile`/`FindBin` lookup for `datafirstbin`, the
mask-range branch on the quickFit command, the `PostfitExtractor`/
`FitParameterExtractor` calls, or the p-value-source selection between
`Run3TLA_rebinned` and `Run3TLA_bkgonly_rebinned`.

### Target function — inputs and outputs (as it exists today)

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `build_fit_extract(topfile, datafile, datahist, rangelow, rangehigh, wsfile, fitresultfile, poi=None, maskrange=None)` | as listed | `(pval: float, postfitfile: str, parameterfile: str)` | runs XMLReader + quickFit subprocesses; writes ROOT files; may generate a resolution-binning file; shells out to `plot_edm.py` |

### Tests added

- `test_build_fit_extract_succeeds_for_unmasked_fit` — drives the full
  successful path with `maskrange=None` using controlled test doubles
  (`_FakeTFile`/`_FakeHist` for the `ROOT.TFile`/`FindBin` lookup,
  `_FakePostfitExtractor`, `_FakeFitParameterExtractor`); asserts the
  returned `(pval, postfitfile, parameterfile)` tuple, that `maskmin`/
  `maskmax` reach `PostfitExtractor` as `-1`/`-1`, that
  `GetPval("Run3TLA_rebinned")` is the p-value source used, that
  `plot_edm.py` is shelled out to via a plain `execute()` (not
  `execute_required()`, so its result is discarded), and that
  `datafirstbin` is computed as `FindBin(rangelow) - 1` from the fake
  histogram.
- `test_build_fit_extract_succeeds_for_masked_fit` — same doubles with
  `maskrange=(500, 600)`; asserts `--range SBLo_Run3TLA,SBHi_Run3TLA`
  reaches the actual quickFit command string, that `maskmin`/`maskmax`
  reach `PostfitExtractor` as `500`/`600`, and that
  `GetPval("Run3TLA_bkgonly_rebinned")` (the renormalized source) is
  selected instead of the unmasked one.

Both new tests force `os.path.exists()` to `True` via `monkeypatch` so
the resolution-binning-file branch (`createBinning.py`) is deterministic
and independent of what happens to already exist on disk for
`rangelow=481` — a real fixture file for that range exists in the
repository, which would otherwise make the test's behavior depend on
filesystem state rather than the code path under test.

### What this commit does NOT do

No production file was modified. `git diff --stat -- python/` was empty
throughout this change — only `tests/test_run_anaFit.py` was touched.

### Verification performed

- `python -m pytest tests/test_run_anaFit.py -v -k build_fit_extract` →
  4 passed (2 pre-existing failure-path cases plus the 2 new
  successful-path cases), run against the unmodified
  `python/run_anaFit.py`.
- `python -m pytest tests/test_run_anaFit.py -v` → 19 passed (full-file
  regression check).
- `python scripts/quality_check.py --mode full` → 145 passed, 2
  deselected; ruff clean; black clean (18 files unchanged) — one ruff
  F841 (unused `executed_commands` in the masked test) and one black
  reformat (long `monkeypatch.setattr(... raising=False)` line) were
  found and fixed while preparing this commit, both confined to the new
  test code itself.
- `git diff --stat` → only `tests/test_run_anaFit.py` touched.
- `git diff --check` → passed.
- `grep -nE '[[:blank:]]+$' tests/test_run_anaFit.py` → no output.

### Compliance review (Section 8, Characterization checklist)

1. Chunk 6, Step A.
2. `git diff --stat` shows only `tests/test_run_anaFit.py` — zero
   production files touched.
3. Both new tests assert the real, specific successful-path shape
   (return tuple, exact kwargs reaching the collaborators, exact p-value
   source string selected), not merely "does not raise."
4. Tests were run against the unmodified target file before any
   production change; results reported in full above for review.
5. Human-verification checkpoint: presented to the user in session for
   confirmation before Step B's commit is made (recorded per Step B's own
   activity-log entry once given).

### Remaining open chunks

Chunk 6.B (extraction of `run_fit.py`) and Chunks 7 through 12 are open.

## 2026-09-03: Tier-3 refactoring — Chunk 6.B: extract `run_fit.py`

### Objective

Move `build_fit_extract()`, characterized in Chunk 6.A (commit
`e8f5467`), out of `run_anaFit.py` into a new `python/run_fit.py`, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 6.

### What changed

- `python/run_fit.py` created with `build_fit_extract()`, moved verbatim
  in logic and comments (including the commented-out dead alternatives -
  the `#bkgonly_opt` lines, the two commented-out `rebinfile=` variants,
  and the `#pfe.WriteRoot(postfitfile)` line). `from run_execution import
  execute, execute_required` at module level (flat sibling-import style)
  - the module needs both: `execute` for the `plot_edm.py` diagnostic
    call and the conditional `createBinning.py` call; `execute_required`
    for XMLReader and quickFit.
  - `import ROOT`, `from ExtractPostfitFromWS import PostfitExtractor`,
    `from ExtractFitParameters import FitParameterExtractor` are deferred
    inside `build_fit_extract` itself, placed immediately before the
    first `ROOT.TFile(...)` line - i.e. after both `execute_required`
    calls have already succeeded, matching the plan's import-placement
    rule. This is why the two failure-path tests (`_stops_after_
    xmlreader_failure`, `_stops_after_quickfit_failure`) need zero
    ROOT/sibling-module stubbing in their relocated form - both return
    before reaching the deferred import.
- `python/run_anaFit.py`: `build_fit_extract()`'s 106-line definition
  removed; `from ExtractPostfitFromWS import PostfitExtractor`, `from
  ExtractFitParameters import FitParameterExtractor`, and `import ROOT`
  removed from the top-level import block (confirmed by `grep -n "ROOT\.
  \|PostfitExtractor\|FitParameterExtractor" python/run_anaFit.py`
  before editing that every remaining reference to all three was inside
  the function being moved - none survive elsewhere in the coordinator).
  Replaced with `from run_fit import build_fit_extract` (flat
  sibling-import style). The two `run_anaFit()` call sites
  (`pval_global, ... = build_fit_extract(...)` and `pval_masked,_,_ =
  build_fit_extract(...)`) are unchanged - same name, now resolved via
  the import.
- `tests/test_run_fit.py` created with the 4 tests from Chunk 6.A
  (2 pre-existing failure-path, 2 new successful-path), relocated per the
  Test Relocation Rule with two documented, necessary exceptions (below).
- `scripts/quality_check.py`: added `python/run_fit.py` to
  `python_targets` and `tests/test_run_fit.py` to `test_targets`.

### Two Test Relocation Rule exceptions, both anticipated in Chunk 6.A and confirmed necessary

1. **Cross-module patch target.** `execute`/`execute_required` live in
   `run_execution.py`, a different module from where `build_fit_extract`
   now lives. The relocated tests patch `run_fit.execute_required`/
   `run_fit.execute` directly (via `monkeypatch.setattr(run_fit, ...)`),
   not `module.execute_required` as in the old `test_run_anaFit.py`
   version - the same necessary-consequence pattern already documented
   for Chunk 4.B (`run_masking.execute_required`) and Chunk 1.B.
2. **Deferred-import stubbing.** Because `ROOT`, `PostfitExtractor`, and
   `FitParameterExtractor` are now imported inside `build_fit_extract`
   itself rather than at module level, there is no `run_fit.ROOT`/
   `run_fit.PostfitExtractor` attribute to patch directly (unlike the old
   `test_run_anaFit.py` version, which patched attributes on the
   `exec_module`-loaded coordinator object that already had these names
   bound at import time). The two successful-path tests instead stub the
   modules those deferred imports resolve against, via
   `monkeypatch.setitem(sys.modules, "ROOT"/"ExtractPostfitFromWS"/
   "ExtractFitParameters", fake_module)` - the same technique already
   used for `run_provenance.collect_scientific_runtime`'s deferred
   `import ROOT` (Chunk 3.A/3.B) and `run_templates._seed_prefit_
   parameters`'s deferred `from PreFit import PreFitter` (Chunk 5.B). All
   assertions and expected values carried over unchanged from Chunk 6.A -
   only how the doubles are installed differs.

The two failure-path tests needed **neither** exception - they still
patch `run_fit.execute_required` only (exception 1 applies to both
failure and success tests equally) and never reach the deferred
ROOT/extractor imports at all, confirming the import placement is
correct per the plan's own acceptance check.

### Ruff/Black fixes required to register the new file (mechanical, zero behavior change)

Registering `run_fit.py` in `python_targets` was the first time this
exact code was lint-checked (it lived inside the un-gated
`run_anaFit.py` before):
- `def build_fit_extract(...)`'s 121-character single-line signature
  wrapped to one parameter per line.
- Two long `print(...)` string literals and the `quickfit_command`
  format string wrapped using implicit adjacent-string-literal
  concatenation - no change to the resulting string values.
- The `execute(f"python3 python/createBinning.py ...")` call wrapped
  across two lines (black then folded the two adjacent f-string literals
  back onto one line, still under 100 columns).
- Two `E501` findings on already-commented-out dead code
  (`#binningFileName = f"/afs/.../lbazzano/..."`,
  `#rebinfile=f"/afs/.../lbazzano/..."` x2) and one on a comment
  containing a long already-commented-out `print(...)` call marked
  `# noqa: E501` rather than reformatted, to avoid rewriting the exact
  text of preserved dead code for a line-length rule that only applies to
  live formatting; the "If we used masking..." comment was wrapped across
  two lines instead, since it is prose, not preserved code/data.
- `python -m black python/run_fit.py`: one further whitespace-only
  reformat (operator spacing, e.g. `_poi="-p %s" % poi` ->
  `_poi = "-p %s" % poi`).

None of these touch `run_anaFit.py`, which remains outside
`python_targets` (deferred to Chunk 8, per the established policy for
this file's pre-existing dead imports).

### Verification performed

- `python -m pytest tests/test_run_fit.py -v` → 4 passed, in isolation.
- `python -m pytest tests/test_run_fit.py tests/test_run_anaFit.py -v`
  → 19 passed (4 + 15, matching the pre-move total of 19 exactly).
- `python scripts/quality_check.py --mode full` → 145 passed, 2
  deselected; ruff clean; black clean (20 files unchanged); exit code 0.
- `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
  → 1 passed in 118.72s - **mandatory** for this chunk (Section 7:
  Chunks 4, 5, 8, and always before 12; this chunk rewrites the
  coordinator's actual fit/masking call path), matched against the
  frozen reference exactly.
- `git diff --stat -- python/run_anaFit.py` → 111 lines changed (1
  insertion, 110 deletions) - confirms only the import block and the
  function body were touched, nothing in `run_anaFit()` itself.
- `git diff --check` → passed (all trailing-whitespace hits are
  pre-existing lines in `run_anaFit.py`'s untouched body, not part of
  this diff).

### Compliance review (Section 8, Extraction checklist)

1. Chunk 6, Step B (this entry).
2. Step A is committed (`e8f5467`) and referenced above.
3. No scientific constants, references, tolerances, dependency revisions,
   or canonical workflow arguments touched.
4. Relocated tests' diffs are not import-line-only - two documented,
   necessary exceptions (cross-module patch target; deferred-import
   stubbing), both anticipated in Chunk 6.A; no assertion or expected
   value changed from Chunk 6.A.
5. `build_fit_extract` is covered by all 4 tests (2 failure-path,
   2 successful-path, unmasked and masked).
6. Confirmed by grep: `run_anaFit.py` actually imports and never
   redefines `build_fit_extract`.
7. Only this chunk's five changed/new files were staged.
8. All required Section 7 gates ran and passed, including the mandatory
   integration gate, output captured above.
9. `git diff --check` passed.
10. This activity-log entry appended (not a rewrite of any existing
    section).
11. Chunks 7 through 12 remain open, listed below.
12. No other branch's Tier 3 work was consulted.

### Remaining open chunks

Chunks 7 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open.

## 2026-09-03: Tier-3 refactoring — Chunk 7.A: characterization tests for `main()`'s argument parsing and signal-name defaulting

### Objective

Pin down the current, unmodified behavior of `main()`'s inline
`argparse` setup and default-signame logic in `python/run_anaFit.py`
before extracting them into `build_arg_parser()`/`normalize_signal_name()`
in `run_cli.py`, per `doc/TIER3_COMPLETION_PLAN.md` Chunk 7. Neither
target function exists yet, so - per Chunk 5.A's precedent - this logic
is characterized indirectly, by calling the real `main()` (with
`run_anaFit` monkeypatched to capture its kwargs) rather than by
constructing a standalone parser that doesn't exist yet.

### Pre-change state

Only `test_main_propagates_analysis_status` touched `main()` before this
commit, and only to confirm it returns `run_anaFit()`'s status - it never
inspects parsed arguments or the derived `signame`. No dedicated test
existed for the default-naming branch (normal width, the `sigwidth ==
-999` Zprime branch, or the `7.0`-vs-`"7"` string-formatting quirk named
explicitly in the plan's own Chunk 7 text as a known "clean-up" trap), nor
for a representative full set of CLI flags parsing correctly.

### Target functions (as they exist today, inline in `main()`)

| Function-to-be | Inputs | Outputs | Side effects |
|---|---|---|---|
| `build_arg_parser()` | none | `argparse.ArgumentParser` | none |
| `normalize_signal_name(sigmean, sigwidth, signame)` | `sigmean`, `sigwidth`, `signame` (possibly `None`/falsy) | `str` | none (pure) |

### Tests added

- `test_main_derives_default_signame_for_normal_width` — no `--signame`,
  `sigmean=1200`, `sigwidth=8.5` -> `"mean1200_width8.5"`.
- `test_main_preserves_integer_valued_float_width_in_default_signame` —
  `--sigwidth` omitted (default `7.` = `7.0`) -> `"mean1000_width7.0"`,
  pinning down the naive `"%s"`-style formatting the plan warns is easy to
  accidentally "clean up" into `"%g"`-style formatting (which would
  silently turn `7.0` into `7`) during extraction.
- `test_main_uses_zprime_naming_when_sigwidth_is_minus_999` —
  `sigwidth=-999`, `sigmean=1400` -> `"mR1400"`.
- `test_main_respects_explicit_signame_override` — an explicit
  `--signame` survives unchanged even when it doesn't match what the
  default-naming logic would have derived for the same
  `sigmean`/`sigwidth`.
- `test_main_parses_representative_j100_style_invocation` — mirrors an
  actual invocation shape from `scripts/run_anaFit_J100.sh`
  (`backgroundfile`/`signalfile` present, no `--signame`/`--dosignal`/
  `--dolimit`/`--doprefit`/`--sysfile`), asserting the full set of parsed
  values (including defaults `nsig="0,-1E6,1E6"`, `dosignal=False`,
  `dolimit=False`, `doprefit=False`, `systdict=None`) that reach
  `run_anaFit()`.

All five new tests pass `--folder` pointing at `tmp_path` to avoid the
side effect of `main()`'s `os.makedirs(args.folder)` creating a real
`run/` directory in the working tree (the pre-existing
`test_main_propagates_analysis_status` already relies on the untouched
default and was left as-is, per the Test Relocation Rule guidance below).

### Test Relocation Rule check for `test_main_propagates_analysis_status`

Per the plan's own explicit instruction: this test only exercises status
propagation through `main()` end-to-end (`run_anaFit` fully mocked, no
inspection of parsed arguments or `signame`) - it does not test parsing
behavior directly. It therefore stays in `tests/test_run_anaFit.py` and
is not moved to `tests/test_run_cli.py` in Step B.

### What this commit does NOT do

No production file was modified. `git diff --stat -- python/` was empty
throughout this change - only `tests/test_run_anaFit.py` was touched (5
new tests plus one shared capture helper, 220 lines).

### Verification performed

- `python -m pytest tests/test_run_anaFit.py -v -k main` → 7 passed (2
  pre-existing status-propagation cases plus the 5 new parsing/naming
  cases), run against the unmodified `python/run_anaFit.py`.
- `python -m pytest tests/test_run_anaFit.py -v` → 20 passed (full-file
  regression check).
- `python scripts/quality_check.py --mode full` → 150 passed, 2
  deselected; ruff clean; black clean (20 files unchanged).
- `git diff --stat` → only `tests/test_run_anaFit.py` touched.
- `git diff --check` → passed.
- `grep -nE '[[:blank:]]+$' tests/test_run_anaFit.py` → no output.

### Compliance review (Section 8, Characterization checklist)

1. Chunk 7, Step A.
2. `git diff --stat` shows only `tests/test_run_anaFit.py` - zero
   production files touched.
3. Each new test asserts the real, specific derived value (`signame`,
   or the full set of parsed kwargs), not merely "does not raise."
4. Tests were run against the unmodified target file before any
   production change; results reported in full above for review.
5. Human-verification checkpoint: presented to the user in session for
   confirmation before Step B's commit is made (recorded per Step B's own
   activity-log entry once given).

### Remaining open chunks

Chunk 7.B (extraction of `run_cli.py`) and Chunks 8 through 12 are open.

## 2026-09-03: Tier-3 refactoring — Chunk 7.B: extract `run_cli.py`

### Objective

Move `main()`'s inline `argparse` setup and default-signame logic,
characterized in Chunk 7.A (commit `9194c2a`), out of `python/run_anaFit.py`
into a new `python/run_cli.py`, per `doc/TIER3_COMPLETION_PLAN.md`
Chunk 7 - the plan's last extraction.

### What changed

- `python/run_cli.py` created with two functions:
  - `build_arg_parser()` - the 22 `parser.add_argument(...)` calls, moved
    verbatim (same flags, dests, types, defaults, help text, including the
    `default= None` stray-space quirk on `--signalfile`), wrapped in a
    thin function that returns the constructed parser instead of leaving
    it inline in `main()`.
  - `normalize_signal_name(sigmean, sigwidth, signame)` - the
    `if not args.signame: ...` default-naming block, moved verbatim and
    made pure (takes/returns `signame` instead of mutating `args`).
- `python/run_anaFit.py`: the 22-line `parser = argparse.ArgumentParser
  (...)` block and the 5-line default-signame `if` block both removed from
  `main()`; replaced with `parser = build_arg_parser()` and `args.signame =
  normalize_signal_name(args.sigmean, args.sigwidth, args.signame)`.
  `from run_cli import build_arg_parser, normalize_signal_name` added
  (flat sibling-import style). The top-level `argparse` name in the
  combined `import os,sys,re,argparse,subprocess,shutil` statement is now
  dead - left in place and documented, per the established policy for
  this not-yet-gated file's dead imports (`hashlib`/`platform`/
  `subprocess` since Chunk 3.B, `re` since Chunk 5.B), deferred to
  Chunk 8's coordinator slimming.
- `tests/test_run_cli.py` created with 5 tests, **rewritten to call
  `run_cli.build_arg_parser()`/`run_cli.normalize_signal_name()` directly**
  rather than through `main()` (see below).
- `scripts/quality_check.py`: added `python/run_cli.py` to
  `python_targets` and `tests/test_run_cli.py` to `test_targets`.

### Necessary test-relocation adaptation, and one deliberate non-move

Chunk 7.A's 5 characterization tests called `module.main([...])` end-to-end
(mocking `run_anaFit` and capturing its kwargs) because no standalone
function existed yet to call directly - the same situation as Chunk 5.A.
Now that `build_arg_parser()`/`normalize_signal_name()` exist, the 4 tests
whose whole point is one of those two functions' own behavior were
rewritten to call them directly and split accordingly:
- `test_main_derives_default_signame_for_normal_width`,
  `test_main_preserves_integer_valued_float_width_in_default_signame`,
  `test_main_uses_zprime_naming_when_sigwidth_is_minus_999`,
  `test_main_respects_explicit_signame_override` -> became
  `test_normalize_signal_name_derives_default_for_normal_width`,
  `test_normalize_signal_name_preserves_integer_valued_float_width`,
  `test_normalize_signal_name_uses_zprime_naming_when_sigwidth_is_minus_999`,
  `test_normalize_signal_name_respects_explicit_override` in
  `tests/test_run_cli.py`, calling `run_cli.normalize_signal_name(sigmean,
  sigwidth, signame)` directly - no `main()`, no module loading, no
  `tmp_path`/`--folder` needed at all, since the pure function has no
  filesystem side effects. Same expected values as Chunk 7.A, unchanged.
- `test_main_parses_representative_j100_style_invocation` was **split
  rather than moved wholesale**: its flag-parsing assertions (datafile,
  backgroundfile, rangelow/rangehigh, dosignal/dolimit/doprefit,
  sigmean/sigwidth, nsig default, maskthreshold, sysfile) became
  `test_build_arg_parser_parses_representative_j100_style_invocation` in
  `tests/test_run_cli.py`, calling `run_cli.build_arg_parser()` directly
  and asserting `args.signame is None` (the bare parser leaves it
  unset - deriving a default is `normalize_signal_name()`'s job, not the
  parser's). Its `systdict` assertion belongs to neither new function -
  loading `--sysfile` into `systdict` is separate logic that **stays
  inline in `main()`** (out of scope for this chunk's two named target
  functions) - so the original test **was kept in
  `tests/test_run_anaFit.py`**, unmoved, now serving explicitly as
  `main()`'s own wiring/smoke test: that `build_arg_parser()` ->
  `parser.parse_args()` -> `normalize_signal_name()` -> the kwargs
  actually passed to `run_anaFit()` are still correctly connected, plus
  the one piece of CLI logic that remains inline. This is a documented,
  necessary Test Relocation Rule exception, not an oversight: the test's
  coverage spans two extracted functions and one still-inline block at
  once, so it could not honestly become an import-line-only move into
  either module.

### Ruff/Black fixes required to register the new file (mechanical, zero behavior change)

Registering `run_cli.py` in `python_targets` was the first time this
exact code was lint-checked (it lived inline in the un-gated
`run_anaFit.py`'s `main()` before): every `add_argument(...)` call
exceeded the 100-column limit (up to 178 characters) and was reflowed by
`python -m black python/run_cli.py` into one-argument-per-line or
single-line form as each call's length required; two calls remained
exactly at 99-100 columns after formatting and needed no further change.
No `ruff check` findings beyond what black's reformat already resolved.

### Verification performed

- `python -m pytest tests/test_run_cli.py -v` → 5 passed, in isolation.
- `python -m pytest tests/test_run_cli.py tests/test_run_anaFit.py -v`
  → 21 passed (5 new + 16 remaining in `test_run_anaFit.py`, matching the
  pre-move total of 21 exactly: Chunk 7.A's 20 plus one - Chunk 7.A had
  added 5 to a pre-existing 15, Step B nets the same 21 by moving 4 out
  and keeping 1 as the coordinator's wiring test).
- `python scripts/quality_check.py --mode full` → 151 passed, 2
  deselected; ruff clean; black clean (22 files unchanged); exit code 0.
- `git diff --stat -- python/run_anaFit.py` → 32 lines changed (4
  insertions, 28 deletions).
- `git diff --check` → passed (all trailing-whitespace hits are
  pre-existing lines in `run_anaFit.py`'s untouched body).
- The mandatory J100/J50 integration gate was **not** rerun for this
  chunk: `build_arg_parser()`/`normalize_signal_name()` touch no real
  branch conditions in the scientific fit/masking pipeline (pure CLI
  parsing and string formatting), matching the precedent set by Chunk 2.B
  (`run_manifest.py`) and Chunk 3.B (`run_provenance.py`), neither of
  which reran it either - Section 7 reserves the mandatory rerun for
  Chunks 4, 5, 8, and always before 12.

### Compliance review (Section 8, Extraction checklist)

1. Chunk 7, Step B (this entry) - the plan's last extraction chunk.
2. Step A is committed (`9194c2a`) and referenced above.
3. No scientific constants, references, tolerances, dependency revisions,
   or canonical workflow arguments touched.
4. Relocated tests' diffs are not import-line-only - the call target
   changed from `module.main(...)` to `run_cli.build_arg_parser()`/
   `run_cli.normalize_signal_name(...)` directly for 5 tests, and one
   test was deliberately kept unmoved as a documented exception (its
   coverage spans a still-inline block); no assertion or expected value
   changed from Chunk 7.A.
5. Both new functions are covered: `build_arg_parser()` (1 direct test
   plus indirect coverage via `main()`'s own wiring test) and
   `normalize_signal_name()` (4 tests covering normal width, the
   float-formatting quirk, the Zprime branch, and explicit override).
6. Confirmed by grep: `run_anaFit.py` actually imports and never
   redefines `build_arg_parser`/`normalize_signal_name`; no remaining
   `argparse.` call sites outside the dead top-level import.
7. Only this chunk's five changed/new files were staged.
8. All required Section 7 gates ran and passed; the mandatory integration
   gate was correctly judged not applicable to this chunk (see above),
   matching established precedent for non-branch-touching chunks.
9. `git diff --check` passed.
10. This activity-log entry appended (not a rewrite of any existing
    section).
11. Chunk 8 through 12 remain open, listed below.
12. No other branch's Tier 3 work was consulted.

### Remaining open chunks

Chunks 8 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open. All seven
module extractions (Chunks 1-7) are now complete and verified;
`python/run_anaFit.py` is 254 lines. Chunk 8 (coordinator slimming and
dependency-direction verification) is next.

## 2026-09-03: Fix run_cli.py description placeholder and a wrong test return annotation (GitHub Copilot review, PR #6)

### What Copilot found

Two findings on the Chunk 7.B commit (`fdee1ae`):

1. `python/run_cli.py:5` (also flagged, incorrectly, as recurring on line
   53 - no second occurrence actually exists there, checked directly):
   `argparse.ArgumentParser(description="%prog [options]")` uses the
   optparse-era `%prog` placeholder, which `argparse` does not substitute
   in `description` - it would appear literally in `--help` output.
   `argparse`'s own placeholder is `%(prog)s`.
2. `tests/test_run_fit.py:135-138`:
   `_prepare_build_fit_extract_success_doubles()` is annotated `-> None`
   but actually `return`s `executed_commands` (a `list[str]`).

### Verification performed before fixing

- Finding 2 (return-type mismatch) is directly visible by reading the
  function body against its own signature - confirmed by inspection, no
  further check needed.
- Finding 1 required checking whether `argparse` actually substitutes
  `%(prog)s` (unlike `%prog`, which is optparse-specific) - confirmed
  empirically: constructing two parsers with `description="%prog
  [options]"` and `description="%(prog)s [options]"` respectively and
  rendering each showed the first prints the placeholder text unchanged,
  the second substitutes the real program name. This is a real,
  user-visible bug (a person running `--help` would see the literal
  string `%prog [options]` instead of a description).
- **Scope check**: `git blame`/direct comparison against the pre-Tier-3
  commit (`5b23af8`) confirmed `'%prog [options]'` is not something this
  refactor introduced - it was already present, verbatim, in the original
  `run_anaFit.py`'s inline `main()`, moved as-is into `run_cli.py` by
  Chunk 7.B per the "move verbatim" policy. A repo-wide `grep -rn
  "%prog"` additionally found the exact same `%prog [options]` pattern in
  **29 other files** across `python/` (essentially every script in the
  repo using `argparse`/`optparse`), confirming this is a long-standing,
  repo-wide copy-paste convention, not something specific to
  `run_anaFit.py`. Per `doc/TIER3_COMPLETION_PLAN.md`'s own guardrail
  ("Fixing pre-existing, unrelated issues noticed along the way ... note
  them in the activity log if seen again, do not fix them unless a chunk
  says to"), the other 29 occurrences are explicitly **out of scope** and
  were not touched - Tier 3's scope is the four named files, not a
  repo-wide sweep. This one occurrence is fixed because it is literally
  the line Copilot flagged in this PR's diff and is required to complete
  the merge review, matching this project's established practice for
  addressing real PR review findings (e.g. the `should_mask()` NaN fix).

### A second, unrelated pre-existing bug found while verifying the fix (noted, not fixed)

Confirming the `%(prog)s` substitution end-to-end via
`parser.print_help()` crashed with `ValueError: unsupported format
character ')' ... `, unrelated to the `description` fix itself. Root
cause: the `--sigwidth` argument's `help=` text - `"Width of signal
Gaussian for s+b fit (in %). If -999 dealing with Zprime samples."` -
contains a bare `%` that `argparse`'s help-string `%`-expansion (used for
things like `%(default)s`) chokes on when rendering the *full* help
output. This exact string was confirmed present, unchanged, at the
pre-Tier-3 commit (`5b23af8`) too - calling `run_anaFit.py --help` (or
now `run_cli.build_arg_parser().print_help()`) has been broken since
before this refactor started. Per the same plan guardrail cited above,
this is noted here rather than fixed; the new regression test below
verifies the `description` fix in isolation (via the formatter's
`add_text()`/`format_help()`, not `parser.print_help()`) specifically to
avoid tripping over this unrelated, out-of-scope crash.

### Fixes

- `python/run_cli.py`: `description="%prog [options]"` ->
  `description="%(prog)s [options]"`.
- `tests/test_run_fit.py`: `_prepare_build_fit_extract_success_doubles()`'s
  return annotation `-> None` -> `-> list[str]`.
- `tests/test_run_cli.py`:
  `test_build_arg_parser_description_uses_argparse_prog_placeholder`
  added - asserts `"%prog" not in parser.description` and that rendering
  the description through the formatter substitutes the real `prog`
  value. Confirmed to fail against the pre-fix `"%prog [options]"` string
  (`AssertionError: assert '%prog' not in '%prog [options]'`) and pass
  against the fix.

### Verification performed

- `python -m pytest tests/test_run_cli.py -v` → 6 passed (5 pre-existing
  plus the new regression test).
- `python -m pytest tests/test_run_fit.py tests/test_run_cli.py tests/test_run_anaFit.py -v`
  → 26 passed.
- `python scripts/quality_check.py --mode full` → 152 passed, 2
  deselected; ruff clean; black clean (22 files unchanged).
- `git diff --check` → passed.
- The mandatory integration gate was not rerun: neither fix touches the
  fit/masking pipeline (a CLI help-text placeholder and a test-only type
  annotation), matching the same judgment already applied to Chunk 7.B
  itself.

### Scope

Only `python/run_cli.py`, `tests/test_run_fit.py`, and
`tests/test_run_cli.py` touched. Not folded into Chunk 8 - a review
finding on already-pushed Chunk 7 work, fixed immediately as its own
commit, per this project's established practice for Copilot review
findings.

## 2026-09-03: Fix the sigwidth help-string crash and a rangehigh help typo (GitHub Copilot review, PR #6)

### What Copilot found

Two more findings on `python/run_cli.py`, following up on the previous
commit (`850b35b`):

1. (Medium) The `--sigwidth` help text contains a literal `%`, which
   `argparse` treats as a format marker when rendering full `--help`
   output; this raises `ValueError` and breaks help generation in normal
   CLI usage. Suggested fix: escape it as `%%`.
2. (Low) The `--rangehigh` help text reads `"End Start of fit range (in
   GeV)"` - an apparent accidental duplication/typo, confusing in `--help`
   output.

### Correction to the previous commit's scoping decision

The previous commit (`850b35b`) already found and *documented* this exact
`--sigwidth` crash while verifying the `%prog` fix, but judged it
out-of-scope as a "pre-existing, unrelated issue noticed incidentally"
per `doc/TIER3_COMPLETION_PLAN.md`'s guardrail, and left it unfixed with
a comment explaining why. Copilot has now flagged the same line directly
as a blocking finding on this PR. Per this project's established
practice for review findings (fix what Copilot raises on the PR, not a
repo-wide sweep), this is the correct trigger to fix it: unlike the other
28 occurrences of the unrelated `%prog` pattern found elsewhere in the
repo (still correctly left untouched - a repo-wide sweep remains out of
scope), this line lives in `run_cli.py`, a file created by this PR, and
is directly, specifically flagged as blocking approval. The guardrail's
purpose is to prevent scope creep into unrelated files noticed
in passing, not to leave a confirmed, reviewer-flagged crash in the code
this PR is introducing.

### Verification performed before fixing

- Confirmed the crash directly: `run_cli.build_arg_parser().print_help()`
  raised `ValueError: unsupported format character ')' (0x29) at index
  42` before the fix (matches the trace already captured in the previous
  commit's activity-log entry).
- Confirmed the `--rangehigh` typo by direct inspection - the text is
  exactly `"End Start of fit range (in GeV)"`, evidently `"End "`
  mistakenly prepended to a copy of `--rangelow`'s own `"Start of fit
  range (in GeV)"` help text.
- After fixing, confirmed `parser.format_help()` renders the full help
  text successfully (no exception), and that the escaped `%%` renders as
  a single literal `%` in the output: `"Width of signal Gaussian for s+b
  fit (in %). If -999 dealing with Zprime samples."` appears verbatim in
  the rendered text - the escaping changes only how the help string is
  written in source, not what a user sees.

### Fixes

- `python/run_cli.py`:
  - `--sigwidth`'s `help=` string: `"...(in %). If -999..."` ->
    `"...(in %%). If -999..."`.
  - `--rangehigh`'s `help=` string: `"End Start of fit range (in GeV)"`
    -> `"End of fit range (in GeV)"`.
- `tests/test_run_cli.py`:
  - `test_build_arg_parser_format_help_does_not_raise` added - calls
    `parser.format_help()` directly (the full render, not the isolated
    formatter workaround the previous commit used to sidestep this exact
    crash) and asserts the expected wording appears. Confirmed to raise
    `ValueError` against the pre-fix `%` (not `%%`) and pass against the
    fix.
  - `test_build_arg_parser_rangehigh_help_does_not_duplicate_start` added
    - asserts the exact expected help string. Confirmed to fail against
    the pre-fix `"End Start of fit range (in GeV)"` text and pass against
    the fix.
  - `test_build_arg_parser_description_uses_argparse_prog_placeholder`
    (added in the previous commit) simplified: now calls
    `parser.format_help()` directly instead of the isolated
    `formatter.add_text()`/`format_help()` workaround, since the full
    render no longer crashes - the workaround and its explanatory comment
    are no longer needed and were removed.

### Verification performed

- `python -m pytest tests/test_run_cli.py -v` → 8 passed (3 new/changed
  plus 5 unchanged).
- `python -m pytest tests/test_run_cli.py tests/test_run_fit.py tests/test_run_anaFit.py -v`
  → 28 passed.
- `python scripts/quality_check.py --mode full` → 154 passed, 2
  deselected; ruff clean; black clean (22 files unchanged) - one further
  black reformat collapsed `--rangehigh`'s `add_argument(...)` back onto
  a single line, now under 100 columns with the shorter help text.
- `git diff --check` → passed.
- The mandatory integration gate was not rerun: this fix touches only CLI
  help text (`argparse` `help=`/`description=` strings), not the
  fit/masking pipeline, matching the same judgment already applied to
  Chunk 7.B and the previous Copilot-fix commit.

### Scope

Only `python/run_cli.py` and `tests/test_run_cli.py` touched. Not folded
into Chunk 8 - a review finding on already-pushed Chunk 7 work, fixed
immediately as its own commit, per this project's established practice
for Copilot review findings.

## 2026-09-03: Fix optional range args and ambiguous command-string concatenation (GitHub Copilot review, PR #6)

### What Copilot found

Two more findings on the newly introduced Chunk 6/7 modules:

1. (Medium) `python/run_cli.py`: `--rangelow`/`--rangehigh` are parsed as
   optional, but `run_anaFit.run_anaFit()` immediately does `rangehigh -
   rangelow` arithmetic, so omitting either would parse to `None` and
   crash later with a confusing `TypeError` instead of a clear `argparse`
   usage error at parse time. Suggested fix: mark both `required=True`.
2. (Low) `python/run_fit.py`: `xmlreader_command`'s construction relies on
   implicit adjacent-string-literal concatenation with mixed quoting
   (`"..." '...'`), which is easy to misread/edit. Suggested fix: a single
   f-string, keeping the exact runtime command text unchanged.

### Verification performed before fixing

- Confirmed finding 1's premise by inspection: `run_anaFit()`'s first
  real line of work is `nbins=rangehigh - rangelow`, unconditionally.
  Neither flag has a `default=`.
- Checked whether this was introduced by Tier 3 or pre-existing: it was
  already present, verbatim, in the original `run_anaFit.py` (moved as-is
  by Chunk 7.B). Notably, the **sibling** script
  `python/run_injections_anaFit.py` (out of Tier 3's scope, untouched by
  this refactor) already marks its own `--rangelow`/`--rangehigh` as
  `required=True` for the exact same reason - confirming this is an
  established convention elsewhere in the codebase that `run_anaFit.py`'s
  own CLI simply never had, not a new requirement being invented here.
- Checked real-world impact: both `scripts/run_anaFit_J100.sh` and
  `scripts/run_anaFit_J50.sh` (the only production callers) already pass
  `--rangelow`/`--rangehigh` unconditionally - `required=True` changes
  nothing for the canonical workflows, it only changes what happens for
  an invocation that omits them (a clear `argparse` error instead of a
  crash two functions later).
- Found one existing test that *would* break:
  `test_main_propagates_analysis_status` in `tests/test_run_anaFit.py`
  omits both flags (it mocks `run_anaFit` entirely, so the resulting
  `None` values were never actually used) - updated to pass them, per the
  same practice used for prior fixes that require a compensating test
  update to stay green.
- Verified finding 2's suggested rewrite is byte-identical to the
  original by direct comparison in a Python shell: constructing the old
  three-piece expression and the new f-string with the same `topfile`
  value and comparing the results confirmed `old == new`.

### Fixes

- `python/run_cli.py`: `--rangelow` and `--rangehigh` both gained
  `required=True` (and were reflowed to `black`'s multi-line
  `add_argument(...)` form, since the line no longer fits one line with
  the new keyword).
- `python/run_fit.py`: `xmlreader_command`'s construction rewritten from
  `("...%s " '...') % topfile` to a single f-string
  `f'...XMLReader -x {topfile} -o "logy integral" --minimizerStrategy 0'`
  - same runtime string, single unambiguous literal.
- `tests/test_run_anaFit.py`: `test_main_propagates_analysis_status`'s
  args list gained `--rangelow 481 --rangehigh 3000`.
- `tests/test_run_cli.py`:
  - The representative-invocation args list was pulled out into a shared
    module-level `_REPRESENTATIVE_ARGS` constant (previously duplicated
    inline), used by both the existing parse test and the new one below.
  - `test_build_arg_parser_requires_range_flags` added (parametrized over
    both flags) - builds a valid arg list, removes one flag/value pair,
    and asserts `parser.parse_args(...)` raises `SystemExit` with the
    missing flag named in the printed error. Confirmed to fail
    (`DID NOT RAISE SystemExit`) against the pre-fix optional flags and
    pass against the fix.
- `tests/test_run_fit.py`:
  `test_build_fit_extract_stops_after_xmlreader_failure` extended to
  capture and assert the exact rendered `xmlreader_command` string,
  pinning down that the f-string rewrite produces byte-identical output.

### Verification performed

- `python -m pytest tests/test_run_cli.py -v` → 10 passed.
- `python -m pytest tests/test_run_fit.py tests/test_run_cli.py tests/test_run_anaFit.py -v`
  → 30 passed.
- `python scripts/quality_check.py --mode full` → 156 passed, 2
  deselected; ruff clean; black clean (22 files unchanged).
- `git diff --check` → passed.
- The mandatory integration gate was not rerun: `run_fit.py`'s change is
  proven byte-identical output (verified above and pinned by the new
  test), and `run_cli.py`'s `required=True` change does not alter the
  canonical J100/J50 invocations at all (both already pass these flags) -
  neither fix changes fit/masking behavior for the authoritative
  workflows, matching the judgment already applied to the two preceding
  Copilot-fix commits on this PR.

### Scope

Only `python/run_cli.py`, `python/run_fit.py`, `tests/test_run_cli.py`,
`tests/test_run_fit.py`, and `tests/test_run_anaFit.py` touched. Not
folded into Chunk 8 - review findings on already-pushed Chunk 6/7 work,
fixed immediately as their own commit, per this project's established
practice for Copilot review findings.

## 2026-09-03: Fix silent output-file collision when fitresultfile lacks the FitResult token (GitHub Copilot review, PR #6)

### What Copilot found

`python/run_fit.py` (High severity): `postfitfile`/`parameterfile`/
`logfile`/`edmplot` are all derived from `fitresultfile` via
`fitresultfile.replace("FitResult", <other token>)` - an undocumented
filename contract. If `fitresultfile`'s basename does not contain
`"FitResult"` (the CLI currently accepts any string via `--outputfile`,
with no such validation), every one of those substitutions is a no-op,
so `postfitfile` and `parameterfile` both silently collapse back to
`fitresultfile` itself; `PostfitExtractor`/`FitParameterExtractor` then
both open that same path in `RECREATE` mode, overwriting the quickFit
result twice. Separately, because the substitution operates on the
*entire path* rather than just the filename, a parent directory
component that happens to contain `"FitResult"` gets rewritten too.
Copilot's ask: validate the basename before launching quickFit, and
derive each sibling output by transforming only that basename.

### Verification performed before fixing

- Confirmed the collapse-to-self claim by direct reasoning through
  `str.replace()` semantics for a non-matching input (e.g.
  `"fit-result.root"`): every `.replace("FitResult", ...)` call is a
  no-op, so `postfitfile == parameterfile == fitresultfile`.
- Confirmed this predates Tier 3 - the exact same `.replace("FitResult",
  ...)` pattern, operating on the whole `fitresultfile` path, was already
  present in the original `run_anaFit.py`, moved verbatim into
  `run_fit.py` by Chunk 6.B. Unlike the `%prog` pattern (found duplicated
  in 29 unrelated files and correctly left untouched), this logic lives
  entirely inside `run_fit.py`, a file this PR created - the same
  reasoning already applied to the `--rangelow`/`--rangehigh` and
  `xmlreader_command` fixes earlier on this PR justifies fixing it here,
  not sweeping the rest of the repository.
- Checked real-world impact: both `scripts/run_anaFit_J100.sh` and
  `scripts/run_anaFit_J50.sh` always construct `--outputfile` as
  `${folder}/FitResult_anaFit_...root` - the canonical workflows are
  unaffected either way; this is a latent bug reachable only via a
  manual invocation with a non-conforming `--outputfile`.
- Reproduced the parent-directory-rewrite half of the bug directly: ran
  `build_fit_extract(..., fitresultfile="run/FitResult_stage/
  FitResult_anaFit.root")` against the pre-fix code and observed
  `postfitfile` come back as `"run/PostFit_stage/PostFit_anaFit.root"` -
  the `FitResult_stage` directory segment was rewritten to `PostFit_stage`
  along with the filename, confirmed via the new regression test (below)
  failing against the pre-fix code before the production fix was applied.

### Fix

`python/run_fit.py`: `os.path.split(fitresultfile)` splits the path once
into `fitresult_dir`/`fitresult_name`. A validation check (raising
`ValueError` if `"FitResult"` is not in `fitresult_name`) runs where
`logfile`/`edmplot` were already being derived - after XMLReader (which
never touches `fitresultfile`) but **before** quickFit launches, per
Copilot's ask. All four derived filenames (`logfile`, `edmplot`,
`postfitfile`, `parameterfile`) now transform only `fitresult_name` and
rejoin with `fitresult_dir` via `os.path.join(...)`, instead of
transforming the whole path. For every filename shape actually used
today (no directory component, or a directory with no incidental
`"FitResult"` substring), this produces byte-identical output to the
original code - confirmed by the three pre-existing success-path tests
passing unmodified against the fix.

### Tests added

- `tests/test_run_fit.py::test_build_fit_extract_rejects_fitresultfile_without_fitresult_token` -
  asserts `ValueError` (matching `'must contain "FitResult"'`) for
  `fitresultfile="fit-result.root"`, and that quickFit's
  `execute_required` call is never reached. Confirmed to pass silently
  (no exception) against the pre-fix code and raise correctly against the
  fix.
- `tests/test_run_fit.py::test_build_fit_extract_derives_siblings_from_basename_only` -
  `fitresultfile="run/FitResult_stage/FitResult_anaFit.root"`; asserts
  `postfitfile`/`parameterfile` come back as
  `"run/FitResult_stage/PostFit_anaFit.root"`/
  `"run/FitResult_stage/FitParameters_anaFit.root"` (directory segment
  preserved) and that the `plot_edm.py` diagnostic command embeds the
  correctly-derived `logfile`/`edmplot` paths too. Confirmed to fail
  against the pre-fix code with the directory segment corrupted to
  `"PostFit_stage"` (see above), and pass against the fix.

### Verification performed

- `python -m pytest tests/test_run_fit.py -v` → 6 passed (4 pre-existing
  plus the 2 new regression tests).
- `python -m pytest tests/test_run_fit.py tests/test_run_cli.py tests/test_run_anaFit.py -v`
  → 32 passed.
- `python scripts/quality_check.py --mode full` → 158 passed, 2
  deselected; ruff clean; black clean (22 files unchanged).
- `git diff --check` → passed.
- `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
  → 1 passed in 160.02s, matching the frozen reference exactly - rerun as
  extra confidence, since this fix changes the exact filename-derivation
  logic inside `build_fit_extract()` (the same function Chunk 6.B's own
  commit required the mandatory gate for), confirming the fix is
  byte-identical for the real J100/J50 filename shapes, not just the
  unit-test fixtures above.

### Scope

Only `python/run_fit.py` and `tests/test_run_fit.py` touched. Not folded
into Chunk 8 - a review finding on already-pushed Chunk 6 work, fixed
immediately as its own commit, per this project's established practice
for Copilot review findings.

## 2026-09-03: Tier-3 refactoring — Chunk 8: coordinator slimming and dependency-direction verification

### Objective

With Chunks 1-7 done (all seven module extractions complete, plus four
GitHub Copilot review-finding fixes), verify `run_anaFit()` now reads as
an orchestration of calls into the seven new modules, not a container for
their logic, and register `python/run_anaFit.py` itself with the Tier 2
quality gate. Per the plan, this is a checkpoint, not a new extraction -
no new target function exists, so guardrail 3's characterization-first
pattern does not apply; there is nothing new to characterize before
modifying, only a verification pass over work already characterized and
extracted in Chunks 1-7. Delivered as a single commit.

### Re-read of `run_anaFit.py` top to bottom

Confirmed the file contains only: imports, `run_anaFit()`, `main()`, and
the `if __name__ == "__main__":` guard - no extracted logic was copied
rather than moved, and no partial extractions remain. Verified formally
via the plan's own acceptance-check script (below).

### Dead imports removed (live gate failures once registered)

Registering `python/run_anaFit.py` in `python_targets` for the first time
surfaced imports that were dead but never checked while the file was
un-gated - the same "deferred to Chunk 8" imports named explicitly across
Chunks 3.B (`hashlib`, `platform`), 5.B (`re`), and implicitly since
7.B (`argparse`), plus one found only now:
- `re`, `argparse`, `subprocess`, `hashlib`, `platform`, and
  `from pathlib import Path` - all confirmed dead by grepping for every
  live (non-comment) use in the file; none found. Removed.
- `execute_required` (imported from `run_execution`, alongside `execute`)
  - confirmed dead: `run_anaFit.py` itself only ever calls `execute(...)`
    directly (for the quickLimit command); `execute_required` is used
    inside the sub-modules (`run_masking.py`, `run_templates.py`,
    `run_fit.py`), not the coordinator. This has been dead since
    Chunk 1.B's own extraction, simply never linted until now. Removed.
- `covariancedict = None` in `main()` - a local variable assigned but
  never used or passed to `run_anaFit()` (confirmed: `main()`'s call to
  `run_anaFit()` never includes `covariancedict=...`). This pairs with a
  pre-existing, still-commented `#if args.covariancefile: ...` stub for a
  CLI flag that was never actually added to `run_cli.py`'s
  `build_arg_parser()` - an unimplemented feature stub, not something
  Tier 3 is building out (out of scope per Section 3). Removed the dead
  assignment; left the commented stub as-is with an explanatory comment
  added above it, rather than deleting a decade-old TODO-shaped comment
  outright.

`os`, `sys`, `shutil`, `json`, and every `from run_*` import were
confirmed live (each has at least one real call site) and kept unchanged.

### Ruff/Black fixes required to register the file (mechanical, zero behavior change)

First time this exact code (the original coordinator, minus what Chunks
1-7 already moved out) was ever lint-checked:
- Import block sorted/blank-line-separated (`I001`, auto-fixed).
- A literal tab character mixed with spaces in one indented comment line
  (`if sigwidth == -999: <TAB><SPACES># poi=...`) and in one closing-paren
  line of a multi-line call (seven literal tabs before the paren) -
  both replaced with plain spaces (`W191`/`E101`).
- All `W291`/`W293` trailing/blank-line whitespace, auto-fixed.
- One genuinely dead local variable (`covariancedict`, `F841`) - removed,
  as above.
- Several long-line (`E501`) findings:
  - Two long "####...####" debug `print(...)` banner strings and three
    already-commented-out dead-code lines (a `shutil.copy2` pair, a
    `FindBHWindow.py` invocation, and one line of a commented-out `sed`
    command block) marked `# noqa: E501` rather than reformatted, per the
    same precedent established in Chunk 6.B's `run_fit.py` - preserving
    live debug output and dead-code text verbatim rather than rewriting
    strings for a line-length rule.
  - Two genuinely long *live* lines given real wraps, both verified
    byte-identical to the original by direct comparison in a Python shell
    before applying: the `maskrange=(int(...), int(...))` kwarg (split
    across three lines) and the live `quickLimit` command string
    (rewritten via implicit adjacent-string-literal concatenation,
    mirroring the identical technique already used for
    `run_fit.py`'s `xmlreader_command`/`quickfit_command` in Chunk 6.B
    and the Copilot-fix commit for `xmlreader_command`). The still-
    commented-out `#rtv=execute(...)` sibling line (the disabled
    `timeout --foreground 1800` variant) was left as dead-code text with
    `# noqa: E501`, not touched.
- `python -m black python/run_anaFit.py`: one further, large
  whitespace-only reformat - this file's original formatting (comma-
  packed single-line imports, tight `key=value` spacing, unindented
  multi-line call continuations) had never been through `black` before,
  unlike every other module extracted so far, which each got this same
  one-time reformat pass when first registered (Chunks 3.B, 5.B, 6.B,
  7.B). No `ast` diff beyond whitespace/formatting - confirmed by all
  tests below passing unchanged before and after.

### Acceptance check (run verbatim from the plan)

```
$ wc -l python/run_anaFit.py
292 python/run_anaFit.py

$ python -c "import ast, pathlib; tree = ast.parse(pathlib.Path('python/run_anaFit.py').read_text()); print(sorted({n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}))"
['main', 'run_anaFit']

$ grep -rn "^from run_anaFit import\|^import run_anaFit" python/run_execution.py python/run_manifest.py python/run_provenance.py python/run_masking.py python/run_templates.py python/run_fit.py python/run_cli.py
(no output - confirmed no reverse dependency)

$ grep -n "python/run_anaFit.py" scripts/quality_check.py
        "python/run_anaFit.py",
```

292 lines - larger than the plan's original "~60-100 lines" estimate
(Section 4's draft written before Chunks 1-7's actual signatures/kwargs
were known), but the acceptance check does not assert a line count, only
that the AST contains exactly `{'main', 'run_anaFit'}` - satisfied. The
extra size versus the estimate is legitimate orchestration: the masking
branch (BumpHunter refit, XML template copying/blinding, second
`build_fit_extract` call) and the quickLimit branch are real coordinator
logic that stays in `run_anaFit()` by design (Chunks 1-7's scope was the
seven named modules, not further decomposing the coordinator's own
control flow), plus `main()`'s CLI wiring and the still-inline
`--sysfile`-to-`systdict` logic (Chunk 7.B's own documented scope
boundary).

### Verification performed

- `python -m pytest tests/test_run_anaFit.py -v` → 16 passed.
- `python scripts/quality_check.py --mode full` → 158 passed, 2
  deselected; ruff clean; black clean (23 files unchanged) - the first
  time `run_anaFit.py` itself has ever passed this gate.
- `python -m pytest tests/ -m "not requires_analysis_dependencies and not (integration and requires_root)" -v`
  → 159 passed, 4 deselected. Section 2's original baseline (Chunk 0,
  commit range start) was 120 passed under the same filter - comfortably
  exceeds baseline plus the net new tests added across Chunks 1-8 and the
  four Copilot-fix commits.
- `python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`
  → 2 passed.
- `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
  → 1 passed in 152.04s, matching the frozen reference exactly - mandatory
  for this chunk per Section 7 (explicitly named alongside Chunks 4, 5,
  and always before 12).
- `git diff --check` → passed.
- `git status` → only `python/run_anaFit.py` and `scripts/quality_check.py`
  modified; no untracked repository-root artifacts from test execution.

### Compliance review (Section 8, Verification checklist)

1. Chunk 8 - a checkpoint/verification commit, not a characterization-
   then-extraction pair; no Step A/Step B split applies (guardrail 3
   explicitly does not apply here, per the plan's own Chunk 8 text).
2. `run_anaFit.py` re-read top to bottom; contains only imports,
   `run_anaFit()`, `main()`, and the `__main__` guard - confirmed by the
   plan's own AST-based acceptance check.
3. No dependency-direction violation: none of the seven extracted modules
   imports back from `run_anaFit.py` (confirmed by grep, above).
4. `python/run_anaFit.py` registered in `scripts/quality_check.py`'s
   `python_targets`; full gate passes with zero remaining findings in the
   coordinator itself.
5. Every fix in this commit is either a proven-dead-code removal (grepped
   for zero live uses before removing) or a proven byte-identical
   reformat/wrap (verified in a Python shell before applying, or a pure
   whitespace/import-order `black`/`ruff --fix` pass) - no behavior
   change; confirmed by the coordinator's own 16 tests and the full
   159-test suite passing unchanged.
6. Only this chunk's two changed files were staged.
7. All required Section 7 gates ran, including the mandatory integration
   gate, which passed and matched the frozen reference (above).
8. `git diff --check` passed; no untracked artifacts remain.
9. This activity-log entry appended (not a rewrite of any existing
   section).
10. Chunks 9 through 12 remain open, listed below.
11. No other branch's Tier 3 work was consulted.

### Remaining open chunks

Chunks 9 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open. All eight
module-extraction and coordinator-slimming chunks (1-8) are now complete
and verified.

## 2026-09-03: Tier-3 refactoring — Chunk 9.A: characterization tests for `plot_minuit_continuous`

### Objective

Pin down the current, unmodified behavior of `plot_minuit_continuous()`
in `plot_edm.py` (repository root) before splitting it into
`parse_minuit_edm_log()` and `plot_minuit_edm_trace()`, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 9. `plot_edm.py` has no existing
tests at all, so this is a first-ever characterization, not a relocation.

### A discrepancy between the plan and the actual dev environment, found before writing any test

The plan's Section 4.2 import-placement table lists `plot_edm.py` as
"already ROOT-free — matplotlib only" and places its imports "top-level"
- implicitly assuming matplotlib (and, transitively, the also-imported
`numpy`) is available wherever this file's tests run. Checked directly:
neither `matplotlib` nor `numpy` is installed in this repository's dev
venv, and neither appears in `requirements-dev-lock.txt` or
`requirements-dev.txt`. Confirmed by direct attempt:
`python -c "import matplotlib.pyplot"` and `python -c "import numpy"`
both raise `ModuleNotFoundError`, and `import plot_edm` itself fails at
module level for the same reason - **the current dev venv cannot import
this file at all**, today, regardless of any refactor.

This is the same situation this plan has already handled for ROOT
throughout Chunks 3, 5, and 6: `plot_edm.py` is only ever invoked as a
subprocess from within the LCG/CVMFS scientific environment (see
`run_fit.py`'s `execute("python plot_edm.py %s %s" % (logfile,
edmplot))` call) - the same environment that provides ROOT, not the
pytest dev venv. The plan's "top-level" placement note for this file's
imports is therefore corrected here: **Step B will defer `import
matplotlib.pyplot as plt` inside `plot_minuit_edm_trace()`** (the one
function that touches it), matching the import-placement rule already
applied to every ROOT-touching function elsewhere in this plan, not left
top-level as the draft table said. This test file stubs
`sys.modules["matplotlib"]`/`["matplotlib.pyplot"]`/`["matplotlib.cm"]`/
`["numpy"]` the same way `test_run_anaFit.py`/`test_run_provenance.py`
already stub `ROOT`, so these characterization tests exercise real,
verifiable behavior (see below) without needing matplotlib installed.

### A second discrepancy: two of the three top-level imports are already dead

`import numpy as np` and `import matplotlib.cm as cm` are both present in
`plot_edm.py` today but neither `np.` nor `cm.` appears anywhere in the
function body - confirmed by direct grep. Only `matplotlib.pyplot` (as
`plt`) is actually used. Noted here for Step B (removing genuinely dead
imports on newly-registered files is this project's established
practice, e.g. Chunk 8's `run_anaFit.py` cleanup) rather than acted on in
this characterization-only commit.

### Target function (as it exists today)

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `plot_minuit_continuous(filename, outname)` | `filename: str` (quickFit log path), `outname: str` | `None` | reads `filename`; prints "Error: The file was not found." and `sys.exit(1)` if missing; prints "No matching data found." and returns early if the log has no Minuit trace lines; otherwise builds and saves a matplotlib figure to `outname` via `plt.savefig(outname, bbox_inches="tight")` |

### How the fake `matplotlib.pyplot` was built, and what it actually proves

The stub module records every `savefig(outname, **kwargs)` call and
**actually writes bytes to `outname`** (a real file, not just a recorded
call), so file-existence/non-emptiness assertions below are testing a
real filesystem effect, not merely "the stub was invoked." Every other
`pyplot` function used (`figure`, `plot`, `axhline`, `yscale`, `xscale`,
`xlabel`, `ylabel`, `title`, `grid`, `legend`) is a permissive no-op,
since their exact call arguments are not part of this file's documented
external contract.

### Tests added (`tests/test_plot_edm.py`, new file)

- `test_plot_minuit_continuous_produces_output_file_for_log_with_trace_lines` -
  a small synthetic log with four matching `VariableMetricBuilder ... -
  FCN = ... Edm = ... NCalls` lines (including two with internal
  iteration `0`, to exercise the star-index branch); asserts the output
  file exists, is non-empty, and that `savefig` was called with exactly
  `(outname, {"bbox_inches": "tight"})`.
- `test_plot_minuit_continuous_produces_output_for_real_quickfit_log` -
  uses the real, already-committed
  `run/fits/J100/run_481_3000_sixPar/quickFitLog_anaFit_sixPar_bkgOnly.log`
  fixture the plan calls out explicitly; asserts a non-empty output file
  is produced from genuine production log data, not just a synthetic one.
- `test_plot_minuit_continuous_no_output_when_no_matching_lines` - a log
  with no matching trace lines; asserts no exception, no output file
  created, `savefig` never called, and `"No matching data found."`
  actually printed (not just "does not raise").
- `test_plot_minuit_continuous_exits_with_status_1_for_missing_file` - a
  nonexistent input path; asserts `SystemExit` with `.code == 1`,
  `savefig` never called, and `"Error: The file was not found."` actually
  printed.

The regex-parsed values used in the synthetic-log test (`cumulative_x`,
`edm_values`, `star_indices`) were verified directly in a Python shell
against the real `pattern.search(...)` regex before being relied on in
the fixture, rather than hand-derived (the lesson already learned the
hard way in Chunk 5.A).

### What this commit does NOT do

No production file was modified. `git status --short` shows only
`tests/test_plot_edm.py` as untracked (new); `plot_edm.py` itself is
absent from `git diff --stat` because it was never touched. The new test
file is **not yet** registered in `scripts/quality_check.py` - per the
plan, that happens in Step B alongside `plot_edm.py` itself.

### Verification performed

- `python -m pytest tests/test_plot_edm.py -v` → 4 passed, run against
  the unmodified `plot_edm.py`.
- `python scripts/quality_check.py --mode full` → 158 passed, 2
  deselected; ruff clean; black clean (23 files unchanged) - unaffected,
  confirming the new file doesn't touch anything already gated.
- `python -m ruff check tests/test_plot_edm.py` /
  `python -m black --check tests/test_plot_edm.py` → both clean already
  (run ahead of Step B's registration, so the file starts clean).
- `git diff --check` → passed.
- `grep -nE '[[:blank:]]+$' tests/test_plot_edm.py` → no output.

### Compliance review (Section 8, Characterization checklist)

1. Chunk 9, Step A.
2. `plot_edm.py` untouched; only `tests/test_plot_edm.py` (new, untracked)
   added.
3. Every new test asserts real, specific behavior (exact `savefig` call
   arguments, exact printed messages, exact exit code) - not merely "does
   not raise."
4. Tests were run against the unmodified target file before any
   production change; results reported in full above for review.
5. Human-verification checkpoint: presented to the user in session for
   confirmation before Step B's commit is made (recorded per Step B's own
   activity-log entry once given).

### Remaining open chunks

Chunk 9.B (extraction of `parse_minuit_edm_log`/`plot_minuit_edm_trace`)
and Chunks 10 through 12 are open.

## 2026-09-03: Tier-3 refactoring — Chunk 9.B: extract `parse_minuit_edm_log`/`plot_minuit_edm_trace`

### Objective

Split `plot_minuit_continuous()`, characterized in Chunk 9.A (commit
`de11262`), into `parse_minuit_edm_log()` (log parsing) and
`plot_minuit_edm_trace()` (matplotlib rendering), per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 9 - separating pure, trivially
unit-testable logic from rendering that needs matplotlib.

### What changed

- `plot_edm.py`:
  - `parse_minuit_edm_log(filename)` (new) - the regex-parsing loop,
    moved verbatim, returning `(cumulative_x, edm_values, star_indices)`.
    **Decision required by the plan and recorded here** (to be folded
    into `doc/TIER3_SYSTEM.md` at Chunk 12): the original function caught
    `FileNotFoundError` itself and called `sys.exit(1)`; this function
    instead lets `FileNotFoundError` propagate naturally from `open(...)`
    - a pure, directly-callable function should not terminate the whole
    process, and doing so made it awkward to test (every caller would
    need `pytest.raises(SystemExit)` instead of a plain, specific
    exception type). `plot_minuit_continuous()` (below) is the thin
    CLI-facing wrapper that still does the print + `sys.exit(1)`,
    preserving the exact external behavior Chunk 9.A characterized.
  - `plot_minuit_edm_trace(cumulative_x, edm_values, star_indices,
    outname)` (new) - the rendering code, moved verbatim, including the
    "No matching data found." early return (moved here per the plan's own
    target-decomposition table) and every commented-out dead line
    (`#    plt.xscale('log')`, the three commented `#print(...)`
    diagnostics, etc.), preserved exactly.
  - `plot_minuit_continuous(filename, outname)` - now a thin orchestrator:
    calls `parse_minuit_edm_log()`, catching `FileNotFoundError` to
    reproduce the original print + `sys.exit(1)`, then calls
    `plot_minuit_edm_trace()`. Signature unchanged, per the plan.
  - `import matplotlib.pyplot as plt` deferred inside
    `plot_minuit_edm_trace()`, **placed after the empty-data early
    return**, not before it - a placement choice beyond what Chunk 9.A's
    entry committed to: it means the "no matching data" path through
    `plot_minuit_edm_trace()` (and, transitively, through
    `plot_minuit_continuous()`) needs **zero** matplotlib stubbing, not
    just `parse_minuit_edm_log()`. Confirmed directly: `import plot_edm`
    and calling `plot_edm.plot_minuit_edm_trace([], [], [], path)` both
    succeed with no `sys.modules` stubbing at all, verified before
    committing.
  - `import matplotlib.cm as cm` and `import numpy as np` removed - both
    confirmed dead in Chunk 9.A's entry (zero live uses), and this is the
    first time the file is lint-checked.
  - One `E501` fix: the regex pattern literal wrapped across two raw
    string literals (verified byte-identical `.pattern` before applying).
  - `python -m black plot_edm.py`: one further, first-ever reformat pass
    (quote style, argument wrapping) - matching every other
    newly-registered file in this plan.
- `tests/test_plot_edm.py`: rewritten - the module-loading helper that
  stubbed `matplotlib`/`numpy` in `sys.modules` before `exec_module`-ing
  the file is **gone entirely**, replaced with a plain `import plot_edm`
  at the top of the file - the concrete testability payoff the plan
  promised for this decomposition. Only the two tests that actually reach
  `plot_minuit_edm_trace()`'s non-empty-data path still stub
  `matplotlib`/`matplotlib.pyplot` (via a smaller, module-scoped
  `_stub_matplotlib()` helper, `matplotlib.cm` no longer stubbed since
  it's no longer imported); the other five tests - both empty-data paths,
  both `parse_minuit_edm_log()` failure/empty cases, and the
  missing-file/`SystemExit` case - now run with zero stubbing.
- `scripts/quality_check.py`: registers `plot_edm.py` (in `python_targets`,
  at repository-root path, not under `python/`) and `tests/test_plot_edm.py`.

### Necessary test-relocation adaptation and new coverage (guardrail 4)

Chunk 9.A's four tests were adapted, not moved wholesale - the module-
loading mechanism itself changed (see above), and one test
(`test_plot_minuit_continuous_no_output_when_no_matching_lines`) dropped
its `matplotlib` stub entirely as a direct, intended consequence of the
import-placement decision. No assertion or expected value changed from
Chunk 9.A. Five new tests were added for the two newly-introduced
functions, per guardrail 4:
- `parse_minuit_edm_log()`: exact-tuple success case (reusing Chunk 9.A's
  already-verified synthetic-log values), empty-result case, and the
  `FileNotFoundError`-propagates case (the decision above).
- `plot_minuit_edm_trace()`: non-empty-data success case (asserts the
  exact `savefig` call, same as the orchestrator-level test) and the
  empty-data early-return case (asserts the message and that no file is
  created, with zero stubbing).

### Verification performed

- `python -m pytest tests/test_plot_edm.py -v` → 9 passed (4 adapted from
  Chunk 9.A plus 5 new).
- `python scripts/quality_check.py --mode full` → 167 passed, 2
  deselected; ruff clean; black clean (25 files unchanged).
- `git diff --check` → passed.
- No integration-gate rerun: `plot_edm.py`'s output is a diagnostic plot,
  already outside the scientific-acceptance artifact contract per the
  2026-08-20 "Plotting separated from scientific acceptance" entry,
  matching the plan's own explicit acceptance-check note for this chunk.

### Compliance review (Section 8, Extraction checklist)

1. Chunk 9, Step B (this entry) - the plan's first non-`run_anaFit.py`
   extraction.
2. Step A is committed (`de11262`) and referenced above.
3. No scientific constants, references, tolerances, dependency revisions,
   or canonical workflow arguments touched.
4. Relocated tests' diffs are not import-line-only - the module-loading
   mechanism itself changed (real `import plot_edm` instead of
   `exec_module`-with-stubbing), and one test's stub was dropped entirely
   as a direct, documented consequence of the import-placement decision;
   no assertion or expected value changed from Chunk 9.A.
5. Both new functions are covered: `parse_minuit_edm_log()` (3 tests:
   success, empty, failure) and `plot_minuit_edm_trace()` (2 tests:
   success, empty).
6. Confirmed by grep: `plot_edm.py`'s `plot_minuit_continuous()` calls
   both new functions and defines nothing else duplicating their logic.
7. Only this chunk's three changed files were staged.
8. All required Section 7 gates ran; the integration gate's inapplicability
   to this chunk is explicit in the plan itself, not a judgment call made
   here.
9. `git diff --check` passed.
10. This activity-log entry appended (not a rewrite of any existing
    section).
11. Chunks 10 through 12 remain open, listed below.
12. No other branch's Tier 3 work was consulted.

### Remaining open chunks

Chunks 10 through 12 in `doc/TIER3_COMPLETION_PLAN.md` are open.

## 2026-09-03: Correction — Chunk 9.B entry miscounted matplotlib-stubbing tests (GitHub Copilot review, PR #6)

### What Copilot found

The Chunk 9.B entry above (`tests/test_plot_edm.py` bullet) says "the
two tests that actually reach `plot_minuit_edm_trace()`'s non-empty-data
path still stub `matplotlib`/`matplotlib.pyplot` ... the other five tests
... now run with zero stubbing." Checked directly against
`tests/test_plot_edm.py` as committed: `_stub_matplotlib(monkeypatch)` is
called by **three** tests
(`test_plot_minuit_edm_trace_produces_output_file_for_non_empty_data`,
`test_plot_minuit_continuous_produces_output_file_for_log_with_trace_lines`,
`test_plot_minuit_continuous_produces_output_for_real_quickfit_log`), not
two - confirmed by grepping the test file for the call site (three
matches). The remaining **six** tests (not five) run with zero stubbing.
Three plus six correctly sums to the file's actual nine tests; two plus
five does not (seven), which is itself a smaller internal inconsistency
in the original entry, also caught by this same review comment.

### Correction

The counts should read: **three** tests stub matplotlib (the two
`plot_minuit_continuous(...)` tests that reach real trace data, plus
`test_plot_minuit_edm_trace_produces_output_file_for_non_empty_data`
directly), and the other **six** tests - both `plot_minuit_edm_trace()`/
`plot_minuit_continuous()` empty-data paths, all three
`parse_minuit_edm_log()` cases (success, empty, missing-file), and the
`plot_minuit_continuous()` missing-file/`SystemExit` case - run with zero
stubbing.

This is a correction to prose in the Chunk 9.B entry's own description of
already-committed, unchanged test code - no test or production file was
touched to produce this finding or this correction. Per the activity
log's append-only guardrail, the original entry is left exactly as
written above; this section is the correction of record.

## 2026-09-03: Tier-3 refactoring — Chunk 10.A: characterization tests for `python/plotPostFit.py`

### Objective

Pin down the current, unmodified behavior of `python/plotPostFit.py`
before splitting it into functions, per `doc/TIER3_COMPLETION_PLAN.md`
Chunk 10. The file has zero functions today — the entire 79-line file is
top-level script code (`import ROOT` at module scope, then a linear
sequence of `argparse`/`ROOT.TFile`/`TCanvas` calls) — so, per Chunk 10's
own instruction, Step A's characterization runs the current script
**end-to-end as a subprocess**, since there is nothing importable to call
directly yet.

### A discrepancy between the plan and this dev environment, found before writing the test

`plotPostFit.py` does `import ROOT` at module scope. Confirmed directly:
`.venv/bin/python -c "import ROOT"` raises `ModuleNotFoundError` in this
repository's dev venv — the same situation already documented for
`plot_edm.py` in the Chunk 9.A entry above, except here it cannot be
worked around with `sys.modules` stubbing, because Step A's own
characterization strategy (per the plan) is to run the *whole script* as
a subprocess against a real ROOT file and assert on its real output — the
point is to exercise genuine `ROOT.TFile`/`TCanvas`/`TPad` behavior, not a
stand-in for it. `plotPostFit.py` is only ever invoked in production
after `scripts/setup_buildAndFit.sh` has been sourced (see
`scripts/run_anaFit_J100.sh`/`run_anaFit_J50.sh`, both of which run
`python "$repo_dir/python/plotPostFit.py" -i ... -o ...` after sourcing
that script), which puts the LCG/CVMFS-provided `python` (with `ROOT`
importable) on `PATH` — not this repository's own pytest dev venv. The
new test therefore sources `scripts/setup_buildAndFit.sh` itself inside a
`subprocess.run(["bash", "-lc", ...])` call before invoking the script,
mirroring the exact probe pattern already established by
`test_analysis_workflows_integration.py::test_authoritative_setup_provides_scientific_runtime`.
Run directly against this host's actual CVMFS/LCG environment, it passes
for real — this is not a mocked assertion.

### Target script (as it exists today)

| Entry point | Inputs | Outputs | Side effects |
|---|---|---|---|
| `python plotPostFit.py -i <inputFile> -o <output>` (whole script, no functions) | `-i/--inputFile: str` (a `PostFit_*.root` file), `-o/--output: str` | none (process exit code only) | opens `inputFile` via `ROOT.TFile.Open`; reads `Run3TLA/postfit`, `Run3TLA/data`, `Run3TLA/chi2`; builds a two-pad `TCanvas` (postfit-vs-data overlay + data/postfit ratio); writes `output` via `TCanvas.SaveAs`; closes `inputFile` |

### Tests added (`tests/test_plot_post_fit.py`, new file)

- `test_plot_post_fit_script_produces_nonempty_pdf_for_real_fixture` —
  runs the real, unmodified script as a subprocess (via the
  `setup_buildAndFit.sh`-sourcing probe described above) against the
  already-committed
  `run/fits/J100/run_481_3000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root`
  fixture, writing to a `tmp_path` output; asserts the process exits `0`
  and the output PDF exists and is non-empty.

Per the plan's own instruction, **byte-identical PDF comparison is
deliberately not attempted**: ROOT's PDF output is not guaranteed
bit-reproducible across environments/fonts, and Tier 1 already
established (2026-08-20 activity-log entry, "Plotting separated from
scientific acceptance") that PDF artifacts are excluded from strict
scientific comparison. "Runs successfully against a real fixture and
produces a real, non-empty plot" is the chosen, and only, characterized
invariant — recorded here explicitly so a future reader does not expect
stronger guarantees than this step provides.

### A marker decision, recorded so Step B doesn't have to re-derive it

The new test is marked `@pytest.mark.requires_root` only (not also
`requires_analysis_dependencies`). Per `doc/TIER2_SYSTEM.md`'s own marker
definitions, `requires_root` means "needs the configured ROOT/RooFit
runtime" and `requires_analysis_dependencies` means "needs prepared
external checkouts" (built `XMLReader`/`quickFit`/`pyBumpHunter`
binaries). `plotPostFit.py` needs only a working ROOT/RooFit runtime
(via `scripts/setup_buildAndFit.sh`) — it never invokes `XMLReader`,
`quickFit`, or BumpHunter. `doc/TIER2_SYSTEM.md` states the ordinary gate
("`python scripts/quality_check.py --mode full`") excludes only
`requires_analysis_dependencies`-marked tests, not `requires_root`-marked
ones — so, once Step B registers this file in `scripts/quality_check.py`,
this test is expected to actually run (and pass) as part of the ordinary
full gate on a host with the scientific runtime configured, exactly like
every other already-registered test file in this plan. This matches the
project's existing baseline assumption (`scripts/quality_check.py`'s own
`REQUIRED_BASELINE_PATHS`/`_print_optional_workflow_hints` checks) that
the J100/J50 scientific environment is present, not an optional extra.

### What this commit does NOT do

No production file was modified. `git status --short` shows only
`tests/test_plot_post_fit.py` as untracked (new); `git diff --stat` is
empty — `python/plotPostFit.py` itself was never touched. The new test
file is **not yet** registered in `scripts/quality_check.py` — per the
plan, that happens in Step B alongside `python/plotPostFit.py` itself.

### Verification performed

- `python -m pytest tests/test_plot_post_fit.py -v` → 1 passed (run for
  real against this host's actual CVMFS/LCG scientific runtime, in
  13.81s).
- `python scripts/quality_check.py --mode full` → 167 passed, 2
  deselected; ruff clean; black clean (25 files unchanged) — unaffected,
  confirming the new file doesn't touch anything already gated.
- `python -m ruff check tests/test_plot_post_fit.py` /
  `python -m black --check tests/test_plot_post_fit.py` → both clean
  already (run ahead of Step B's registration, so the file starts clean).
- `git diff --check` → passed.
- `git diff --stat` → empty (no production file touched).
- `grep -nE '[[:blank:]]+$' tests/test_plot_post_fit.py` → no output.

### Compliance review (Section 8, Characterization variant)

1. Chunk 10, Step A.
2. `python/plotPostFit.py` untouched; only `tests/test_plot_post_fit.py`
   (new, untracked) added.
3. The new test asserts real, specific behavior (real process exit code,
   real non-empty PDF file on disk from a real ROOT fixture) — not merely
   "does not raise."
4. The test was run against the unmodified target file, for real, against
   this host's actual scientific runtime, before any production change;
   the exact result (1 passed, 13.81s) is reported above for review.
5. Human-verification checkpoint: presented to the user in session for
   confirmation before Step B's commit is made (recorded per Step B's own
   activity-log entry once given).

### Remaining open chunks

Chunk 10.B (extraction of `parse_args`/`load_postfit_histograms`/
`build_ratio_histogram`/`draw_postfit_canvas`/`main`) and Chunks 11
through 12 are open.

## 2026-09-03: Tier-3 refactoring — Chunk 10.B: extract functions from `python/plotPostFit.py`

### Objective

Move `python/plotPostFit.py`'s top-level script code, characterized and
human-verified in Step A (commit `d24d5bf`), into five functions plus a
`main()` and an `if __name__ == "__main__":` guard, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 10.

### What changed

- `python/plotPostFit.py` restructured in place into:
  - `PostfitHistograms` — a `typing.NamedTuple` of `(postfit, data, chi2)`.
  - `parse_args(argv=None)` — the two `argparse` arguments, moved verbatim
    into a function, `parser.parse_args(argv)` instead of
    `parser.parse_args()` so it is callable with an explicit argument list
    in tests, matching the pattern already used for `run_cli.py`'s
    `build_arg_parser()`.
  - `load_postfit_histograms(input_file)` — opens `input_file`, reads
    `Run3TLA/postfit`/`Run3TLA/data`/`Run3TLA/chi2`, applies the same
    marker/line styling the original script applied inline, moved
    verbatim.
  - `build_ratio_histogram(data, postfit)` — the `h_ratio = data.Clone(...);
    h_ratio.Divide(postfit)` block and all of its styling calls, moved
    verbatim.
  - `draw_postfit_canvas(data, postfit, chi2_hist, ratio_hist)` — the
    two-pad canvas, legend, and χ²/ndof text block, moved verbatim (one
    string-formatting rewrite, see below); returns the built `TCanvas`
    without saving it.
  - `main(argv=None)` — orchestrates the above: sets
    `ROOT.gStyle.SetOptStat(0)`/`ROOT.gROOT.SetBatch(True)` (moved out of
    module scope, see decision below), calls `parse_args`, then
    `load_postfit_histograms`, `build_ratio_histogram`,
    `draw_postfit_canvas` in order, then `canvas.SaveAs(args.output)` and
    `postfit_file.Close()`.
  - `if __name__ == "__main__": main()` guard.
- `scripts/quality_check.py`: `python/plotPostFit.py` and
  `tests/test_plot_post_fit.py` added to `python_targets`/`test_targets`
  (alphabetically, next to `python/analysis_reference.py` and
  `tests/test_plot_edm.py` respectively).
- Step A's end-to-end test
  (`test_plot_post_fit_script_produces_nonempty_pdf_for_real_fixture`)
  kept, unchanged, in `tests/test_plot_post_fit.py` — it is now a
  regression test of `main()`'s CLI contract, still valuable (the Test
  Relocation Rule does not apply here: this test never imported the
  production file, it always ran it as a subprocess, so there is no
  import line to update and nothing else to change).
- Five new tests added for the newly-introduced functions (listed below).

### A real, verified bug the plan's own table would have introduced: ROOT file lifetime

The plan's Section 6 target-decomposition table lists
`load_postfit_histograms(input_file)`'s output as just the
`PostfitHistograms` triple. Implemented and tested literally as written
first, then verified directly against the real fixture file, in this
host's actual scientific runtime (not simulated): once the function
returns and its own local `TFile` reference goes out of scope with no
other reference held, calling `.GetEntries()`/any other method on the
returned histograms fails with `AttributeError: 'CPyCppyy_NoneType'
object has no attribute 'GetEntries'` — the file is garbage-collected
before the histograms are used, invalidating them. The original,
single-scope script never hit this, because its `postfit_file` stayed
alive as a script-level name for the entire run; splitting it into a
function that returns only the histograms introduces a new object-
lifetime hazard that did not exist before. **Corrected the plan's
literal table**: `load_postfit_histograms()` returns
`(PostfitHistograms, postfit_file)` — the still-open `TFile` alongside
the triple — and `main()` holds that reference until after
`canvas.SaveAs(...)`, then calls `postfit_file.Close()`, exactly
mirroring the original script's object lifetime. This was verified two
ways: (1) a standalone reproduction script matching the plan's literal
signature, run for real, reproducing the crash; (2) the new
`test_load_postfit_histograms_applies_styling_and_keeps_file_open` test
below, confirmed to fail against the literal (unfixed) version — reverted
locally, observed a real `ValueError: too many values to unpack` at the
unpacking call site once `main()`'s own call was also downgraded to match
— and to pass against the fixed version once restored.

### A second decision, recorded per the plan's own instruction

The plan's table asks Step B to "decide whether styling stays in
[`load_postfit_histograms`] or moves to a separate
`style_postfit_histograms()`, and record the decision." Decision: styling
(`data`/`postfit`'s marker/line style) **stays inside**
`load_postfit_histograms()`. It is applied immediately and unconditionally
to every histogram this function loads, with no call site needing the
unstyled objects first — unlike `run_templates.py`'s Chunk 5 decomposition
(`_stage_xml_templates`/`_seed_prefit_parameters`), where splitting served
a real, independent testability or reuse need, a separate
`style_postfit_histograms()` here would only relocate four `Set*()` calls
without changing what is tested or reused.

### A third, related decision: where `ROOT.gStyle.SetOptStat(0)`/`ROOT.gROOT.SetBatch(True)` now live

The original script executed these two calls at **import time**, before
`argparse` even ran. The plan's decomposition table has no dedicated
"setup" function for them, and logically they belong wherever `main()`'s
orchestration begins — moved to the top of `main()`, called before
`parse_args()`, preserving the exact original ordering relative to
everything else. For the one real production call path (`python
plotPostFit.py -i ... -o ...`, which always reaches `main()` via the
`if __name__ == "__main__":` guard), behavior is unchanged bit-for-bit.
The only behavioral difference is for a hypothetical bare `import
plotPostFit` with `main()` never called — which nothing in this
repository does (confirmed by `grep -rn "plotPostFit"` across the whole
repository: only the two shell launchers invoke it, both as a
subprocess). This is also a direct, verified testability payoff:
`tests/test_plot_post_fit.py`'s `parse_args()` tests import the module
with a bare, attribute-less `ROOT` stub (nothing beyond the module name
needs to resolve) precisely because no ROOT attribute is touched at
import time any more.

### A verified byte-identical string-formatting rewrite

`draw_postfit_canvas()`'s χ²/ndof text was built with implicit
concatenation (`string = "#chi^{2}/ndof = "; string += f"{rchi2:.3f}"`);
rewritten as a single f-string,
`f"#chi^{{2}}/ndof = {rchi2:.3f}"`. Verified byte-identical in a live
Python shell for a representative value (`rchi2 = 12.34567`) before
relying on it — both forms produce `'#chi^{2}/ndof = 12.346'`.

### New tests added (`tests/test_plot_post_fit.py`)

- `test_parse_args_parses_required_flags`,
  `test_parse_args_accepts_long_flags`,
  `test_parse_args_requires_both_flags` (parametrized: no args, only
  `-i`, only `-o`) — zero real ROOT: `parse_args()` never touches it, so
  these import the module with a bare, attribute-less `ROOT` stub in
  `sys.modules` (mirroring `test_run_anaFit.py`'s established stubbing
  style) and call `parse_args()` directly.
- `test_load_postfit_histograms_applies_styling_and_keeps_file_open` —
  real ROOT, run as a subprocess snippet (after sourcing
  `scripts/setup_buildAndFit.sh`, mirroring
  `test_authoritative_setup_provides_scientific_runtime`'s probe
  pattern) against the same real fixture Step A used; asserts every
  styling call's exact effect (marker style/size/color, line
  width/color) and that the returned `postfit_file` is still open with
  usable histograms — the direct regression test for the file-lifetime
  fix above.
- `test_build_ratio_histogram_computes_real_ratio_and_styling` — per the
  plan's own instruction, uses small real `ROOT.TH1D` objects built
  in-test (no input file needed); asserts the actual computed ratio bin
  contents (`10/5=2.0`, `20/40=0.5`) and every styling call's exact
  effect, not just "was called."
- `test_draw_postfit_canvas_returns_two_pad_canvas` — small real
  `ROOT.TH1D`/`build_ratio_histogram()` output; asserts the returned
  object `isinstance(..., ROOT.TCanvas)` and that its primitives include
  pads named exactly `pad1`/`pad2`.

All four new real-ROOT assertions (styling values, ratio bin contents,
axis titles/divisions, marker style, pad names) were independently
verified in a live, real-ROOT shell against this host's actual scientific
runtime before being relied on in the tests, rather than hand-derived.

### Confirm: no scientific behavior changed

`plotPostFit.py` produces plots, not scientific acceptance results — it
is excluded from the frozen `analysis_reference.json` contract (Tier 1,
"Plotting separated from scientific acceptance"). Every ROOT call, in the
same order, with the same arguments, was moved verbatim into its new
function (the two deviations above — the returned `TFile` handle and the
`gStyle`/`gROOT` call site — are both non-scientific, plot-only
concerns, not fit/statistics logic, and both were verified empirically
to reproduce the exact original end-to-end output: a real, non-empty
PDF from the real J100 fixture, `python
plotPostFit.py -i run/fits/J100/run_481_3000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root
-o <tmp>` → exit 0, `<tmp>` created and non-empty, run directly against
this host's real scientific runtime after this commit's change, not
just via the test suite).

### Verification performed

- `python -m pytest tests/test_plot_post_fit.py -v` → 9 passed (46.87s),
  run for real against this host's actual CVMFS/LCG scientific runtime.
- `python scripts/quality_check.py --mode full` → 176 passed, 2
  deselected; ruff clean; black clean (27 files unchanged).
- `python -m pytest tests/test_analysis_workflows_integration.py -m
  "integration and requires_root" -v` → 1 passed, 2 deselected, in
  145.24s (run in the background per this session's established practice
  for this specific command, which regularly exceeds the foreground tool
  timeout; this chunk is not one of Section 7's chunks where this gate is
  strictly mandatory, but it is rerun here anyway as an extra safety net,
  since this chunk changed real ROOT object-lifetime control flow — it
  confirms the J100/J50 authoritative workflows, which both invoke
  `plotPostFit.py`, still match the frozen scientific reference).
- `git diff --check` → passed.
- `grep -nE '[[:blank:]]+$' python/plotPostFit.py tests/test_plot_post_fit.py scripts/quality_check.py` →
  no output.
- `grep -n "plotPostFit" scripts/run_anaFit_J100.sh scripts/run_anaFit_J50.sh` →
  both launchers' invocations (`python "$repo_dir/python/plotPostFit.py"
  -i ... -o ...`) unchanged, confirming the public CLI contract this
  refactor must not break.

### Compliance review (Section 8, Extraction variant)

1. Step A's commit (`d24d5bf`) is named above; this commit's Step A test
   is kept unchanged, and five new tests are added for the newly-
   introduced functions — none of the five are relocated, all are new.
2. `tests/test_plot_post_fit.py`'s Step A test required no diff beyond
   its position in the file (no import line existed to change, since it
   was always subprocess-based).
3. Production code (the two shell launchers) is unchanged and still
   calls the script's unchanged public CLI contract — confirmed by grep,
   not assumed.
4. `python/plotPostFit.py` does not import from `run_anaFit.py` or any
   of the seven extracted `run_anaFit.py` modules — it was never part of
   that module system; it is its own standalone script under `python/`.
5. Required Section 7 gates ran; output captured above.
6. Activity-log entry appended (this content), not a rewrite of any
   existing section.

### Remaining open chunks

Chunk 11 (`plot_postfit.cpp`) and Chunk 12
(`doc/TIER3_SYSTEM.md`) are open.

## 2026-09-03: Fix plot_post_fit real-ROOT tests failing in CI (no CVMFS mount)

### Objective

The GitHub Actions CI run for this branch (`ubuntu`-hosted runner,
`/home/runner/work/FrequentistFramework/FrequentistFramework`) reported
`quality_check.py --mode full` failing with 4 real failures in
`tests/test_plot_post_fit.py`:
`test_load_postfit_histograms_applies_styling_and_keeps_file_open`,
`test_build_ratio_histogram_computes_real_ratio_and_styling`,
`test_draw_postfit_canvas_returns_two_pad_canvas`, and
`test_plot_post_fit_script_produces_nonempty_pdf_for_real_fixture` — each
failing with `scripts/setup_buildAndFit.sh: line 12:
/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/user/atlasLocalSetup.sh: No
such file or directory`. This is a genuine, verified environment gap, not
a false report: the GitHub Actions runner has no CVMFS mount at all, so
any test that actually sources `scripts/setup_buildAndFit.sh` cannot pass
there, regardless of ROOT/RooFit correctness.

### The actual bug: an incorrect marker decision in Chunk 10.A/10.B

Chunk 10.A's activity-log entry recorded a marker decision: mark these
tests `@pytest.mark.requires_root` only, reasoning from
`doc/TIER2_SYSTEM.md`'s literal marker definitions ("`requires_root`:
needs the configured ROOT/RooFit runtime", "`requires_analysis_dependencies`:
needs prepared external checkouts") that a test needing only ROOT (not
built `XMLReader`/`quickFit`/`pyBumpHunter` binaries) should not need the
second marker. **This reasoning was wrong in practice**: it did not
account for `test_authoritative_setup_provides_scientific_runtime` (in
`tests/test_analysis_workflows_integration.py`) already being marked
**both** `@pytest.mark.requires_root` and
`@pytest.mark.requires_analysis_dependencies`, despite doing exactly the
same thing these four new tests do - sourcing
`scripts/setup_buildAndFit.sh` in a subprocess. That existing precedent
should have been followed literally instead of re-derived abstractly from
the marker-name definitions. The real, load-bearing distinction is not
"does it need XMLReader/quickFit/pyBumpHunter" but "does it need CVMFS
mounted at all" - and every test that sources
`scripts/setup_buildAndFit.sh` needs CVMFS, full stop.

This bug only surfaced in CI, not in this developer's own session, because
this session's environment (`afs.cern.ch`, with CVMFS mounted) satisfies
both markers' conditions simultaneously - `requires_root` alone was
sufficient there to reach a real, working ROOT runtime, masking the
missing `requires_analysis_dependencies` marker's actual purpose (keeping
the test out of the *ordinary*, CVMFS-less CI gate in the first place).

### Fix

Added `@pytest.mark.requires_analysis_dependencies` alongside the
existing `@pytest.mark.requires_root` on all four real-ROOT tests in
`tests/test_plot_post_fit.py` (the three added in Chunk 10.B, plus the
end-to-end test carried over unchanged from Chunk 10.A/Step A). No test
body, fixture, or assertion changed - only the marker decorators. This
matches `test_authoritative_setup_provides_scientific_runtime`'s own
markers exactly, and restores `doc/TIER2_SYSTEM.md`'s stated contract:
"the ordinary gate excludes tests marked `requires_analysis_dependencies`
and does not include the integration test file."

`test_parse_args_*` (5 tests) are unaffected - they never touch ROOT or
CVMFS and continue to run in the ordinary gate, exactly as they did in
CI's own run (`.....FFFF` in the CI log: 5 passes, then the 4 real-ROOT
failures, confirming the split was already correct for those five).

### Verification performed

- `python -m pytest tests/test_plot_post_fit.py -v` (no marker filter,
  matching Chunk 10's own acceptance check, run for real against this
  host's actual CVMFS/LCG scientific runtime) → 9 passed (46.38s) -
  unaffected by the marker-only change.
- `python -m pytest -m "not requires_analysis_dependencies"
  tests/test_plot_post_fit.py -v` (reproducing `quality_check.py`'s own
  filter, matching what CI actually runs) → 5 passed, 4 deselected - the
  four CVMFS-dependent tests are now correctly excluded from exactly the
  gate that failed in CI.
- `python scripts/quality_check.py --mode full` → 172 passed, 6
  deselected (2 pre-existing + these 4, newly and correctly excluded);
  ruff clean; black clean (27 files unchanged).
- `git diff --check` → passed.
- `grep -nE '[[:blank:]]+$' tests/test_plot_post_fit.py` → no output.

### What this commit does NOT do

Does not touch `python/plotPostFit.py` (production code) at all - this is
a test-marker-only fix. Per the append-only guardrail, Chunk 10.A's and
10.B's entries above are left exactly as written, including 10.A's now-
superseded "marker decision" reasoning and 10.B's verification section
(which reported results from this developer's own CVMFS-mounted session,
still accurate for that environment) - this section is the correction of
record for what CI itself actually needs.

## 2026-09-03: Fix plotPostFit.py's module-level ROOT coupling and a real legend-lifetime bug (GitHub Copilot review, PR #6)

### Finding 1: `parse_args()` still needed ROOT to import

Copilot: "The extracted `parse_args()` API is still impossible to import
in the repository's ROOT-less Python environment because ROOT is
imported unconditionally here. This also conflicts with Chunk 10's
explicit requirement that `parse_args()` be tested with zero stubbing;
the new tests only pass by injecting a fake ROOT module. Please defer
ROOT imports to the ROOT-dependent functions."

Verified: correct. `python/plotPostFit.py` had `import ROOT` at module
scope (left there after Chunk 10.B's own decision to move
`ROOT.gStyle`/`ROOT.gROOT.SetBatch()` into `main()`, without going the
rest of the way and deferring the bare `import ROOT` statement itself).
`doc/TIER3_COMPLETION_PLAN.md`'s own Chunk 10 text states `parse_args()`
"needs no ROOT at all and should be tested with zero stubbing" -
Chunk 10.B's tests instead stubbed `sys.modules["ROOT"]` with a bare
`ModuleType`, satisfying the letter of "the module imports" but not
"zero stubbing."

Fix: removed the module-level `import ROOT` entirely. `import ROOT` is
now deferred inside each function that actually touches it -
`load_postfit_histograms()`, `draw_postfit_canvas()`, `main()` - matching
`doc/TIER3_COMPLETION_PLAN.md` Section 4.2's deferred-import rule already
applied to every other ROOT-touching function across this whole Tier 3
plan (this file was simply not brought fully into line with it in Chunk
10.B). `build_ratio_histogram()` needed no `ROOT` import at all, even
before this fix - it only calls methods on the histogram objects passed
to it. `PostfitHistograms`'s field type hints (`"ROOT.TH1"`) are string
literals, never evaluated at runtime, so they impose no import
requirement; a `if TYPE_CHECKING: import ROOT` guard was added so
`ruff`'s `F821` (undefined name in a string annotation) stays satisfied
without a real runtime import.

`tests/test_plot_post_fit.py` updated to match: the
`_import_plot_post_fit_with_stubbed_root()` helper is gone; the module is
now imported once, plainly, at the top of the test file
(`from python import plotPostFit as plot_post_fit`), exactly like
`test_run_manifest.py`/`test_run_execution.py` already do for their own
ROOT-free modules. The three `parse_args()` tests no longer take a
`monkeypatch` fixture at all.

Verified directly, twice: (1) `python -c "import sys;
sys.path.insert(0, 'python'); import plotPostFit as ppf;
ppf.parse_args(['-i','a','-o','b']); print('ROOT' in sys.modules)"` →
prints `False` - the module imports and `parse_args()` runs with zero
ROOT presence in `sys.modules`, real or fake. (2) the full test file
still passes for real against this host's actual ROOT runtime for the
other four tests, which still need it.

### Finding 2: the canvas-content test was too weak - and while fixing it, a real bug was found

Copilot: "This test only verifies that two named pads exist, so it still
passes if the refactor drops the data/postfit plots, ratio, legend, or
chi2 annotation - the actual behavior of `draw_postfit_canvas()`. The
end-to-end test's non-empty-PDF check would also pass for an effectively
empty canvas. Please assert the expected primitives/content in each pad."

Verified, and this surfaced something worse than a coverage gap: while
building a stronger test, `draw_postfit_canvas()`'s legend was found to
be **actually missing** from its own output, right now, in the code
already committed for Chunk 10.B - a real regression Copilot's coverage
concern would have caught, had the stronger test existed from the start.

Reproduced directly, isolated from the rest of the function: `legend =
ROOT.TLegend(...); legend.AddEntry(...); legend.Draw()` inside a
function, with `legend` never referenced again after that function
returns, produces a `TCanvas` whose pad contains **no `TLegend` at all**
- `[p.ClassName() for p in pad1.GetListOfPrimitives()]` came back
`['TH1D', 'TH1D']` with no `TLegend` present. Cause: cppyy (PyROOT) owns,
and therefore deletes, the underlying C++ object of any `TObject` it
constructed once the Python wrapper's reference count reaches zero -
`legend` was a purely local variable inside `draw_postfit_canvas()` with
no reference surviving the function's return, so it was garbage-collected
before the caller ever saw the canvas. This is the exact same class of
hazard already found and fixed for `load_postfit_histograms()`'s `TFile`
in Chunk 10.B (see that entry above), now found a second time for a
different object - both hazards exist only because the original,
single-scope script kept every such object alive as a script-level name
for its entire run, a guarantee that silently broke the moment the code
was split into functions with their own local scopes.

Fix: `ROOT.SetOwnership(legend, False)` immediately after constructing
the legend, telling cppyy the C++ side now owns it, so it survives after
the Python reference is gone. Verified directly: with the fix reverted
locally, `[p.ClassName() for p in pad1.GetListOfPrimitives()]` came back
without `TLegend`; with it restored, `['TH1D', 'TH1D', 'TLegend', ...]`.
The end-to-end script's output PDF also grew from 170489 to 170679 bytes
once the legend was actually being drawn again - independent, physical
corroboration.

`draw_postfit_canvas()`'s test
(`test_draw_postfit_canvas_returns_two_pad_canvas`, renamed
`test_draw_postfit_canvas_draws_expected_content_in_each_pad`) rewritten
to assert real content per pad, not just pad names: pad1's two `TH1D`
histograms by name (`data`/`postfit`), exactly one `TLegend` with exactly
the two expected `(label, option)` entries (`("Data", "lep")`,
`("Postfit", "l")`), a `TLatex` whose exact title is the rendered
`#chi^{2}/ndof = ...` string; pad2's single `TH1D` by name (the ratio
histogram's own name). This test was confirmed to **fail** with
`AssertionError: legend missing or duplicated in pad1` against the
`ROOT.SetOwnership(...)`-reverted code, and to pass against the fix -
the direct regression test for this bug, exactly the protection Copilot
asked for.

### Verification performed

- `python -m pytest tests/test_plot_post_fit.py -v` → 9 passed (~50-67s
  across repeated runs), run for real against this host's actual
  CVMFS/LCG scientific runtime.
- `python scripts/quality_check.py --mode full` → 172 passed, 6
  deselected; ruff clean; black clean (27 files unchanged).
- `python "$repo_dir/python/plotPostFit.py" -i
  run/fits/J100/run_481_3000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root -o
  <tmp>` (direct end-to-end invocation, matching the launchers exactly) →
  exit 0, `<tmp>` created, 170679 bytes.
- `python -m pytest tests/test_analysis_workflows_integration.py -m
  "integration and requires_root" -v` → 1 passed, 2 deselected, in
  165.61s (run in the background per this session's established
  practice) - confirms the J100/J50 authoritative workflows, which both
  invoke `plotPostFit.py`, still match the frozen scientific reference
  after both fixes.
- `git diff --check` → passed.
- `grep -nE '[[:blank:]]+$' python/plotPostFit.py tests/test_plot_post_fit.py` →
  no output.

### What this commit does NOT do

Both fixes are confined to `python/plotPostFit.py` and
`tests/test_plot_post_fit.py`. No other file changed. Per the append-only
guardrail, Chunk 10.A's and 10.B's entries above are left exactly as
written - this section is the correction of record for both Copilot
findings.

## 2026-09-03: Tier-3 refactoring — Chunk 11.A: characterization test for `plot_postfit.cpp`

### Objective

Pin down the current, unmodified behavior of `plot_postfit.cpp`
(repository root) before splitting it into `read_bumphunter_results()`,
`load_postfit_histograms()`, `draw_residual_panel()`, and a slimmed
`plot_postfit()` orchestrator, per `doc/TIER3_COMPLETION_PLAN.md` Chunk
11. The file has one function today, `plot_postfit(char const * in_dir,
char const * pars_str)` - no existing function boundary to characterize
more precisely yet, and no test harness of any kind exists for ROOT
macros anywhere in this repository, so, per Chunk 11's own instruction,
Step A characterizes the **whole macro's current output**, run for real
as a subprocess.

### Target function (as it exists today)

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `void plot_postfit(char const * in_dir, char const * pars_str)` | `in_dir: char const *` (a fit output directory), `pars_str: char const *` (e.g. `"six"`) | `void` | opens up to four `TFile`s under `in_dir` (native/masked PostFit + FitParameters); `exit(1)` if the native residual/chi2 histograms are missing; optionally parses `<in_dir>/BHresults.json` via regex for BumpHunter results, falling back to `bump_hunter = false` when the file is absent; draws three residual panels (params, native, native-rebinned) to a canvas; writes `<in_dir>/post_fit.pdf` via `TCanvas::Print` |

### Test infrastructure decision

Per Chunk 11's own instruction: a small ROOT test macro invoked via
`root -l -b -q` from a `pytest` wrapper (`subprocess.run`), so it reports
through the same `pytest`-based gates as everything else rather than
inventing a second CI mechanism. `plot_postfit.cpp` needs a real ROOT
runtime this repository's own pytest dev venv does not have (confirmed
directly, same situation already documented for
`python/plotPostFit.py`'s ROOT dependency and
`tests/test_analysis_workflows_integration.py`'s scientific-runtime
tests) - it is only ever invoked in production after
`scripts/setup_buildAndFit.sh` has been sourced (see
`scripts/run_anaFit_J100.sh`/`run_anaFit_J50.sh`, both of which run
`root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\")"` after sourcing
that script). The new test sources that same setup script itself inside
a `subprocess.run(["bash", "-lc", ...])` call before invoking the macro,
mirroring the exact probe pattern already established by
`tests/test_plot_post_fit.py`'s own end-to-end test and
`test_authoritative_setup_provides_scientific_runtime`.

Marked both `@pytest.mark.requires_root` and
`@pytest.mark.requires_analysis_dependencies` from the start this time -
applying the lesson from the CI-failure fix earlier today (see that
entry above): any test that actually sources
`scripts/setup_buildAndFit.sh` needs CVMFS mounted, so it must carry both
markers to stay out of the CVMFS-less ordinary CI gate, regardless of
whether it also needs built `XMLReader`/`quickFit`/`pyBumpHunter`
binaries specifically.

### Test added (`tests/test_plot_postfit_macro.py`, new file)

- `test_plot_postfit_macro_produces_nonempty_pdf_for_real_fixture` - runs
  the real, unmodified macro as a subprocess (via the
  `setup_buildAndFit.sh`-sourcing probe described above) against a
  `tmp_path` **copy** of the already-committed
  `run/fits/J100/run_481_3000_sixPar/` fixture directory (never written
  into the tracked fixture itself - the macro writes `post_fit.pdf` into
  `in_dir`), with `pars_str = "six"`. This fixture directory has no
  `BHresults.json` and no `*_masked.root` files, confirmed by direct
  listing - exercising the current no-BumpHunter fallback path
  (`bump_hunter = false`) exactly as Chunk 11 specifies. Asserts the
  process exits `0` and `post_fit.pdf` exists and is non-empty in the
  copied directory.

Per the plan's own instruction (and Tier 1's existing "Plotting separated
from scientific acceptance" policy, already cited for
`tests/test_plot_post_fit.py`), **byte-identical PDF comparison is
deliberately not attempted** - "runs successfully against a real fixture
and produces a real, non-empty plot" is the chosen, and only,
characterized invariant. As independent, incidental corroboration (not a
relied-upon assertion): the macro's real output PDF came back exactly
41589 bytes in this session, byte-for-byte identical to the already-
committed `post_fit.pdf` sitting in the tracked fixture directory from an
earlier real production run of this exact, unmodified macro against this
exact fixture - consistent with, though not proof of, a fully
deterministic PDF for this specific ROOT/font/data combination.

### What this commit does NOT do

No production file was modified. `git status --short` shows only
`tests/test_plot_postfit_macro.py` as untracked (new); `git diff --stat`
is empty - `plot_postfit.cpp` itself was never touched. Per Chunk 11's
own text, no `scripts/quality_check.py` registration applies to this
file (it only covers Python files) - `tests/test_plot_postfit_macro.py`
is a Python test file and could in principle be registered, but Chunk 11
explicitly does not require it (unlike Chunks 9/10's Python production
targets), so registration is deferred to a decision recorded in Step B
below rather than assumed here.

### Verification performed

- `python -m pytest tests/test_plot_postfit_macro.py -v` → 1 passed
  (19.83s), run for real against this host's actual CVMFS/LCG scientific
  runtime.
- `python scripts/quality_check.py --mode full` → 172 passed, 6
  deselected; ruff clean; black clean (27 files unchanged) - unaffected,
  confirming the new file doesn't touch anything already gated.
- `python -m ruff check tests/test_plot_postfit_macro.py` /
  `python -m black --check tests/test_plot_postfit_macro.py` → both
  clean already.
- `git diff --check` → passed.
- `grep -nE '[[:blank:]]+$' tests/test_plot_postfit_macro.py` → no
  output.

### Compliance review (Section 8, Characterization variant)

1. Chunk 11, Step A.
2. `plot_postfit.cpp` untouched; only
   `tests/test_plot_postfit_macro.py` (new, untracked) added.
3. The new test asserts real, specific behavior (real process exit code,
   real non-empty PDF file on disk from a real ROOT fixture) - not merely
   "does not raise."
4. The test was run against the unmodified target file, for real, against
   this host's actual scientific runtime, before any production change;
   the exact result (1 passed, 19.83s) is reported above for review.
5. Human-verification checkpoint: presented to the user in session for
   confirmation before Step B's commit is made (recorded per Step B's own
   activity-log entry once given).

### Remaining open chunks

Chunk 11.B (extraction of `read_bumphunter_results`/
`load_postfit_histograms`/`draw_residual_panel`) and Chunk 12 are open.

## 2026-09-03: Tier-3 refactoring — Chunk 11.B: extract functions from `plot_postfit.cpp`

### Objective

Move `plot_postfit.cpp`'s single 257-line function, characterized and
human-verified in Step A (commit `2b7d168`), into `read_bumphunter_results()`,
`load_postfit_histograms()`, `draw_residual_panel()`, plus a slimmed
`plot_postfit()` orchestrator with its public entry point's exact name and
parameter order unchanged, per `doc/TIER3_COMPLETION_PLAN.md` Chunk 11.

### What changed

- `plot_postfit.cpp` restructured in place into:
  - `struct BumpHunterInfo { float global_pval, significance, mask_min,
    mask_max; bool available; }` and `BumpHunterInfo
    read_bumphunter_results(string const & bh_log_name)` - the log-reading/
    regex-parsing block moved verbatim, including its diagnostic prints
    (`cout << bh_log_name << endl;` and the "WARNING: Could not parse
    values..." message). `available` matches the original's
    `bump_hunter = false` fallback exactly: `false` only when the log file
    could not be opened, `true` otherwise - not an exception.
  - `struct PostfitHistograms` (the ten `TH1D*` fields, renamed without
    their `h_`/`_native`/`_masked` prefixes since they're now struct
    members: `native`, `native_rebinned`, `native_chi2`,
    `native_chi2_rebinned`, `masked`, `masked_rebinned`, `masked_chi2`,
    `masked_chi2_rebinned`, `native_params`, `masked_params`) and
    `PostfitHistograms load_postfit_histograms(TFile * native, TFile *
    masked, TFile * native_params, TFile * masked_params)` - the
    `Get<TH1D>` block moved verbatim, including the pre-existing
    behavior that `native_params`/`masked_params` are dereferenced
    unconditionally inside the `if (native)`/`if (masked)` guards, with
    no null check of their own (see "Preserved pre-existing landmine"
    below).
  - `enum class ResidualPanelKind { kParams, kNative, kNativeRebinned }`
    and `struct ResidualPanelInfo { ResidualPanelKind kind; float
    native_chi2_ndof, native_pval, masked_chi2_ndof, masked_pval; }` -
    **new**, not in the plan's literal table (see "A real gap in the
    plan's stated signature" below).
  - `void draw_residual_panel(TCanvas * can, TH1D * first, TH1D * second,
    bool bump_hunter, BumpHunterInfo const & bh, char const * pars_str,
    char const * out_file_name, ResidualPanelInfo const & info)` - the
    body of the original for-loop, moved verbatim, with every `h.first ==
    h_native_params`/`h.first == h_native`/`h.first == h_native_rebinned`
    pointer-identity check replaced by `info.kind ==
    ResidualPanelKind::k...`, and the scalar chi2/pval `Form(...)` calls
    reading from `info.native_chi2_ndof`/etc. instead of outer-scope
    variables.
  - `void plot_postfit(char const * in_dir, char const * pars_str)`
    (unchanged signature) - becomes the orchestrator: builds the six
    input/output paths (unchanged), opens the four `TFile`s (unchanged),
    calls `load_postfit_histograms()`, `read_bumphunter_results()`,
    computes `bump_hunter = plot_masked && bh_info.available` (see
    "Preserving `plot_masked`'s exact role" below), computes the ten
    chi2/pval/nbkg scalars (moved verbatim, now reading from the
    `PostfitHistograms` struct's fields instead of individually-named
    pointers), opens the canvas/PDF, then loops over the three panels
    (`{h.native_params, h.masked_params, kParams}`,
    `{h.native, h.masked, kNative}`, `{h.native_rebinned,
    h.masked_rebinned, kNativeRebinned}`) calling `draw_residual_panel()`
    once per pair, per the plan's own "the existing loop... calls this
    once per pair instead of repeating the body inline" instruction.
- `tests/root_macros/BHresults_sample.json` (**new, tracked fixture**) -
  a small, hand-written JSON with known values
  (`global_Pval: 0.1234, significance: 2.5, MaskMin: 500.0, MaskMax: 700.0`),
  since this repository's existing J100 canonical run has no
  `BHresults.json` (it is unmasked). The regex `read_bumphunter_results()`
  uses does a flat text scan, not real JSON-schema-aware parsing (verified
  directly against `python/FindBHWindow.py`, the actual producer of real
  `BHresults.json` files - its `global_Pval`/`significance` keys live
  nested inside a `pyBHresult` sub-object, not top-level; the regex finds
  them regardless of nesting depth), so a flat fixture exercises the exact
  same code path as a real, nested production file.
- `tests/root_macros/test_read_bumphunter_results.cpp` (**new**) - the
  first-ever ROOT-macro unit test in this repository, per Chunk 11's own
  instruction. `#include "../../plot_postfit.cpp"` to reach
  `BumpHunterInfo`/`read_bumphunter_results()` directly (a fresh `root -l
  -b -q` process per invocation, so no redefinition risk from including a
  `.cpp` without an include guard). Calls `read_bumphunter_results()`
  against the fixture above and asserts each `BumpHunterInfo` field
  against the fixture's known values (tolerance `1e-4f`, matching
  `stof`'s own float precision), then against `<fixture>.does_not_exist`
  and asserts `available == false` and all four scalar fields stay at
  their zero-initialized defaults. Prints `TEST_READ_BUMPHUNTER_RESULTS_OK`/
  `_FAILED` and exits `0`/`1` accordingly - explicit `if (!...) { cout <<
  "FAIL: ..."; ok = false; }` checks were used instead of `assert()`, to
  avoid depending on whether this ROOT build's Cling compiles with
  `NDEBUG` defined.
- `tests/test_read_bumphunter_results.py` (**new**) - the thin
  Python/pytest wrapper invoking the macro above via `subprocess.run`,
  matching `tests/test_plot_postfit_macro.py`'s own wrapper pattern
  exactly (same `setup_buildAndFit.sh`-sourcing probe, same two markers).
- `tests/test_plot_postfit_macro.py`'s existing test kept unchanged - it
  is now an end-to-end regression test of the rewritten `plot_postfit()`,
  still valuable (per Chunk 11's own instruction to keep it, not delete
  it).
- No `scripts/quality_check.py` registration - it only covers Python
  files, and Chunk 11 doesn't require registering the two new Python test
  files either (unlike Chunks 9/10's Python production targets).

### A real gap in the plan's stated `draw_residual_panel()` signature

`doc/TIER3_COMPLETION_PLAN.md`'s Chunk 11 table gives
`draw_residual_panel()` exactly seven parameters: `(TCanvas* can, TH1D*
first, TH1D* second, bool bump_hunter, BumpHunterInfo const& bh, char
const* pars_str, char const* out_file_name)`. Implementing this literally
is impossible without losing real, observable behavior: the original
loop's panel-specific content - Y-axis range, draw option ("HIST" vs
plain), whether the zero-line and per-panel "range: ... GeV" text are
drawn, whether the "Bump Hunter" header and global p-val/significance/
mask-range text appear, and which of the four chi2/ndof-and-p-val text
boxes are shown - is driven by two things neither struct nor scalar
parameter in that seven-parameter list can express: (1) **which** of the
three panels this call is drawing (originally `h.first ==
h_native_params`/`h_native`/`h_native_rebinned` pointer-identity checks
against outer-scope variables `draw_residual_panel()` no longer has
access to), and (2) the four scalar chi2/ndof and p-value numbers each
panel displays (`native_chi2_ndof`, `native_pval`, `masked_chi2_ndof`,
`masked_pval`, each with a separately-computed "rebinned" variant used
only by the rebinned panel) - values the plan's own `PostfitHistograms`
struct doesn't carry either (they are computed in `plot_postfit()`
*after* `load_postfit_histograms()` returns, straight from
`GetBinContent()` calls).

Corrected: added `ResidualPanelKind` (an explicit tag replacing the
pointer-identity checks) and `ResidualPanelInfo` (bundling the tag with
the four scalar values relevant to whichever panel is being drawn) as an
eighth parameter. This is the smallest addition that preserves every
originally-observable difference between the three panels; verified
directly (see "Verification performed" below) that the rewritten macro,
run against the same fixture Step A characterized, produces a PDF
byte-identical to both Step A's own captured output and the already-
committed reference `post_fit.pdf` in the tracked fixture directory - not
just "runs and produces a plot", but the exact same plot.

### Preserving `plot_masked`'s exact role

The original set `bool bump_hunter{plot_masked};` (a file-scope `bool
const plot_masked{true}`), then only ever set it to `false` in the `else`
branch when the BumpHunter log could not be opened - meaning `bump_hunter`
equals `plot_masked` whenever the log **can** be opened, and `false`
otherwise. Since `read_bumphunter_results()`'s new signature takes only
`bh_log_name` (per the plan), it cannot see `plot_masked` itself.
`plot_postfit()` now computes `bump_hunter = plot_masked &&
bh_info.available;` - the exact logical equivalent (`available` is
`false` only when the file could not be opened, matching the original
`else` branch precisely; `plot_masked && true == plot_masked`, matching
the original `if` branch precisely), keeping `plot_masked` as a real,
still-honored toggle rather than silently dropping its effect.

### Preserved pre-existing landmine (guardrail 1: no fix, just documented)

`load_postfit_histograms()` dereferences `native_params->Get<TH1D>(...)`
unconditionally inside the `if (native)` block (and
`masked_params->Get<TH1D>(...)` inside `if (masked)`), with no null check
of `native_params`/`masked_params` themselves - if the native `PostFit_*`
file opens successfully but the corresponding `FitParameters_*` file does
not, this crashes on a null-pointer dereference. This is pre-existing
behavior in the original, unmodified `plot_postfit()` (confirmed by
re-reading the source before moving anything), not something this
refactor introduced or is asked to fix (guardrail: "no scope for fixing
pre-existing, unrelated issues noticed along the way") - moved verbatim,
landmine included, exactly as guardrail 6 requires for the `nPars`
double-match quirk found in Chunk 5.

### Dead-code cleanup

`bool is_rebinned{false};` (declared in the original loop, immediately
before the `for` loop it was presumably meant to help control) is never
read anywhere in the function - confirmed by `grep -n "is_rebinned"
plot_postfit.cpp` returning only its own declaration line. Dropped as
mechanical, zero-behavior-change cleanup, matching this project's
established practice (e.g. Chunk 8/9's dead-import removals) for a file
newly being reorganized.

### Confirm: no scientific behavior changed

`plot_postfit.cpp` produces plots, not scientific acceptance results - it
is excluded from the frozen `analysis_reference.json` contract (Tier 1,
"Plotting separated from scientific acceptance"), same as
`python/plotPostFit.py`. Every ROOT call, in the same order, with the
same arguments, was moved verbatim into its new function; the two
additions above (`ResidualPanelKind`/`ResidualPanelInfo`, and the
`plot_masked && bh_info.available` equivalence) are both non-scientific,
plot-only/control-flow concerns, verified empirically, not just argued:
run directly against a `tmp_path` copy of the real J100 fixture
(no `BHresults.json`, exercising the no-BumpHunter fallback path), the
rewritten macro exits `0` and produces `post_fit.pdf` at **exactly
41589 bytes** - byte-for-byte identical to both Step A's own captured
output and the already-committed `post_fit.pdf` sitting in the tracked
fixture directory from an earlier real production run of the original,
unmodified macro against this exact fixture. `guardrail 11` (no new
external library linked) confirmed by diffing the file's `#include` list
before and after: unchanged.

The `bump_hunter == true` (masked-fit) branch inside `draw_residual_panel()`
is **not** exercised by any automated test at this repository state - it
was not exercised by any automated test before this refactor either (no
masked fixture exists; the plan explicitly scopes synthetic ROOT-file-
construction fixtures for the masked path out of this chunk, see below),
so this refactor introduces no new risk there relative to what already
existed. As independent evidence that this branch is at least still
syntactically/type-correct: C++ does not skip compiling an `if` branch
that happens not to execute at runtime, so Cling's successful compilation
and 0-exit run of the whole macro (with `bump_hunter == false` this run)
already exercised compiling the `if (bump_hunter) { ... }` branch's code,
even though it did not execute it.

### Deliberate scope boundary (to be restated in `doc/TIER3_SYSTEM.md`, Chunk 12)

Per the plan's own instruction, `load_postfit_histograms()` is not given
its own dedicated unit test - it is "harder to test in isolation without
a real `TFile`", and inventing a synthetic ROOT-file-construction fixture
for it is explicitly out of this chunk's scope. It remains covered only by
`tests/test_plot_postfit_macro.py`'s existing end-to-end test. Likewise,
`draw_residual_panel()`'s `bump_hunter == true` path (see above) has no
dedicated test either - this is a slightly broader boundary than the plan
states explicitly for `load_postfit_histograms()` alone, but follows the
same underlying constraint (no masked/BumpHunter fixture exists in this
repository to exercise it against). Both are deliberate, explained scope
boundaries, not silent gaps - flagged here for Chunk 12 to restate in
`doc/TIER3_SYSTEM.md`'s "Known Limitations" section.

### Verification performed

- `python -m pytest tests/test_plot_postfit_macro.py
  tests/test_read_bumphunter_results.py -v` → 2 passed (36.62s), run for
  real against this host's actual CVMFS/LCG scientific runtime - the
  exact acceptance-check command Chunk 11 specifies.
- Direct macro invocation (`root -l -b -q "plot_postfit.cpp(\"<tmp copy
  of the J100 fixture>\", \"six\")"`, matching the launchers exactly) →
  exit `0`, `post_fit.pdf` created at exactly 41589 bytes - byte-
  identical to Step A's own characterization run and to the already-
  committed reference PDF.
- Negative control for the new ROOT-macro unit test: re-ran
  `test_read_bumphunter_results.cpp` against a deliberately corrupted
  fixture copy (`global_Pval` changed from `0.1234` to `0.9999`) →
  `FAIL: global_pval = 0.9999, expected 0.1234`,
  `TEST_READ_BUMPHUNTER_RESULTS_FAILED`, exit `1` - confirms the test
  actually catches a wrong value, not just "does not crash."
- `python scripts/quality_check.py --mode full` → 172 passed, 6
  deselected; ruff clean; black clean (27 files unchanged) - unaffected,
  confirming the two new Python files don't touch anything already
  gated (no registration applies to this chunk).
- `python -m ruff check tests/test_read_bumphunter_results.py` /
  `python -m black --check tests/test_read_bumphunter_results.py` → both
  clean already.
- `python -m pytest tests/test_analysis_workflows_integration.py -m
  "integration and requires_root" -v` → 1 passed, 2 deselected, in
  153.99s (run in the background per this session's established
  practice, as an extra safety net - not one of Section 7's strictly-
  mandatory chunks, but this chunk rewrote production code the real
  launchers invoke) - confirms the J100/J50 authoritative workflows,
  which both invoke `plot_postfit.cpp`, still match the frozen
  scientific reference.
- `git diff --check` → passed.
- `grep -nE '[[:blank:]]+$' plot_postfit.cpp
  tests/root_macros/test_read_bumphunter_results.cpp
  tests/root_macros/BHresults_sample.json
  tests/test_read_bumphunter_results.py` → no output.
- `grep -n "#include\|#pragma" plot_postfit.cpp` (before vs. after) →
  identical include list, confirming guardrail 11.

### Compliance review (Section 8, Extraction variant)

1. Step A's commit (`2b7d168`) is named above; this commit's Step A test
   is kept unchanged as an end-to-end regression test; the new
   `read_bumphunter_results()` unit test is new, not relocated (no prior
   test existed to relocate).
2. Not applicable in the usual sense: `tests/test_plot_postfit_macro.py`
   never imported `plot_postfit.cpp` (it always ran it as a subprocess),
   so there is no import line to diff.
3. Production code (the three shell launchers using `plot_postfit.cpp`)
   is unchanged, and `plot_postfit()`'s public entry point retains its
   exact original name and parameter order - confirmed by grep, not
   assumed.
4. No extracted function imports from `run_anaFit.py` or any Python
   module - this chunk is pure C++, unrelated to that module system.
5. Required Section 7 gates ran; output captured above, including the
   extra, non-mandatory integration-gate rerun.
6. Activity-log entry appended (this content), not a rewrite of any
   existing section.

### Remaining open chunks

Chunk 12 (`doc/TIER3_SYSTEM.md`) is the only chunk left.

## 2026-09-03: Tier-3 refactoring — Chunk 12: `doc/TIER3_SYSTEM.md` and final documentation

### Objective

Write `doc/TIER3_SYSTEM.md`, modeled on `doc/TIER1_SYSTEM.md`/
`doc/TIER2_SYSTEM.md`'s structure, per `doc/TIER3_COMPLETION_PLAN.md`
Chunk 12 - the final chunk, completing the plan. Single commit, no
production code change: like Chunk 8, guardrail 3's Step A/Step B
two-step pattern does not apply here, since there is no new target
function to characterize first.

### What changed

`doc/TIER3_SYSTEM.md` created (new file), containing, at minimum, per
Chunk 12's own required-contents list:

- the module tables from the plan's Sections 4.1 and 4.3, updated with
  actual final function signatures - read directly from the finished
  source files (`grep -nE '^(def |class )'` against each of the seven
  `run_anaFit.py` modules, `plot_edm.py`, `python/plotPostFit.py`, and
  `plot_postfit.cpp`), not re-derived from memory or from earlier,
  possibly-superseded plan text;
- every "record the decision" point flagged in Chunks 5, 9, 10, and 11
  resolved and documented in a dedicated "Decisions recorded during
  extraction" section: `run_templates.py`'s internal decomposition and
  the preserved `nPars` quirk (Chunk 5); `parse_minuit_edm_log()`'s
  `FileNotFoundError`-propagation choice (Chunk 9); `python/plotPostFit.py`'s
  styling placement, `gStyle`/`gROOT.SetBatch()` relocation, and the
  `TFile`/`TLegend` lifetime fixes (Chunk 10); `plot_postfit.cpp`'s
  `exit(1)` placement and the `ResidualPanelKind`/`ResidualPanelInfo`
  addition beyond the plan's literal signature (Chunk 11);
- a test-file map from each module/file to its test file(s), including
  the two new ROOT-macro test files from Chunk 11
  (`tests/test_read_bumphunter_results.py`,
  `tests/root_macros/test_read_bumphunter_results.cpp`), each row noting
  whether real ROOT/CVMFS is needed and, if so, for which specific
  tests;
- the unchanged Tier 1/2 gate commands (lightweight full gate, scientific
  gate), plus the plotting-layer real-ROOT commands this plan introduced,
  with a paragraph confirming they still cover every extracted module -
  the scientific gate specifically, since it reruns the real J100/J50
  launchers, which transitively invoke every one of the four Tier-3
  refactor targets for real;
- a "Known limitations" section naming: the two explicit, deliberate
  scope boundaries Chunk 11 already flagged (`load_postfit_histograms()`
  (C++) has no dedicated unit test; the `bump_hunter == true` masked
  path has no automated test at all); the `sys.modules`-stubbing-only
  testing of `collect_scientific_runtime()`/the `doprefit` branch (never
  against real ROOT/`PreFit` in a unit test, only end-to-end via the
  scientific gate); the two preserved pre-existing landmines (the
  `native_params`/`masked_params` null-pointer risk in
  `plot_postfit.cpp`, and the `nPars` double-match quirk in
  `run_templates.py`); and the plan's own out-of-scope boundary (only
  the four named files were touched).

### Every claim was verified before being written, not just asserted

- The "`run_anaFit.py` imports only from the seven modules, never the
  reverse" claim: verified via `grep -rn "run_anaFit"
  python/run_execution.py python/run_manifest.py python/run_provenance.py
  python/run_masking.py python/run_templates.py python/run_fit.py
  python/run_cli.py` returning nothing (exit code 1) before writing the
  claim.
- The `should_mask()` NaN-handling description: read directly from
  `python/run_masking.py`'s own source and its inline comment, not
  reconstructed from memory.
- The "every real-ROOT/CVMFS test is marked both `requires_root` and
  `requires_analysis_dependencies`" claim: verified by grepping the
  decorators immediately preceding every `def test_` in
  `tests/test_plot_post_fit.py`, `tests/test_plot_postfit_macro.py`, and
  `tests/test_read_bumphunter_results.py` directly, confirming the three
  `parse_args()`-only tests correctly have neither marker and all seven
  real-ROOT tests correctly have both.
- The "172 passed, 6 deselected" and "27 files unchanged" lightweight-gate
  numbers, and the "11 passed... 87.29 seconds" plotting-layer-gate
  number, were both obtained by actually rerunning the gates fresh in
  this session, immediately before writing them into the document - not
  copied from an earlier, possibly-stale chunk entry. The scientific-gate
  number (1 passed, 153.99s) is cited from Chunk 11.B (commit `b026efd`,
  the most recent commit that could have changed scientific behavior);
  this chunk makes no production change, so re-running the ~3-minute
  scientific gate again was judged unnecessary and is not claimed as
  freshly re-verified in this commit.

### Verification performed

- Manual review: re-read the finished document top to bottom against the
  actual module and test files it describes (see the spot-checks above),
  confirming every claim has a citation, per the plan's own acceptance
  check.
- `grep -nE '[[:blank:]]+$' doc/TIER3_SYSTEM.md` → no output.
- `git diff --check` → passed.
- `python scripts/quality_check.py --mode full` (rerun fresh for this
  entry's own citations) → 172 passed, 6 deselected; ruff clean; black
  clean (27 files unchanged); exit code 0.
- `python -m pytest tests/test_plot_post_fit.py -v
  tests/test_plot_postfit_macro.py tests/test_read_bumphunter_results.py -v`
  → 11 passed (9 + 2), 87.29 seconds, exit code 0, run for real against
  this host's actual CVMFS/LCG scientific runtime.
- No integration-gate rerun in this commit: no production file changed,
  so the Chunk 11.B result (`b026efd`, 1 passed, 153.99s) remains the
  current, accurate citation.

### Compliance review

1. Chunk 12, single commit (no Step A/Step B split applies - no target
   function exists to characterize, matching Chunk 8's precedent).
2. Every required-contents item from Chunk 12's own list is present:
   updated module tables, resolved decision points, test-file map, gate
   commands with confirmation of continued coverage, and a Known
   Limitations section.
3. No production code touched - `git status --short` shows only
   `doc/TIER3_SYSTEM.md` as new/untracked before this commit.
4. Every factual claim was checked against the actual repository state
   in this session before being written, not carried forward from
   possibly-stale earlier chunk text.
5. Activity-log entry appended (this content), not a rewrite of any
   existing section.

### Remaining open chunks

None. All twelve chunks of `doc/TIER3_COMPLETION_PLAN.md` are complete.

## 2026-09-04: Wire the ROOT regression tests into CI and correct the paired-pointer contract (GitHub Copilot review, PR #6)

### Objective

Resolve the two findings from GitHub Copilot's review of PR #6, both
raised against the Chunk 11/Chunk 12 work:

1. (Medium) `tests/test_plot_postfit_macro.py` and
   `tests/test_read_bumphunter_results.py` are absent from
   `scripts/quality_check.py`'s `test_targets`, and the hosted scientific
   workflow only invokes `tests/test_analysis_workflows_integration.py`.
   Neither new ROOT regression test therefore ran in any CI job, and both
   Python wrappers also escaped Ruff/Black.
2. (Low) `plot_postfit.cpp`'s `load_postfit_histograms()` comment claims
   all four `TFile *` parameters "may be null", but `native_params`/
   `masked_params` are dereferenced unconditionally inside their
   partner's guard, so a caller following the stated contract crashes.

Both were verified against the repository before any change, not taken at
face value:

- `grep -n "pytest" .github/workflows/scientific-analysis.yml` shows the
  only three pytest invocations in the hosted job are
  `tests/test_repo_utils.py -m "requires_analysis_dependencies"`,
  `tests/test_analysis_workflows_integration.py -k
  authoritative_setup_provides_scientific_runtime`, and
  `tests/test_analysis_workflows_integration.py -m "integration and
  requires_root"`. `.github/workflows/tier1-root-comparison.yml` runs
  `scripts/quality_check.py`, whose `test_targets` did not list either
  file. Finding 1 confirmed: neither file ran anywhere in CI.
- Reading `load_postfit_histograms()` directly confirms
  `native_params->Get<TH1D>("postfit_params")` sits inside
  `if (native) { ... }` with no null check of `native_params` itself
  (same for the masked pair). Finding 2 confirmed as a documentation
  defect; the code behavior itself is the pre-existing landmine this plan
  deliberately preserved, and is not changed here.

### What changed

- `scripts/quality_check.py`: added `tests/test_plot_postfit_macro.py`
  and `tests/test_read_bumphunter_results.py` to `test_targets`, in
  alphabetical position. This buys Ruff/Black coverage only - every test
  in both files carries `requires_analysis_dependencies`, so the ordinary
  gate's pytest phase still deselects all of them, which is exactly the
  behavior Copilot's comment described as acceptable ("the existing
  marker can still keep them out of the lightweight pytest phase").
- `.github/workflows/scientific-analysis.yml`: added a final step, "Run
  plotting-layer real-ROOT regression gates", which sources
  `scripts/setup_buildAndFit.sh` (same preamble and same failure
  annotation as every other scientific step in that job) and then runs
  `python -m pytest tests/test_plot_post_fit.py
  tests/test_plot_postfit_macro.py tests/test_read_bumphunter_results.py
  -m "requires_analysis_dependencies" -v`. The step is placed in this job
  specifically because it is the only one with CVMFS: it mounts
  `atlas.cern.ch`/`sft.cern.ch` via the `cvmfs-contrib/github-action-cvmfs`
  step and verifies the mounts before use.
  Scope note: Copilot named only the two new wrapper files, but
  `tests/test_plot_post_fit.py`'s four real-ROOT tests were in exactly
  the same position - registered for linting, but marker-deselected
  everywhere and run by no CI job. Fixing only the two named files would
  have left two thirds of the plotting layer's real-ROOT coverage still
  unreachable in CI, so all three files are included.
- `plot_postfit.cpp`: rewrote `load_postfit_histograms()`'s leading
  comment to state the paired-pointer requirement explicitly
  (`native_params` must be non-null whenever `native` is; likewise for
  the masked pair; passing a null params pointer alongside a non-null
  partner crashes), replacing the previous "any of which may be null"
  wording. Comment-only: no statement, signature, or behavior changed.
- `doc/TIER3_SYSTEM.md`: brought in line with the above, and corrected
  three claims found to be wrong when this branch was reviewed end to
  end:
  - the `run_masking.py` row said `should_mask()` was "fixed post-hoc to
    treat `NaN` as 'not maskable' rather than raising". Both halves are
    backwards: verified directly that `should_mask(float("nan"), 0.01)`
    returns `True` (NaN *does* require masking, matching the original
    coordinator's `if p_value > threshold:` gating), and the pre-fix
    version returned `False` rather than raising. Rewritten to state the
    `not (p_value > threshold)` vs `p_value <= threshold` distinction and
    cite the proving test.
  - the "Gate commands" closing paragraph claimed the scientific gate
    exercises all four Tier-3 refactor targets "for real". Verified
    false: `tests/test_analysis_workflows_integration.py` sets
    `ANAFIT_SKIP_PLOTS=1`, and `scripts/run_anaFit_J100.sh`/
    `run_anaFit_J50.sh` gate both plotting invocations on that variable,
    so the gate covers `run_anaFit.py` and `plot_edm.py` (invoked
    unconditionally from `build_fit_extract()`) but not
    `python/plotPostFit.py` or `plot_postfit.cpp`. Rewritten as a
    three-bullet split stating which gate covers what, and why the
    plotting layer needed its own CI step.
  - the test-file map said `tests/test_plot_postfit_macro.py` runs "via
    `tests/root_macros/`"; it invokes `plot_postfit.cpp` directly.
  - the `quality_check.py` registration paragraph (which said the two
    wrapper files are deliberately unregistered) and the plotting-layer
    gate section were updated to match the new registration and CI step;
    lightweight-gate numbers refreshed from 172 passed / 6 deselected /
    27 files to 172 passed / 8 deselected / 29 files.

### Verification performed

- `python scripts/quality_check.py --mode full` → 172 passed, 8
  deselected, ruff clean, black clean (29 files unchanged), exit code 0.
  Both newly-registered files are visibly present in the echoed ruff and
  black command lines.
- `python -m pytest tests/test_plot_post_fit.py
  tests/test_plot_postfit_macro.py tests/test_read_bumphunter_results.py
  -m "requires_analysis_dependencies" --collect-only -q` → 6/11
  collected, 5 deselected, listing exactly the four `test_plot_post_fit`
  real-ROOT tests plus the two macro wrappers. This is the precise
  selection the new CI step will make.
- `python -m pytest <the same three files> -m
  "requires_analysis_dependencies"` run for real against this host's
  CVMFS/LCG runtime → 6 passed, confirming `plot_postfit.cpp` still
  compiles and behaves identically after the comment rewrite.
- The workflow file was parsed with `yaml.safe_load` to confirm it is
  still valid YAML and that the new step is the 15th and last step of
  `complete-analysis-test-suite`, with its backslash continuations
  surviving the block scalar intact.
- `grep -nE '[[:blank:]]+$'` over every changed file and `git diff
  --check` → both clean.
- No integration-gate rerun in this commit: no analysis-affecting
  production code changed (the only `.cpp` change is a comment), so the
  scientific gate result recorded for Chunk 11.B (`b026efd`, 1 passed,
  153.99 s) remains the current citation. It was, however, independently
  re-run at this branch's HEAD during the review that preceded this
  commit (`pytest -m "not requires_analysis_dependencies" tests/` → 174
  passed in 153.75 s, which selects it) and still matched the frozen
  reference.

### Compliance review

1. Only the two verified findings were acted on, plus the documentation
   claims that the CI change itself made stale and three factual errors
   found by direct verification against the repository. No unrelated
   cleanup.
2. No production behavior changed anywhere: the `.cpp` edit is a comment,
   `quality_check.py` gains two list entries, and the workflow gains a
   step. `run_anaFit.py` and the seven extracted modules are untouched.
3. No new dependency or tool was introduced; the new CI step reuses the
   existing setup preamble, the existing markers, and the existing
   pytest invocation style verbatim. The one marker change in this
   commit (see below) applies an existing, already-defined marker to one
   more test - it does not define a new one.
4. Activity-log entry appended (this content), not a rewrite of any
   existing section - except the "Known follow-up" subsection below,
   which was rewritten from "not done here" to "done here" before this
   entry was ever committed, per the append-only rule's own scope (it
   protects committed history, not a still-uncommitted draft of the
   entry describing the commit currently being prepared).

### Additional one-line fix folded into this commit

`tests/test_analysis_workflows_integration.py::test_authoritative_j100_j50_workflows_match_frozen_reference`
carried `integration` and `requires_root` but not
`requires_analysis_dependencies`, so it was the one real-ROOT test this
plan's own stated rule ("any test that sources
`scripts/setup_buildAndFit.sh` carries both markers") did not cover.
Measured consequence before the fix: `pytest -m "not
requires_analysis_dependencies" tests/` selected it and ran a real
154-second fit, and would fail outright on a machine with no CVMFS - the
same failure mode fixed for the plotting tests in `6745188`. This was
raised during the same-branch review as a follow-up rather than acted on
immediately (it touches the scientific gate's own test file and is
outside both Copilot findings), and is now applied at the user's explicit
request alongside the two Copilot fixes above, in this same commit.

Added `@pytest.mark.requires_analysis_dependencies` to that one test.
Verified both CI selectors are unaffected: `pytest
tests/test_analysis_workflows_integration.py -m "not
requires_analysis_dependencies" --collect-only` now deselects it (1/3
collected, was 2/3); `pytest tests/test_analysis_workflows_integration.py
-m "integration and requires_root" --collect-only` still selects exactly
it (1/3 collected) - the hosted scientific job's own selector is
unchanged. `scripts/quality_check.py` never listed this file in
`test_targets` at all, so it was never affected either way. Reran
`python scripts/quality_check.py --mode full` after this addition - 172
passed, 8 deselected, ruff/black clean (29 files unchanged), exit code 0,
unchanged from the pre-marker run - confirming the fix is inert to every
existing selector except the one it was meant to change.

## 2026-09-04: Fail-fast validation ordering, a dead parameter, and two documentation-accuracy fixes (same-branch review follow-up)

### Objective

Continue resolving the remaining, non-Copilot items raised during the
same-branch review that preceded the previous commit (`6855d4a`), at the
user's explicit request to "fix the rest of the issues found":

1. `run_fit.py`'s `fitresultfile` basename validation ran after the
   XMLReader subprocess, so a bad `fitresultfile` still paid for a full
   (expensive) workspace build before failing.
2. `run_templates.py`'s `_seed_prefit_parameters()` took an `nbkg`
   parameter that is unconditionally overwritten before any use inside
   the function - dead parameter-passing, not a behavior difference.
3. `doc/TIER3_SYSTEM.md`'s Chunk 11 decision paragraph credited the
   Chunk 11.B byte-identical-PDF verification (41589 bytes) to
   `tests/test_plot_postfit_macro.py`'s automated test, which
   deliberately does not assert byte-identical output (its own comment
   says so, matching `tests/test_plot_post_fit.py`'s documented policy).

Two other items surfaced in the same review - `repository_dirty` added to
provenance without a `schema_version` bump, and the latent dual-module
hazard from `pyproject.toml`'s `pythonpath = [".", "python"]` - were
looked at again and deliberately left alone; see "Considered and not
changed" below.

### What changed

- `python/run_fit.py`: the `fitresultfile` basename check (added by an
  earlier Copilot-fix commit, `9f1956a`) moved from between the XMLReader
  and quickFit calls to the very top of `build_fit_extract()`, before
  `xmlreader_command` is even constructed. Comment updated from "before
  quickFit launches" to "before either XMLReader or quickFit launches",
  with the fail-fast rationale stated explicitly. Pure code motion of a
  stateless check that only reads `fitresultfile` - no other statement
  before it in the function depended on anything the check itself
  produces beyond `fitresult_dir`/`fitresult_name`, both of which move
  with it.
- `tests/test_run_fit.py`::`test_build_fit_extract_rejects_fitresultfile_without_fitresult_token`
  strengthened to match: the comment explaining the ordering change, and
  the trailing assertion tightened from "quickFit never reached" (`assert
  "quickFit background or signal fit" not in calls`) to "neither
  subprocess reached at all" (`assert calls == []`) - the test now
  actually proves the new fail-fast behavior, not just its weaker,
  pre-existing guarantee.
- `python/run_templates.py`: removed `_seed_prefit_parameters()`'s
  `nbkg` parameter and the corresponding `nbkg=nbkg` keyword argument at
  its one call site inside `_stage_xml_templates()`. Verified dead by
  direct reading: the parameter is declared, never read anywhere in the
  function body, then unconditionally reassigned from the `PreFitter`'s
  own fitted background count (`nbkg = "%.1E, 0, %.1E" % (_nbkg, 2 *
  _nbkg)`) before its only use (the `return nbkg` at the end). True of
  the original single-scope script's identical local-variable
  reassignment too - this was inert noise introduced by the Chunk 5
  extraction, not a preserved behavior difference. No test called
  `_seed_prefit_parameters()` directly with an `nbkg=` keyword (confirmed
  by grep), so no test needed updating.
- `doc/TIER3_SYSTEM.md`:
  - `run_templates.py`'s module-map row and the Chunk 5 decision
    paragraph updated for the new `_seed_prefit_parameters()` signature,
    with the removed-parameter history and reasoning recorded inline.
  - the Chunk 11 decision paragraph rewritten: the automated test is now
    credited only with what it actually proves (exit `0`, real non-empty
    `post_fit.pdf`); the byte-identical 41589-byte claim is now
    attributed to the one-time manual verification recorded in this same
    file's Chunk 11.B entry, with an explicit note that the automated
    test does not repeat or enforce it on every run.

### Verification performed

- `python -m pytest tests/test_run_fit.py tests/test_run_templates.py -v`
  → 11 passed. The strengthened assertion (`calls == []`) passing
  confirms XMLReader is genuinely never invoked once the check moved
  ahead of it, not just that quickFit is skipped.
- `grep -n "_seed_prefit_parameters(" tests/test_run_templates.py` →
  no direct calls (only through `prepare_run_templates`/
  `_stage_xml_templates`, both of which keep their own `nbkg` parameter
  unchanged), confirming the signature change had no test blast radius.
- `python scripts/quality_check.py --mode full` (rerun fresh after both
  code changes) → 172 passed, 8 deselected, ruff clean, black clean (29
  files unchanged), exit code 0 - identical to the pre-fix run, showing
  neither change touched anything the lightweight gate exercises beyond
  the two files edited.
- `grep -nE '[[:blank:]]+$'` over every changed file and `git diff
  --check` → both clean.
- Scientific gate rerun (`python -m pytest
  tests/test_analysis_workflows_integration.py -m "integration and
  requires_root" -v`) - see result recorded below; `build_fit_extract()`
  and `prepare_run_templates()` are both on this gate's real,
  authoritative code path, so a rerun (not just the lightweight gate) is
  the correct verification for behavior-affecting production changes,
  unlike the previous, comment-only commit. Result: **1 passed, 2
  deselected, 172.97 seconds, exit code 0** -
  `test_authoritative_j100_j50_workflows_match_frozen_reference` still
  matches the frozen `tests/references/analysis_reference.json` exactly.
  This run happened to exercise both edits for real, not just in
  isolation: it was observed mid-run (`ps aux`) actually executing
  `python/run_anaFit.py --doprefit` against the real J100 fixture, which
  drives `run_templates.py`'s `doprefit` branch (and therefore
  `_seed_prefit_parameters()`, whose `nbkg` parameter was just removed)
  and `run_fit.py`'s `build_fit_extract()` (whose validation check was
  just reordered ahead of the real XMLReader subprocess call it now
  precedes) on the authoritative code path, not a stub.

### Considered and not changed

- **`analysis_results.json`'s `repository_dirty` field was added under
  `schema_version: 2` rather than a new version** (`a83e888`, prior to
  this session). Checked against repository history before deciding not
  to act: this repeats an already-established, precedented pattern in
  this repository (an earlier 2026-08-27 schema change made the
  identical choice - see `doc/ACTIVITY_LOG.md`'s own schema-version-2
  entries from that date), and both times shipped with a full
  regeneration of the two tracked canonical manifests in the same
  commit, so no stale `schema_version: 2` manifest missing the new field
  is left committed in this repository. Not a Tier 3 concern (it
  predates this plan's own commits) and not something this branch's
  review is the right place to relitigate unilaterally. Documented as a
  Known Limitation in `doc/TIER3_SYSTEM.md` instead of changed.
- **The latent dual-module-import hazard from `pyproject.toml`'s
  `pythonpath = [".", "python"]`** - confirmed directly
  (`python.run_execution is not run_execution` inside one interpreter)
  that a module is reachable two ways with two distinct module objects.
  Not changed: removing either `pythonpath` entry would break real,
  currently-passing tests that depend on it (the flat-style entry for
  `tests/test_run_anaFit.py`'s own module-loading helper; the dotted
  entry for every other test file's `from python.<module> import ...`
  style), and no test in this repository currently straddles both styles
  for the same module, so there is no live bug to fix, only a documented
  risk for future test-writing. Documented as a Known Limitation in
  `doc/TIER3_SYSTEM.md` instead of changed.

### Compliance review

1. Every change traces to a specific, verified finding from the review
   that preceded this commit - two real code fixes (fail-fast ordering,
   dead parameter) and two documentation-accuracy fixes - plus two items
   deliberately left alone and recorded as Known Limitations rather than
   silently dropped.
2. Both code changes are pure refactors with no change to any success
   path's output: `run_fit.py`'s check is relocated, not altered, and
   still raises the identical `ValueError` with the identical message;
   `run_templates.py`'s removed parameter was provably dead (never read
   before being overwritten), so nothing observable changed. The
   scientific gate rerun (not just the lightweight gate) confirms this
   for the real J100 workflow, including the exact `doprefit` and
   XMLReader code paths touched.
3. No new dependency, tool, or marker was introduced.
4. Activity-log entry appended (this content), not a rewrite of any
   existing section.

## 2026-09-04: End-to-end execution trace of the J100 launcher, and a fixed finding (`python/createBinning.py`)

### Objective

Trace `scripts/run_anaFit_J100.sh` from invocation to its final output
artifacts, listing every file it executes along the way, and document
which of those files do not follow the Tier 3 decomposition-and-testing
system (`doc/TIER3_SYSTEM.md`). The trace surfaced one real defect
(`python/createBinning.py` fails to parse); the user then asked for it to
be fixed and tested by rerunning the analysis, folded into this same
entry rather than a separate one, since nothing from the trace-only work
had been committed yet.

### What changed

- Added `doc/TIER3_EXECUTION_TRACE.md`: a full call-graph trace of one
  real J100 run (`FIT_PARS=six`, `sigmean=400`, `dosignal=0`, `dolimit=0`,
  `doprefit=1`), from `scripts/run_anaFit_J100.sh` through
  `scripts/setup_buildAndFit.sh`, `python/run_anaFit.py` and its seven
  Tier 3 modules, into the external XMLReader/quickFit submodule binaries,
  the plotting layer, and back out to the final output files. Classifies
  every file the trace touches into three categories: part of the Tier 3
  system (cites `doc/TIER3_SYSTEM.md` directly rather than repeating it),
  legitimately outside Tier 3's documented scope but still on this repo's
  own code (`python/PreFit.py`, `ExtractPostfitFromWS.py`,
  `ExtractFitParameters.py`, `createBinning.py`, `FindBHWindow.py`,
  `scripts/setup_buildAndFit.sh`), and a different category entirely -
  third-party code in external Git submodules (`xmlAnaWSBuilder`,
  `quickFit`, `pyBumpHunter`, `workspaceCombiner`, confirmed via
  `.gitmodules`).
- Added a cross-reference from `doc/TIER3_SYSTEM.md`'s "Purpose and
  audience" section to the new trace document.
- **Found, while tracing, that `python/createBinning.py` did not
  parse**: `python3 -c "import ast; ast.parse(open('python/createBinning.py').read())"`
  raised `IndentationError: unexpected indent` at line 11. Root-caused to
  a stray one-space indent on the `tfile`/`IsZombie`/`reso_fit` null-check
  block, introduced in commit `e6bfd96` (2026-07-30). Confirmed this was
  dormant: `run_fit.py`'s `build_fit_extract()` only calls this script
  when `Input/data/dijetisrTLA/mjjResolutionBinning_<rangelow>.root` is
  missing, and both fixtures this repository's tests actually use
  (`mjjResolutionBinning_481.root` for J100, `mjjResolutionBinning_344.root`
  for J50) are already committed, so that branch had never fired in the
  scientific gate or CI.
- **Fixed** `python/createBinning.py`: dedented the five affected lines
  back to column 0, matching every other top-level statement in the
  file. Pure whitespace change - no other line touched, no logic altered.
  Documented in `doc/TIER3_EXECUTION_TRACE.md`'s Section 5 (rewritten
  from "found, not fixed" to "found and fixed", with the fix's own
  verification recorded there); the earlier "Purpose and audience"
  cross-reference in `doc/TIER3_SYSTEM.md` updated to match. Explicitly
  out of scope for this fix: `createBinning.py` is still not decomposed
  into functions, still has no dedicated test file, and is still
  unregistered in `scripts/quality_check.py` - it remains outside the
  Tier 3 system, just no longer syntactically broken. Also out of scope:
  this repository has no committed `Input/data/dijetisrTLA/resolutionFits.root`
  at all (the file this script's own logic reads) - a separate,
  pre-existing gap, noted but not addressed here.

### Verification performed

- Every file in the trace was read directly (`run_anaFit.py`,
  `run_masking.py`, `run_fit.py`, `run_templates.py`,
  `scripts/setup_buildAndFit.sh`, `python/PreFit.py`,
  `ExtractPostfitFromWS.py`, `ExtractFitParameters.py`,
  `createBinning.py`, `FindBHWindow.py`), not inferred from
  `doc/TIER3_SYSTEM.md`'s existing descriptions.
- `grep -rn` across `tests/` for each of the five out-of-scope files'
  class/module names, confirming every match is a `ModuleType` stub used
  to isolate a Tier 3 module under test, or a subprocess command-string
  assertion in the integration test - never a direct unit test of that
  file's own logic.
- `python3 -c "import ast; ast.parse(...)"` run individually against all
  five out-of-scope Python files at trace time; only `createBinning.py`
  failed.
- Confirmed both `mjjResolutionBinning_481.root`/`mjjResolutionBinning_344.root`
  are tracked and present, and that 481/344 match J100's/J50's own
  `rangelow` values in the two launcher scripts.
- Confirmed via `.gitmodules` and `git submodule status` that
  `xmlAnaWSBuilder`, `quickFit`, `pyBumpHunter`, `workspaceCombiner` are
  external submodules, not this repository's own code.
- Fix verification: `python3 -c "import ast; ast.parse(...)"` now
  succeeds on `createBinning.py`. Ran the fixed script for real, exactly
  as `run_fit.py` invokes it (`python3 python/createBinning.py -s 481 -e
  3000 -o <path>`), against a synthetic `resolutionFits.root` built on
  the fly with a trivial `TF1` named `gsc_mjj_reso_fit` (a real one isn't
  committed to this repository at all - noted above, not addressed
  here): exit 0, and the resulting file contained a real `mjjBinning`
  `TH1F` with 38 bins spanning exactly `[481, 3000]`, confirmed by
  reading it back with `ROOT.TFile.Open(...)`. Both the synthetic input
  and the scratch output were deleted afterward; `git status` on
  `Input/` came back clean.
- Reran the scientific gate
  (`tests/test_analysis_workflows_integration.py -m "integration and
  requires_root"`) end to end against the fix: **1 passed, 2 deselected,
  289.19 seconds, exit code 0** - `ps aux` confirmed mid-run it was
  genuinely executing the real J100 `run_anaFit.py --doprefit` process,
  not passing coincidentally.
- Reran `python scripts/quality_check.py --mode full`: 172 passed, 8
  deselected, Ruff clean, Black clean (29 files unchanged), exit code 0.
- `grep -nE '[[:blank:]]+$'` and `git diff --check` on all changed files:
  clean.

### Compliance review

1. The trace itself changed no production code (pure documentation),
   matching the original request; the one production-code change in this
   entry (`python/createBinning.py`'s dedent) was made only after the
   user explicitly asked for it, and is a one-line whitespace fix with no
   logic change.
2. The defect found is reported *and* fixed, with both the fix and its
   verification recorded plainly - root cause, why it was dormant, the
   fix itself, and the two-gate + direct-execution verification that
   proves it now works and regresses nothing.
3. No new dependency, tool, or marker introduced. `createBinning.py`
   remains unregistered in `quality_check.py` and undecomposed -
   explicitly not brought into Tier 3 compliance by this fix, since that
   was never asked for.
4. Activity-log entry appended and edited in place while still
   uncommitted (this content), not a rewrite of any already-committed
   entry.

## 2026-09-04: Extend the Tier 3 plan to the five hot-path support files (Chunks 13-18, planning only)

### Objective

The user asked for `doc/TIER3_COMPLETION_PLAN.md` to be updated so the
five hot-path support files `doc/TIER3_EXECUTION_TRACE.md` found outside
Tier 3 (`python/PreFit.py`, `python/ExtractFitParameters.py`,
`python/ExtractPostfitFromWS.py`, `python/createBinning.py`,
`python/FindBHWindow.py`) get decomposed and tested with the same
formula as Chunks 0-12. This entry covers **planning only**: writing
Chunks 13-18 into the plan document. Actually executing them (real
characterization tests, real extraction, real gates) is separate,
substantial follow-on work, explicitly not done here.

Two decisions were confirmed with the user before drafting: (1) reopen
`doc/TIER3_COMPLETION_PLAN.md` itself rather than start a new Tier 4
document; (2) for two dormant bugs found in `ExtractPostfitFromWS.py`
during design research, add two separate, optional, explicitly-scoped
fix chunks (16a/16b) rather than only document-and-preserve them (the
plan's default for every other quirk found).

### What changed

- `doc/TIER3_COMPLETION_PLAN.md`: Section 0 and Section 3 updated to
  describe the extended, nine-file scope (the original four-file scope
  is preserved as a dated historical statement, not silently rewritten).
  Section 4 gained subsections 4.4/4.5 (target decomposition tables and
  import/testing-tier notes for the five files). Section 6 gained Chunks
  13 (`createBinning.py`), 14 (`FindBHWindow.py`), 15
  (`ExtractFitParameters.py`), 16 (`ExtractPostfitFromWS.py`, the primary
  decomposition target) plus optional Chunks 16a/16b (the two dormant-bug
  fixes), 17 (`PreFit.py`), and 18 (a single-commit documentation update,
  to run only once Chunks 13-17 land) - each using the exact Step A/Step
  B table/prose template Chunks 1-11 already established. Section 7
  gained the `FindBHWindow.py` dedicated-interpreter gate command.
  Section 9's completion definition extended to "Chunks 0 through 18"
  with new bullets, including an explicit caveat that the standard
  scientific gate does not by itself prove `FindBHWindow.py`'s or fully
  `createBinning.py`'s correctness. Section 10's scope boundary updated
  "four" to "nine."
- `doc/TIER3_SYSTEM.md` and `doc/TIER3_EXECUTION_TRACE.md`: one small,
  accurate pointer added/revised in each, noting Chunks 13-18 now exist
  as a plan but are **not yet executed** - deliberately not rewriting
  either document's actual-status claims, since none of the five files'
  real decomposition/testing has happened yet. `doc/TIER3_SYSTEM.md`
  describes only what has actually happened (its own opening sentence's
  citation requirement) and is not updated further until Chunk 18 itself
  runs.

### Research performed before drafting

Two Explore agents read `doc/TIER3_COMPLETION_PLAN.md`/`doc/TIER3_SYSTEM.md`
in full (exact section structure, chunk template, guardrails, every
"Tier 3 is complete" claim with line numbers) and all five target files
plus their real call sites and existing test-stub patterns in full. A
Plan agent then designed the concrete per-file decomposition against
that fact base. Two corrections to initial assumptions were found by
direct verification during that research, both recorded in the plan
itself: `numpy` is not importable in `.venv/bin/python` (affects Chunk
14's test design); and `ExtractFitParameters`/`ExtractPostfitFromWS`'s
shared `wsfile` constructor parameter is actually the fit-result file in
production for both classes, not the workspace file either name
suggests (confirmed directly from `run_fit.py:114-168`).

### Verification performed

- `grep -nE '[[:blank:]]+$'` across all three changed docs: clean.
- `git diff --check`: clean.
- `grep -n "the four named\|four files\|Chunks 0-12\|Chunks 0 through 12\|no other file is in scope" doc/TIER3_COMPLETION_PLAN.md`:
  the four remaining hits are all legitimate local/historical references
  (Chunk 12's own "as it stood at Chunk 12's completion" framing; Chunk
  17's "these four files" meaning four of the *five new* files that keep
  a module-level `import ROOT`; Chunk 15's "the other four files" meaning
  the other four of the five new files; Chunk 18's own acceptance-check
  text) - none is a stale document-wide scope claim.
- Confirmed all 8 new/optional chunk headers (13, 14, 15, 16, 16a, 16b,
  17, 18) present, in order, via `grep -n "^### Chunk 1[3-8]"`.
- `python scripts/quality_check.py --mode full`: 172 passed, 8
  deselected, Ruff clean, Black clean (29 files unchanged), exit code 0 -
  unaffected, since no production code changed.

### Compliance review

1. This is a planning-document change only - no production code, no
   test file, no `scripts/quality_check.py` registration change (there is
   nothing new to register yet; the five target files' real test files
   don't exist until Chunks 13-17 are actually executed).
2. Every quirk/bug found in the five target files during design research
   is preserved in the plan text with an explicit preserve-or-fix
   decision and rationale, matching this repository's established
   "characterize and preserve, never silently clean up" principle -
   including the two dormant bugs the user explicitly chose to schedule
   fix chunks for (16a/16b), each kept separate from Chunk 16's own
   extraction commit.
3. `doc/TIER3_SYSTEM.md`'s and `doc/TIER3_EXECUTION_TRACE.md`'s
   actual-status claims were not rewritten to describe unexecuted work as
   done - only a small, accurate forward-pointer was added to each.
4. Activity-log entry appended (this content), not a rewrite of any
   existing section.

## 2026-09-04: Resolve Chunks 13/14's two open pre-Step-A verification items

### Objective

Chunks 13 and 14 of `doc/TIER3_COMPLETION_PLAN.md` (added earlier today)
each flagged one fact that needed direct confirmation before their real
Step A could be written: Chunk 13's `.Get(...)` key name, and Chunk 14's
committed-fixture directory-structure requirement. Both are resolved here
by direct verification - closing out the last open items in the planning
stage - with one significant, unplanned discovery surfaced along the way.

### What changed

- `doc/TIER3_COMPLETION_PLAN.md` Chunk 13: replaced the "confirm this
  directly" hedge with the confirmed key name (`"gsc_mjj_reso_fit"`, read
  directly from `python/createBinning.py`'s own `.Get(...)` call - matches
  what was already assumed).
- `doc/TIER3_COMPLETION_PLAN.md` Chunk 14: replaced the "not yet verified"
  paragraph with a confirmed fact - the committed
  `run/fits/J100/run_481_3000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root`
  does carry both `Run3TLA_bkgonly_rebinned/postfit` and
  `Run3TLA_rebinned/data` (confirmed by opening it and walking its
  `TDirectory` structure with ROOT directly) - no synthetic fixture
  needed for Chunk 14 either, same as Chunks 15/16.
- Added a new paragraph to Chunk 14 recording an unplanned discovery made
  while resolving the above: `run/fits/run_135_1000_sixPar/` and
  `run/fits/run_135_1000_sevenPar/` are real, committed, tracked masked-
  fit fixtures (`PostFit_*_masked.root`, `FitParameters_*_masked.root`,
  and a real `BHresults.json`, confirmed via `git ls-files`) - not
  produced by either current launcher script, not referenced by any test
  today. This directly contradicts `doc/TIER3_SYSTEM.md`'s existing Known
  Limitations claim that "No masked-fit fixture... exists in this
  repository" (written for `plot_postfit.cpp`'s Chunk 11). Left as an
  explicitly open decision for whoever picks up Chunk 14 - not acted on
  in this pass, since neither correcting that claim nor changing Chunk
  14's design was what this pass was asked to do.

### Verification performed

- `grep -n '\.Get(' python/createBinning.py` - confirms the key name.
- Opened `run/fits/J100/run_481_3000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root`
  directly with ROOT and walked its full `TDirectory` tree - confirms
  both required category subdirectories are present.
- `git ls-files run/fits/run_135_1000_sixPar/ run/fits/run_135_1000_sevenPar/`
  - confirms the masked fixtures are real and tracked, not local-only
  artifacts.
- `grep -rln "run_135_1000" tests/` - confirms no test references them.
- `grep -nE '[[:blank:]]+$' doc/TIER3_COMPLETION_PLAN.md` and
  `git diff --check`: clean.
- `python scripts/quality_check.py --mode full`: 172 passed, 8
  deselected, Ruff clean, Black clean, exit code 0 (unaffected - no
  production code changed).

### Compliance review

1. Both resolved items are read-only verification, not chunk execution -
   still within the planning stage the user asked about, not a start of
   Chunks 13/14's actual work.
2. The masked-fixture discovery is recorded plainly, not silently
   dropped or acted on unilaterally - it touches an already-committed
   doc's claim and a chunk's own design, both left for explicit decision.
3. Activity-log entry appended (this content), not a rewrite of any
   existing section.

## 2026-09-04: Untrack non-canonical analysis output (run/fits/run_135_1000_*)

### Objective

The user stated a repository policy: analysis-run outputs should
generally not be tracked in git unless needed for Tier 1/2 comparison.
Applied directly to `run/fits/run_135_1000_sixPar/` and
`run/fits/run_135_1000_sevenPar/` - the masked-fit fixture directories
surfaced by the previous entry's discovery.

### What changed

- `git rm` both directories (51 tracked files total: `PostFit_*.root`,
  `FitResult_*.root`, `FitParameters_*.root`, both masked and unmasked,
  `BHresults.json`, XML templates, PDFs, logs, `AnaWSBuilder.dtd`) -
  removed from both the git index and the working tree.
- `doc/TIER3_COMPLETION_PLAN.md` Chunk 14's "related discovery" paragraph
  (added in the previous entry) rewritten from "not yet acted on" to
  "since resolved" - records that the removal restores
  `doc/TIER3_SYSTEM.md`'s existing Known Limitations claim ("No
  masked-fit fixture... exists in this repository") to being accurate
  again, and that `FindBHWindow.py`'s masked path remains untested by any
  committed fixture (Chunk 14's own dedicated-interpreter subprocess test
  is still the only real proof of its correctness, on the unmasked case).
- Saved the underlying policy as a persistent project memory (this
  session's memory store), including the nuance found while
  investigating: J100/J50's own tracked non-JSON output files
  (`PostFit_anaFit_sixPar_bkgOnly.root` etc.) are legitimately tracked
  despite going beyond `analysis_results.json` - they match
  `doc/TIER1_SYSTEM.md`'s own documented canonical output contract and
  are real, load-bearing fixtures `tests/test_plot_post_fit.py` reads by
  path directly. `run_135_1000_*` matched none of those three criteria.

### Verification performed

- `grep -rln "run_135_1000" tests/`: confirmed zero references before
  removal.
- Confirmed neither current launcher script (`scripts/run_anaFit_J100.sh`/
  `run_anaFit_J50.sh`) uses `rangelow=135`.
- Confirmed via `.gitignore`'s `run/*`/`run/**` rules (with only
  `!run/fits/J100/...`/`!run/fits/J50/...` re-including the canonical two
  directories) that these files were never meant to be tracked in the
  first place.
- `git status --short` after `git rm`: only the expected deletions.
- `grep -nE '[[:blank:]]+$' doc/TIER3_COMPLETION_PLAN.md` and
  `git diff --check`: clean.
- `python scripts/quality_check.py --mode full`: 172 passed, 8
  deselected, Ruff clean, Black clean, exit code 0 - confirms no test
  depended on the removed files. The scientific gate was not rerun for
  this change: it generates its own fresh run in a `tmp_path` and does
  not read `run/fits/run_135_1000_*` at all, and no production code was
  touched.

### Compliance review

1. Action taken only after explicit user confirmation (asked via a
   direct yes/no choice before removing tracked files).
2. Verified via grep that nothing depended on the removed files before
   removing them, not assumed.
3. The stale plan-document paragraph referencing these files as a
   reusable fixture was corrected in the same commit as their removal,
   not left dangling.
4. Activity-log entry appended (this content), not a rewrite of any
   existing section.

## Chunk 13.A — Characterization tests for python/createBinning.py

### Objective

Pin down the current, unmodified behavior of `python/createBinning.py`
(a flat 32-line top-level script, zero functions, no `main()`, no
`__main__` guard) before any extraction, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 13.

### Target functions — inputs and outputs (as they exist today)

There are no functions to characterize individually - the whole file is
one top-to-bottom script body, run only ever as a subprocess in
production (`run_fit.py`'s `execute("python3 python/createBinning.py
-s {rangelow} -e {rangehigh} -o {binningFileName}")`). Characterized as
a single whole-script unit, mirroring Chunk 10.A's own precedent for
`plotPostFit.py` before its extraction:

| Unit | Inputs | Outputs | Side effects |
|---|---|---|---|
| whole script | `-s/--start`, `-e/--end`, `-o/--output` CLI args; a `resolutionFits.root` file at the hardcoded path `Input/data/dijetisrTLA/resolutionFits.root`, containing a `"gsc_mjj_reso_fit"` object exposing `.Eval(x)` | writes a `TH1F` named `"mjjBinning"` to `-o`'s path | opens/reads the hardcoded input file; raises `OSError`/`KeyError` if it's missing or the key isn't found |

### Tests added

- `test_createBinning_script_produces_expected_binning_for_real_fixture`
  — builds a synthetic `resolutionFits.root` (a flat 5%-resolution `TF1`
  named `"gsc_mjj_reso_fit"`) at the real, hardcoded input path (this
  repository commits no real one - confirmed via `find`, and recorded in
  `doc/TIER3_EXECUTION_TRACE.md` Section 5), runs the unmodified script
  for real against range `[481, 3000]`, and asserts the output file
  contains a `mjjBinning` `TH1F` with exactly **38 bins spanning
  `[481, 3000]`** - the same result already observed once this session
  during the syntax-bug fix, so this test both pins current behavior and
  cross-checks that prior observation. The synthetic input file is
  removed in a `finally` block regardless of outcome, and the test
  refuses to run at all (asserts first) if a real `resolutionFits.root`
  ever exists, to never risk overwriting one.

### What this commit does NOT do

No production file is modified. `python/createBinning.py` is unchanged
byte-for-byte in this diff - confirmed with `git diff --stat` (only
`tests/test_create_binning.py` and this activity-log entry appear).

### Verification performed

- `python -m pytest tests/test_create_binning.py -v` -> **1 passed,
  98.02s** (real ROOT/RooFit runtime, sourced
  `scripts/setup_buildAndFit.sh`), rerun a second time after a
  Black-reformat of the test file itself (whitespace only) to confirm
  the reformat changed nothing observable - both runs passed.
- `python -m ruff check tests/test_create_binning.py` /
  `python -m black --check tests/test_create_binning.py`: clean (one
  line-length finding was fixed via Black before this commit).
- `git diff --stat` (before staging): only `tests/test_create_binning.py`
  - confirms no production file touched.
- `python scripts/quality_check.py --mode full`: 172 passed, 8
  deselected, Ruff clean, Black clean, exit code 0 - unaffected, since
  the new file is not yet registered (Step B's job).
- `git status --short Input/`: clean after the test run - the synthetic
  fixture was removed as intended.

### Compliance review (Section 8, Characterization variant)

- [x] Base commit for these tests: `bdccd29` (this branch's tip
  immediately before this commit) - `python/createBinning.py` is
  identical to its state as fixed and verified in the earlier
  `d66a73c` commit.
- [x] The new test asserts a real output (histogram bin count and exact
  bin edges), not merely "does not raise."
- [x] `git diff --stat` shows no production file touched.
- [x] The test was run for real, twice, and its output reviewed directly
  (not only reported) - confirming both the exit code and the exact
  bin-count/edge assertions against the real subprocess output.
- [x] Human-verification checkpoint: reviewed and confirmed in this same
  session before Step B's commit follows.

## Chunk 13.B — Extract python/createBinning.py into named functions

### Objective

Move the whole-script logic characterized in Step A (commit `e77724f`)
into named, individually-tested functions plus a `main()` and a new
`if __name__ == "__main__":` guard, per `doc/TIER3_COMPLETION_PLAN.md`
Chunk 13.

### What changed

- `python/createBinning.py` restructured from a flat 32-line top-level
  script into `parse_args(argv=None)`, `load_resolution_fit(input_path=...)`,
  `resolve_bin_edges(reso_fit, rangelow, rangehigh)`,
  `build_binning_histogram(bin_edges)`, `main(argv=None)`, and a new
  `if __name__ == "__main__": main()` guard this file previously lacked
  (matching Chunk 10's `plotPostFit.py` precedent exactly).
- `import ROOT` deferred from module scope into the three functions that
  actually touch it (`load_resolution_fit`, `build_binning_histogram`,
  `main`) - **not explicitly in the plan's original text**, added after
  confirming directly that a module-level `import ROOT` would have broken
  the plan's own stated goal ("both need zero ROOT" for `parse_args()`/
  `resolve_bin_edges()`): `.venv/bin/python -c "from python import
  createBinning"` failed with `ModuleNotFoundError: No module named
  'ROOT'` before this fix, and succeeded after. Matches every other
  deferred-import module in this plan (`run_fit.py`, `run_provenance.py`,
  `run_templates.py`).
- The hardcoded input path and `from array import array`'s deferred
  placement (now inside `build_binning_histogram`) preserved verbatim,
  per the plan.
- `tests/test_create_binning.py` gained 7 new tests: 3 for `parse_args()`,
  3 for `resolve_bin_edges()` (against a hand-written `_FakeResolutionFit`
  exposing only `.Eval(x)` - zero ROOT, one cross-checking the real
  fixture's own 38-bin/[481,3000] result via an independently-verified
  edge list, one with a different resolution/range, one confirming the
  `rangehigh` clamp), and 2 for `load_resolution_fit()`'s failure paths
  (both real ROOT, marked). Step A's end-to-end test kept unchanged
  (Test Relocation Rule - it was already written directly into its final
  file, so nothing needed moving), now exercising the extracted `main()`
  instead of the original inline script.
- `scripts/quality_check.py`: `python/createBinning.py` and
  `tests/test_create_binning.py` registered in
  `python_targets`/`test_targets`.

### A real finding, verified and preserved, not fixed

While testing `load_resolution_fit()`'s failure paths directly, found
that on this repository's own installed PyROOT, `ROOT.TFile.Open()`
itself raises its own `OSError` for a missing file - a different message
than the function's own `if not tfile or tfile.IsZombie(): raise
OSError("Could not open Input/data/dijetisrTLA/resolutionFits.root")`
guard, which is therefore currently unreachable in practice here. This
is pre-existing behavior from the original single-scope script (the
check is unchanged), not something this extraction introduced, and it is
not dead code on every PyROOT build (some return a null `TFile` instead
of raising, which is exactly what the guard defends against) - preserved
verbatim, documented in a new source comment, not removed or "fixed."
The `KeyError` path (a valid, openable file simply missing the expected
key) **is** genuinely reached by this function's own code - confirmed
separately and given its own passing test.

Also verified directly, mirroring Chunk 10.B's own file-lifetime check:
unlike `plotPostFit.py`'s `TH1` objects, a ROOT `TF1` read back via
`TFile::Get()` stays evaluable after its owning `TFile` is closed (tested
both after the file object merely fell out of scope with `gc.collect()`
forced, and after an explicit `.Close()` call - both still returned the
correct value). `load_resolution_fit()` therefore safely returns only
the fit object and closes the file itself, rather than needing to hand
the file back to the caller the way `plotPostFit.py`'s
`load_postfit_histograms()` must.

### Confirm: no scientific behavior changed

`run_fit.py`'s call site (`execute(f"python3 python/createBinning.py -s
{rangelow} -e {rangehigh} -o {binningFileName}")`) is unchanged -
confirmed by `grep -n "createBinning" python/run_fit.py`. The extracted
script was run for real, exactly as `run_fit.py` invokes it, against a
synthetic fixture, and produced the identical 38-bin
`[481, 3000]` result already verified twice before (once during the
syntax-bug fix, once in Chunk 13.A). The integration-gate rerun below
confirms zero regression to the real J100/J50 workflows, though - as
already stated in Chunk 13's own plan text - that gate never exercises
this branch at all (both committed binning fixtures already exist), so
it proves no regression to the always-taken existence check, not this
chunk's own correctness; the real proof is the direct script run above
plus the 11 passing tests.

### Verification performed

- `python -m pytest tests/test_create_binning.py -v` -> **11 passed,
  63.51s** (8 fast/unmarked in 0.06s, 3 real-ROOT in the remainder).
- Ran the extracted script directly, exactly as `run_fit.py` invokes it,
  against a synthetic fixture: exit 0, produced a real 38-bin
  `mjjBinning` histogram spanning `[481, 3000]`, confirmed by reading it
  back; `git status --short Input/` clean afterward.
- `python scripts/quality_check.py --mode full` -> **180 passed, 11
  deselected**, Ruff clean, Black clean (31 files unchanged), exit code
  0.
- `python -m pytest tests/test_analysis_workflows_integration.py -m
  "integration and requires_root" -v` -> **1 passed, 2 deselected,
  159.63 seconds, exit code 0**.
- `git diff --check`: clean.
- `grep -n "createBinning" python/run_fit.py`: confirms the call site is
  byte-for-byte unchanged.

### Compliance review (Section 8, Extraction variant)

- [x] Step A's commit (`e77724f`) named above; this commit's relocated
  test is unchanged from it (nothing needed moving - it was already
  written into its final file).
- [x] No scientific constant, reference, tolerance, dependency revision,
  or canonical workflow argument touched.
- [x] `resolve_bin_edges()`'s two new fake-based tests are genuinely new,
  independently-verified assertions, not copied from Step A.
- [x] Every newly-introduced function has a dedicated test (success path
  for all four; failure path for `load_resolution_fit()` and
  `parse_args()`'s required-flag rejection).
- [x] `run_fit.py` still calls `python/createBinning.py` by the same
  subprocess command - confirmed by grep, not assumed.
- [x] All required gates ran and passed, output captured above.
- [x] `git diff --check` passes.
- [x] Activity-log entry appended (this content).
- [x] This entry names Chunk 13 as now resolved; Chunks 14-18 remain
  explicitly open.

## Chunk 14.A — Characterization tests for python/FindBHWindow.py

### Objective

Pin down the current, unmodified behavior of `python/FindBHWindow.py`
(a 113-line script: one clean `NpEncoder` class plus a `main(args)` that
holds the entire real workflow) before any extraction, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 14.

### Target functions/classes — inputs and outputs (as they exist today)

| Unit | Inputs | Outputs | Side effects |
|---|---|---|---|
| `NpEncoder.default(obj)` | any object `json.dumps` can't natively serialize | `int`/`float`/`list`, or delegates to `super().default()` | none |
| `main(args)` (whole workflow) | CLI args (`--inputfile`, `--bkghist`, `--datahist`, `--outputjson`, `--usebinnumbers`, plus unused `--inputxmlcard`/`--outputxmlcard`) | writes `outputjson` (`MaskMin`/`MaskMax`/`BlindRange`/`pyBHresult`); prints the blind range | opens `inputfile` via `uproot`; runs a `pyBumpHunter.BumpHunter1D` scan; writes hardcoded `bump.png`/`BH_statistics.png` to the current directory |

### Tests added

- `test_npencoder_serializes_numpy_integer` /
  `_floating` / `_ndarray` / `_falls_back_to_default_for_unknown_types` —
  characterize `NpEncoder.default()` directly, using a fake `numpy`
  module (real, instantiable `integer`/`floating`/`ndarray` classes) plus
  trivial empty fakes for `matplotlib`/`matplotlib.pyplot`/`uproot`/
  `pyBumpHunter` - the first use of a `numpy` module-name stub in this
  plan, since real `numpy` is not importable in this repository's own
  pytest dev venv either (confirmed directly).
- `test_findbhwindow_script_computes_expected_mask_window_for_real_fixture`
  — runs the real, unmodified script against the already-committed J100
  `PostFit_anaFit_sixPar_bkgOnly.root` fixture (confirmed to have both
  `Run3TLA_rebinned/postfit` and `Run3TLA_rebinned/data` -
  `run_masking.py`'s own hardcoded flag values), and asserts the exact,
  deterministic result (`seed=666` is fixed): `MaskMin=595.0`,
  `MaskMax=691.0`, `BlindRange="595,691"`, `pyBHresult` present, both
  plot files created. Confirmed deterministic by running the real script
  twice independently before writing this assertion.

### A real environment finding, verified and documented, not fixed

While writing the whole-script test, found that
`python/FindBHWindow.py`'s own production interpreter,
`pyBumpHunter/pyBH_env/bin/python3`, is broken in this environment: its
`pyvenv.cfg` sets `include-system-site-packages = false`, and neither
`uproot` nor `matplotlib` was ever installed into its own
`site-packages` (only `pyBumpHunter` itself, as an egg) -
`pyBumpHunter/pyBH_env/bin/python3 -c "import uproot"` fails with
`ModuleNotFoundError` before even reaching `pyBumpHunter`'s own import.
This means `run_masking.py`'s real subprocess command cannot run at all
in this environment. Pre-existing, not caused by this chunk, out of
scope to fix (mirrors `createBinning.py`'s missing-`resolutionFits.root`
gap) - `run_masking.py`'s call site is untouched.

Found and verified a working alternative instead: the ambient `python`
`scripts/setup_buildAndFit.sh` already puts on `PATH` (the same
LCG_102a interpreter `test_plot_post_fit.py`'s real-ROOT tests use) has
`numpy`/`matplotlib`/`uproot` all genuinely importable. It resolves
`pyBumpHunter` to this repository's own top-level submodule directory as
an empty namespace package (`BH.__file__ is None`,
`hasattr(BH, "BumpHunter1D") is False`) unless the submodule's own
package directory is explicitly **appended** to the *existing*
`PYTHONPATH` (replacing it was tried first and broke `matplotlib`, since
the LCG view's own setup already populates `PYTHONPATH` with the entries
`matplotlib`/`uproot` resolve from). With that append, all four
dependencies resolve correctly together - no new package installs, no
production-code change. This becomes this chunk's real-proof mechanism,
documented in `doc/TIER3_COMPLETION_PLAN.md` Chunk 14 alongside this
entry.

### What this commit does NOT do

No production file is modified. `python/FindBHWindow.py` is unchanged
byte-for-byte in this diff - confirmed with `git diff --stat` (only
`tests/test_find_bh_window.py`, this activity-log entry, and
`doc/TIER3_COMPLETION_PLAN.md`'s documentation of the environment finding
above appear).

### Verification performed

- `python -m pytest tests/test_find_bh_window.py -v` -> **5 passed,
  20.48s** (4 fast/unmarked NpEncoder tests, 1 real end-to-end test using
  the working ambient-interpreter combination).
- `python -m ruff check` / `python -m black --check` on the new test
  file: clean (one line-length finding fixed via Black before this
  commit).
- `git diff --stat` (before staging): `doc/TIER3_COMPLETION_PLAN.md` and
  the new test file only - no production file touched.
- `git status --short` after the real-fixture test run: clean - the
  probe's `cd` into `tmp_path` before invoking the script kept
  `bump.png`/`BH_statistics.png` out of the repository entirely.

### Compliance review (Section 8, Characterization variant)

- [x] Base commit for these tests: this branch's tip immediately before
  this commit (`9727e28`) - `python/FindBHWindow.py` is unchanged from
  its state there.
- [x] Every new test asserts a real output (exact serialized values for
  `NpEncoder`; exact deterministic `MaskMin`/`MaskMax`/`BlindRange` and
  real plot-file creation for the end-to-end test), not merely "does not
  raise."
- [x] `git diff --stat` shows no production file touched.
- [x] The tests were run for real, twice for the end-to-end case (once
  manually to confirm determinism before writing the assertion, once as
  the committed test itself), and reviewed directly.
- [x] Human-verification checkpoint: reviewed and confirmed in this same
  session before Step B's commit follows.

## Chunk 14.B — Extract python/FindBHWindow.py into named functions

### Objective

Move the whole-script logic characterized in Step A (commit `604b5cd`)
into named, individually-tested functions, deferring the heavy
third-party imports each needs, per `doc/TIER3_COMPLETION_PLAN.md`
Chunk 14.

### What changed

- `python/FindBHWindow.py` restructured into `NpEncoder` (unchanged),
  `parse_args(argv=None)`, `load_histograms(input_file, bkghist,
  datahist)`, `crop_data_to_background_range(bins, bins_data, data)`,
  `run_bump_hunter(data, bkg, bins)`, `save_bump_plots(hunter, data,
  bkg)`, `compute_mask_window(state, bins, firstbindata,
  use_bin_numbers)`, `write_mask_window_json(out_dict, outputjson)`,
  and `main(argv=None)` as the orchestrator.
- `import matplotlib`/`matplotlib.pyplot` deferred into
  `save_bump_plots()`; `import uproot` into `load_histograms()`;
  `from datetime import datetime` and `import pyBumpHunter as BH`
  into `run_bump_hunter()`. `import numpy as np` stays module-level
  (`NpEncoder` needs it as a name at call time; the two other "pure"
  functions never reference `np.` directly, only operate on values
  already numpy-typed by their caller).
- Confirmed-dead `import re, os` (from the original `import sys, re, os,
  argparse` line) removed - `grep -n "\bre\.\|\bos\."
  python/FindBHWindow.py` found zero uses of either in the whole file,
  confirmed before removing, matching the same explicit,
  separately-noted-removal precedent this plan already established.
- **Two real deviations from the plan's original target-functions table,
  found necessary by direct reading of the actual source (not
  discoverable from the table alone) and documented here rather than
  silently applied**:
  - `crop_data_to_background_range()` returns `(cropped_data,
    firstbindata)`, not just cropped data - `firstbindata` is also
    needed later, by `compute_mask_window()`'s `use_bin_numbers=True`
    branch. The plan's table only listed a cropped-values return.
  - `save_bump_plots()` takes `(hunter, data, bkg)`, not just `hunter` -
    `hunter.plot_bump()` needs `data`/`bkg` directly, not only the
    hunter object. The plan's table listed `save_bump_plots(bump_hunter)`
    only.
- `run_masking.py`'s call site (`pyBumpHunter/pyBH_env/bin/python3
  python/FindBHWindow.py ...`) is unchanged - confirmed via `grep -n
  "FindBHWindow" python/run_masking.py`.
- `tests/test_find_bh_window.py` gained 7 new tests: 3 for `parse_args()`,
  1 for `crop_data_to_background_range()` (plain Python lists - proven
  to need no real numpy call, only indexing/slicing), 2 for
  `compute_mask_window()` (one per `use_bin_numbers` branch, pinning
  both formulas independently), 1 for `write_mask_window_json()`
  (exercising `NpEncoder` end to end through a real file write). Step
  A's `NpEncoder` tests **dropped 3 of their 4 stubs** - an explicit,
  called-out exception to the Test Relocation Rule (no precedent for
  this in Chunks 0-13), since only `numpy` remains module-level
  post-extraction. Step A's end-to-end test kept unchanged, now
  exercising the extracted `main()`.
- `scripts/quality_check.py`: `python/FindBHWindow.py` and
  `tests/test_find_bh_window.py` registered in
  `python_targets`/`test_targets`.

### Confirm: no scientific behavior changed

`run_masking.py`'s call site is byte-for-byte unchanged (confirmed by
grep). The extracted script was run for real, exactly as
`run_masking.py` invokes it (using this chunk's own working
ambient-interpreter combination, per Step A), against the real J100
fixture, and produced the identical deterministic result already
verified in Step A (`MaskMin=595.0`, `MaskMax=691.0`,
`BlindRange="595,691"`). The integration-gate rerun below confirms zero
regression to the real J100/J50 workflows, though - as already stated in
Chunk 14's own plan text - that gate never exercises this file's real
behavior at all (both committed fixtures are unmasked); the real proof
is the 12 passing tests above, particularly the deterministic real-run
one.

### Verification performed

- `python -m pytest tests/test_find_bh_window.py -v` -> **12 passed,
  20.12s** (11 fast/unmarked in well under a second, 1 real end-to-end
  in the remainder).
- `python scripts/quality_check.py --mode full` -> **191 passed, 12
  deselected**, Ruff clean, Black clean (33 files unchanged), exit code
  0.
- `python -m pytest tests/test_analysis_workflows_integration.py -m
  "integration and requires_root" -v` -> **1 passed, 2 deselected,
  162.50 seconds, exit code 0**.
- `grep -n "FindBHWindow" python/run_masking.py`: confirms the call site
  is byte-for-byte unchanged.
- `git status --short` after every real-fixture test run: clean - no
  `bump.png`/`BH_statistics.png` left in the repository.
- `git diff --check`: clean.

### Compliance review (Section 8, Extraction variant)

- [x] Step A's commit (`604b5cd`) named above; this commit's relocated
  end-to-end test is unchanged from it, per the Test Relocation Rule;
  the `NpEncoder` tests' stub-drop is the one explicit, documented
  exception to that rule.
- [x] No scientific constant, reference, tolerance, dependency revision,
  or canonical workflow argument touched.
- [x] Every newly-introduced function has a dedicated, genuinely new
  test (not copied from Step A).
- [x] `run_masking.py` still invokes `python/FindBHWindow.py` by the
  same subprocess command - confirmed by grep, not assumed.
- [x] All required gates ran and passed, output captured above.
- [x] `git diff --check` passes.
- [x] Activity-log entry appended (this content).
- [x] This entry names Chunk 14 as now resolved; Chunks 15-18 remain
  explicitly open.

## Chunk 15.A — Characterization tests for python/ExtractFitParameters.py

### Objective

Pin down the current, unmodified behavior of
`python/ExtractFitParameters.py` (a 109-line script: one class,
`FitParameterExtractor`, whose `Extract()` — 42 lines — does the entire
real workflow, plus a thin `main()`) before Chunk 15's Step B, which
adds no new decomposition — this is the honest minimal-decomposition
case stated in `doc/TIER3_COMPLETION_PLAN.md` Chunk 15's own Rationale.

### Target functions/classes — inputs and outputs (as they exist today)

| Unit | Inputs | Outputs | Side effects |
|---|---|---|---|
| `FitParameterExtractor.__init__(self, wsfile)` | `wsfile: str` (in production, the fit-result file, despite the name — see below) | — | none |
| `Extract(self)` | — | populates `h1_params`/`h2_cov`/`h2_cor`/`nsig`/`nsigErr` | opens `wsfile`, reads the `fitResult` `RooFitResult` |
| `GetH1Params`/`GetH2Cov`/`GetH2Cor`/`GetNsig`/`GetNsigErr` | — | ROOT-typed values | lazily call `self.Extract()` if the corresponding attribute is falsy |
| `WriteRoot(self, outfile)` | `outfile: str` | — | writes the three histograms to a new file |

### Tests added

- `test_extract_and_accessors_and_writeroot_against_real_fixture` — real
  ROOT, constructs `FitParameterExtractor` against the already-committed
  `run/fits/J100/run_481_3000_sixPar/FitResult_anaFit_sixPar_bkgOnly.root`
  (exactly what `run_fit.py:168` passes as `wsfile` in production — the
  lowest fixture-sourcing risk of all five files in this plan, no
  synthetic fixture needed), calls `Extract()`, all 5 accessors, and
  `WriteRoot(tmp_path/"out.root")`, then re-opens that output file and
  asserts its three histograms are genuinely non-empty.
- `test_getnsig_and_getnsigerr_refire_extract_when_zero` /
  `_do_not_refire_extract_when_nonzero` — fast tests (no real ROOT call),
  stubbing `sys.modules["ROOT"]` with a trivial empty `ModuleType` purely
  so the module-level `import ROOT`/`from ROOT import *` resolves. Pin
  down the `if not self.nsig:` / `if not self.nsigErr:` falsiness quirk
  exactly as it exists today (preserve, not fix — matching Chunk 5's own
  precedent): a falsy (zero) cached value re-triggers `Extract()` on
  every single call; a truthy (non-zero) one does not.

### A real finding from the real fixture, characterized not assumed

The committed fixture is a bkg-only fit
(`FitResult_anaFit_sixPar_bkgOnly.root`) — confirmed directly by dumping
`floatParsFinal()`: its six parameters are `nbkg`/`p2`/`p3`/`p4`/`p5`/
`p6`, none containing the substring `"nsig"`. `GetNsig()`/`GetNsigErr()`
therefore genuinely return `None` against this real fixture, not a gap
in the test — asserted as the real observed behavior.

### Documented, not fixed: the shared `wsfile` name

`ExtractFitParameters.FitParameterExtractor`'s `wsfile` parameter and
`ExtractPostfitFromWS.PostfitExtractor`'s same-named parameter mean the
same thing in production (both receive the fit-result file, never the
workspace file either name suggests). Recorded here and will be recorded
again in Chunk 18's Known Limitations; not renamed, per Chunk 15's own
plan text.

### What this commit does NOT do

No production file is modified. `python/ExtractFitParameters.py` is
unchanged byte-for-byte in this diff — confirmed with `git diff --stat`
(only `tests/test_extract_fit_parameters.py` and this activity-log entry
appear).

### Verification performed

- `python -m pytest tests/test_extract_fit_parameters.py -v -m "not
  requires_analysis_dependencies"` -> **2 passed**.
- Under `scripts/setup_buildAndFit.sh`'s ambient interpreter:
  `python -m pytest tests/test_extract_fit_parameters.py -v -m
  "requires_root and requires_analysis_dependencies"` -> **1 passed,
  4.61s**.
- Full lightweight suite (`pytest -m "not requires_analysis_dependencies"
  tests/`): **194 passed, 15 deselected** (was 192 passed, 14 deselected
  immediately before this commit — +2 fast, +1 deselected, matching this
  file's 3 new tests exactly).
- `python -m ruff check` / `python -m black --check` on the new test
  file: clean (one formatting fix applied via Black before this commit).
- `git diff --stat` (before staging): the new test file and this
  activity-log entry only — no production file touched.
- `git status --short`: clean.
- `git diff --check`: clean.

### Compliance review (Section 8, Characterization variant)

- [x] Base commit for these tests: this branch's tip immediately before
  this commit (`058243b`) — `python/ExtractFitParameters.py` is
  unchanged from its state there.
- [x] Every new test asserts a real output (non-empty histograms and a
  real written file for the end-to-end test; exact call-count behavior
  for the falsiness-quirk tests), not merely "does not raise."
- [x] `git diff --stat` shows no production file touched.
- [x] The end-to-end test was run for real against the real committed
  fixture and reviewed directly; its unexpected-but-real `nsig is None`
  result was investigated (by dumping `floatParsFinal()` directly) rather
  than assumed away.
- [x] Human-verification checkpoint: reviewed and confirmed in this same
  session before Step B's commit follows.

## Chunk 15.B — Register python/ExtractFitParameters.py (no restructuring)

### Objective

Complete Chunk 15 per `doc/TIER3_COMPLETION_PLAN.md`'s own explicit
Rationale: `Extract()` (42 lines) is one cohesive block, and forcing a
3-way split would relocate, not reduce, its complexity, unlike Chunk
16's genuinely tangled 137-line `Extract()`. This chunk's entire value
is the file's first-ever direct test of its real behavior (Step A,
commit `f17de07`) plus registration — no production-code restructuring
is proposed or performed.

### What changed

- `python/ExtractFitParameters.py`: **unchanged, byte-for-byte** —
  confirmed via `git diff python/ExtractFitParameters.py` returning
  empty immediately before this commit. Step A's tests already exercise
  the file's real, existing structure directly; nothing in Step A's
  tests required any restructuring to pass.
- `tests/test_extract_fit_parameters.py`: no change needed — Step A
  already wrote its tests directly into this chunk's final file name (no
  interim characterization-only filename existed to move from, unlike
  Chunks 13/14's Test Relocation Rule), matching this chunk's
  no-decomposition design.
- `scripts/quality_check.py`: `python/ExtractFitParameters.py` and
  `tests/test_extract_fit_parameters.py` registered in
  `python_targets`/`test_targets` (inserted alphabetically:
  `createBinning.py` < `ExtractFitParameters.py` < `FindBHWindow.py`
  case-insensitively; same ordering for the paired test file).

### Confirm: no scientific behavior changed

`python/ExtractFitParameters.py` is byte-for-byte unchanged, so there is
no extracted code path to re-verify beyond what Step A's real-fixture
test already exercises directly (`Extract()`, all 5 accessors,
`WriteRoot()`, against the real, already-committed
`FitResult_anaFit_sixPar_bkgOnly.root`). `run_fit.py`'s call site
(`fpe = FitParameterExtractor(wsfile=fitresultfile)` at line 168) is
untouched — confirmed by `git diff python/run_fit.py` returning empty.

### Verification performed

- `git diff python/ExtractFitParameters.py`: empty, confirming no
  production restructuring occurred.
- `python -m pytest tests/test_extract_fit_parameters.py -v` -> **3
  passed** (2 fast, 1 real-ROOT end-to-end, run together under the
  ambient interpreter from `scripts/setup_buildAndFit.sh`).
- `python scripts/quality_check.py --mode full` -> lightweight suite
  **194 passed, 15 deselected**, Ruff clean, Black clean, exit code 0.
- `python -m pytest tests/test_analysis_workflows_integration.py -m
  "integration and requires_root" -v` (mandatory scientific gate,
  unchanged canonical J100/J50 workflows) -> **1 passed, 2 deselected,
  135.10s, exit code 0**.
- `git diff --check`: clean.
- `git status --short` after all real-fixture runs: clean.

### Compliance review (Section 8, Extraction variant)

- [x] Step A's commit (`f17de07`) named above; no test relocation was
  needed (Step A's tests already live in the chunk's final file).
- [x] No scientific constant, reference, tolerance, dependency revision,
  or canonical workflow argument touched.
- [x] No new function was introduced (this chunk's own Rationale states
  why), so there is no new-function-needs-a-new-test obligation beyond
  what Step A already added.
- [x] `run_fit.py` still constructs `FitParameterExtractor` the same
  way — confirmed by `git diff python/run_fit.py` returning empty.
- [x] All required gates ran and passed, output captured above.
- [x] `git diff --check` passes.
- [x] Activity-log entry appended (this content).
- [x] This entry names Chunk 15 as now resolved; Chunks 16 (+ optional
  16a/16b), 17, and 18 remain explicitly open.
