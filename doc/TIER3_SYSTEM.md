# Tier 3 System: Test-Protected Structural Refactoring

## Current Status

**Phase 0 Pre-Refactor Baseline**: Established 2026-08-24. All protective gates passing. Ready for Phase 1–9 execution.

**Current state**: Phases 0–9 verification is complete. The worktree remains
uncommitted because commit and push were not requested.
The verified extracted modules are `analysis_config.py`,
`analysis_artifacts.py`, `analysis_commands.py`, `analysis_bumphunter.py`,
`analysis_provenance.py`, `analysis_results.py`, `analysis_fit.py`,
`analysis_templates.py`, and `analysis_cli.py`.

---

## Purpose

Convert the monolithic `python/run_anaFit.py` (1,100+ lines) into a clear, testable, and maintainable modular structure. Each new module will have explicit responsibilities, focused unit tests, and independently verifiable contracts.

Refactoring must preserve all accepted scientific behaviour and protected contracts established in Tier 1 and Tier 2.

---

## Scope

### In Scope

- Structural decomposition of `run_anaFit.py` into focused, tested modules
- Pure-function extraction (configuration, path resolution, validation, file operations)
- Command-argument assembly functions
- BumpHunter orchestration isolation
- Provenance and manifest generation module
- Existing test expansion to cover extracted functions
- Documentation updates (this document, activity log)
- Quality-target list updates to include new modules

### Explicitly Out of Scope

- CLs workflow implementation
- Signal-analysis changes
- Different fit models, inputs, histograms, or ranges
- New numerical tolerances or assertion relaxation
- Dependency changes without review
- Repository-wide Ruff or Black formatting
- Tier 4 orchestration
- Generated-output policy changes (plots, temporary files)

---

## Protected Scientific Contracts

### J100 Background-Only Baseline

- **Input file**: `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root`
- **Histogram**: `hists_yStar06_rejectEta_10_16/afterSelection/nominal/h_mjj`
- **Fit range**: 481–3000 GeV
- **Model**: Six-parameter background-only
- **Prefit**: Enabled
- **Mask threshold**: 0.01
- **Signal/limit flags**: Disabled
- **Frozen p_chi2**: `0.018448750724012808`
- **Masked**: false
- **Output directory**: `run/fits/J100/run_481_3000_sixPar/`

### J50 Background-Only Baseline

- **Input file**: `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root`
- **Histogram**: `hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj`
- **Fit range**: 344–2079 GeV
- **Model**: Six-parameter background-only
- **Prefit**: Enabled
- **Mask threshold**: 0.01
- **Signal/limit flags**: Disabled
- **Frozen p_chi2**: `0.07853114301666252`
- **Masked**: false
- **Output directory**: `run/fits/J50/run_344_2079_sixPar/`

### Launcher Contracts

Both `scripts/run_anaFit_J100.sh` and `scripts/run_anaFit_J50.sh`:
- Invoke `python/run_anaFit.py` with deterministic arguments
- Support optional `FIT_PARS`, `ANAFIT_OUTPUT_DIR`, `ANAFIT_SETUP_SCRIPT`, `ANAFIT_RUNNER`, `ANAFIT_SKIP_PLOTS` environment variables
- Propagate exit status from Python runner
- Create optional PDFs (non-scientific artifacts)

### Manifest and Provenance

- **Format**: Schema version 2, JSON
- **Required fields**: `schema_version`, `status`, `masked`, `p_chi2`, `provenance`
- **Provenance fields**: `repository_commit`, `runtime`, `tool_revisions`, `input`, `configurations`, `invocation`
- **Writing policy**: Atomic replace (.tmp → final)
- **Success condition**: Manifest written only after all stages succeed
- **Failure condition**: No manifest (or partial) if any stage fails

### Failure Propagation

- **No manifest written** on any subprocess failure
- **No manifest written** if BumpHunter fails or produces invalid output
- **No manifest written** if masked refit fails
- **Exit code 0** only if manifest successfully written with `status: "success"`
- **Stale BumpHunter JSON** removed before BumpHunter execution

---

## Target Architecture

### Verified Module Structure

```
python/
├── run_anaFit.py           ← thin coordinator (after refactoring)
├── analysis_config.py      ← configuration validation
├── analysis_commands.py    ← subprocess execution & validation
├── analysis_artifacts.py   ← required artifact definitions & checks
├── analysis_results.py     ← fit-result extraction & manifest assembly
├── analysis_provenance.py  ← provenance record building
├── analysis_bumphunter.py  ← BumpHunter orchestration
├── analysis_fit.py         ← ROOT-backed fit and post-fit extraction
├── analysis_templates.py   ← XML template replacement
├── analysis_cli.py         ← command-line parsing and normalization
└── analysis_reference.py   ← reference validation (existing)
```

### Module Responsibilities

#### `analysis_config.py` (Verified Phase 3 extraction)

**Responsible for**:
- Fit-range validation (low < high, both positive integers)
- Output folder creation and validation
- Configuration flags normalization (signal names, prefit defaults)
- Fit-parameter count detection from background file

**Interface**:
- `validate_fit_range(rangelow, rangehigh) → None` (raises ValueError)
- `validate_output_folder(folder) → Path` (creates if needed)
- `normalize_signal_name(sigmean, sigwidth) → str`
- `detect_parameter_count(backgroundfile) → int`

**Tests**: 8+ focused unit tests
- Valid ranges (J100, J50)
- Invalid ranges (reversed, equal, negative)
- Folder creation (new, existing)
- Signal-name normalization

#### `analysis_commands.py` (Verified Phase 5 extraction)

**Responsible for**:
- XMLReader command assembly and execution
- quickFit command assembly and execution
- Output validation after subprocess calls

**Interface**:
- `build_xmlreader_command(topfile, outputfile) → str`
- `build_quickfit_command(wsfile, poi, maskrange, outputfile) → str`
- `execute_xmlreader(command, expected_outputs) → bool`
- `execute_quickfit(command, expected_outputs) → bool`

**Tests**: 6+ focused unit tests
- Command assembly with escaping
- Success with expected outputs
- Failure with nonzero exit
- Missing expected output detection

#### `analysis_artifacts.py` (Verified Phase 4 extraction)

**Responsible for**:
- Required artifact list construction
- Freshness checks
- Non-empty artifact checks
- Stale-output removal

**Interface**:
- `define_required_artifacts(folder, pars_count) → List[Path]`
- `check_artifact_freshness(artifact_path, before_time) → bool`
- `check_artifact_nonempty(artifact_path) → bool`
- `remove_stale_bumphunter_json(folder) → None`

**Tests**: 8+ focused unit tests
- Artifact list construction
- Freshness checks with timestamps
- Non-empty validation
- Stale-file removal

#### `analysis_results.py` (Verified Phase 7 extraction)

**Responsible for**:
- Manifest payload assembly
- Result validation

**Interface**:
- `extract_fit_parameters(fitresult_file) → Dict`
- `extract_p_chi2(postfit_file) → float`
- `assemble_manifest_payload(p_chi2, masked, provenance) → Dict`
- `validate_manifest_payload(payload) → None` (raises ValueError)

**Tests**: 6+ focused unit tests
- Parameter extraction from valid fit
- P-value extraction
- Payload assembly
- Invalid payload rejection

#### `analysis_provenance.py` (Verified Phase 7 extraction)

**Responsible for**:
- SHA-256 file hashing
- Git revision collection
- Scientific runtime details
- Dependency revisions
- Input and configuration provenance

**Interface**:
- `calculate_file_sha256(path) → str`
- `get_git_revision(repo_path) → str`
- `collect_scientific_runtime() → Dict`
- `build_file_provenance(path, repository_root) → Dict`
- `build_analysis_provenance(...) → Dict`

**Tests**: 8+ focused unit tests
- File hashing (success, missing)
- Git revision (success, non-repo)
- Runtime collection
- Provenance assembly

#### `analysis_bumphunter.py` (Verified Phase 6 extraction)

**Responsible for**:
- BumpHunter command preparation
- Stale result removal
- Result loading and validation
- Mask-range validation
- Conditional masking decisions

**Interface**:
- `prepare_bumphunter_command(postfit_file, output_json) → str`
- `load_bumphunter_results(results_file) → Dict`
- `validate_mask_range(mask_min, mask_max) → None` (raises ValueError)
- `should_mask(p_chi2, threshold) → bool`

#### `analysis_templates.py` (Verified Phase 8 extraction)

**Responsible for**:
- Regular-expression replacement in generated XML templates
- Preserving the existing replacement error contract

#### `analysis_cli.py` (Verified Phase 8 extraction)

**Responsible for**:
- Command-line argument parsing
- Default signal-name normalization
- Output-folder creation
- Optional systematics JSON loading

#### `analysis_fit.py` (Verified Phase 8 extraction)

**Responsible for**:
- XMLReader and quickFit-backed fit execution
- ROOT post-fit extraction and p-value calculation
- Fit-parameter output generation

#### Verified plan alignment

The implemented architecture extends the original plan’s reasonable target with
`analysis_fit.py`, `analysis_templates.py`, and `analysis_cli.py` so the
ROOT-backed fit stage, template mutation, and CLI boundary are independently
owned and tested. `analysis_commands.py` and `analysis_bumphunter.py` expose
explicit command builders matching the established command strings.

**Tests**: 8+ focused unit tests
- Command preparation
- JSON loading and validation
- Invalid result rejection
- Mask-range validation

#### `run_anaFit.py` (After refactoring)

**Ultimately responsible only for**:
1. Receiving the analysis request
2. Parsing and validating configuration
3. Calling the established analysis stages in order
4. Handling the conditional masking path decision
5. Coordinating manifest/provenance generation
6. Writing the success manifest only after completion
7. Returning meaningful process status

**Measured size**: 465 lines, reduced from the 1,100+ line starting point. The
original 200–300-line estimate was not reached without a broader rewrite and
is retained as a documented limitation.

---

## Dependency Rules

**Allowed dependencies** (from higher to lower level):
- `run_anaFit.py` → calls all specialized modules
- Specialized modules (e.g., `analysis_config.py`) → may call other specialized modules
- Specialized modules → may call pure utilities (hash, path, git)
- No module → should call `run_anaFit.py` or depend on others

**Prohibited dependencies**:
- Circular dependencies (e.g., `A` → `B` → `A`)
- Hidden global state (all dependencies explicit)
- Direct ROOT operations in non-extraction modules (ROOT only in `PostfitExtractor`, `FitParameterExtractor`, `PreFitter`)
- Subprocess calls outside designated command modules

---

## Test Policy

### Unit Tests (Per-Function)

Every new function has focused unit tests:

1. **Normal successful path** (at least 1 test)
2. **Meaningful invalid input** (at least 1 test)
3. **Relevant failure paths** (at least 1 test)
4. **Return values and side effects** (verified in all tests)

**Test location**: `tests/test_<module_name>.py`

**Use temporary directories** (`tmp_path` from pytest) for file I/O tests. Do not use canonical `run/fits` directories.

### Integration Tests

**Do not** run ROOT, XMLReader, quickFit, BumpHunter, or complete scientific workflows in lightweight unit tests.

**Do** verify end-to-end J100/J50 workflows via marked `integration` and `requires_root` tests in `tests/test_analysis_workflows_integration.py`.

### Regression Tests

After each extraction, run:
```bash
python -m pytest tests/test_<new_module>.py -v
python -m pytest tests/test_run_anaFit.py -v  # verify launcher still works
python scripts/quality_check.py --mode full
python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v
```

---

## Refactoring Workflow

### Phases (from `TIER3_REFACTORING_PLAN.md`)

1. **Phase 0** (COMPLETE): Pre-refactor baseline checkpoint
2. **Phase 1–2** (COMPLETE): Analysis audit and Tier 3 system specification
3. **Phase 3** (RECOMMENDED FIRST): Extract pure configuration functions
4. **Phase 4**: Isolate file-system operations
5. **Phase 5**: Isolate external command execution
6. **Phase 6** (COMPLETE): Separate BumpHunter logic and result extraction
7. **Phase 7** (COMPLETE): Separate provenance and manifest generation
8. **Phase 8** (COMPLETE): Reduce `run_anaFit.py` to orchestration
9. **Phase 9** (COMPLETE): Final verification and documentation

### Per-Change Workflow

For every extracted module:

1. Identify single responsibility
2. Identify current code path and behaviour
3. Identify Tier 1/2 contracts protecting it
4. Identify existing tests covering it
5. **Add focused tests BEFORE extraction** (or alongside)
6. Extract function with explicit inputs/return values
7. Replace original inline logic with function call
8. Run focused unit tests: `pytest tests/test_<module>.py -v`
9. Run launcher tests: `pytest tests/test_run_anaFit.py -v`
10. Run full gate: `python scripts/quality_check.py --mode full`
11. Run integration gate: `pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`
12. Review diff: `git diff`, `git diff --stat`, `git diff --check`
13. Append result to `doc/ACTIVITY_LOG.md` (new dated section)
14. Stage only explicit intended paths: `git add <files>`

---

## Gate Commands

### Lightweight Full Gate (Fast)

```bash
python scripts/quality_check.py --mode fast
```

**Expected**: 103 tests passed, 2 deselected, exit 0

### Lightweight Full Gate (Complete)

```bash
python scripts/quality_check.py --mode full
```

**Expected**: 103 tests passed, Ruff passed, Black passed, exit 0

### Prepared Dependency Gate

```bash
python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v
```

**Expected**: 2 tests passed, 11 deselected, exit 0

### Scientific Runtime Readiness

```bash
python -m pytest tests/test_analysis_workflows_integration.py -k authoritative_setup_provides_scientific_runtime -v
```

**Expected**: 1 test passed, 2 deselected, exit 0

### Authoritative Scientific Characterization

```bash
python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v
```

**Expected**: 1 test passed, 2 deselected, exit 0, p_chi2 matches frozen reference

---

## Documentation Policy

### Per-Change Documentation

Every substantial Tier 3 change must include:

1. **Source code**: Clear comments explaining responsibility
2. **Tests**: Docstrings in test functions explaining what is tested
3. **Activity log entry**: Dated section in `doc/ACTIVITY_LOG.md` with:
   - Objective
   - Files and responsibilities changed
   - Tests added or updated
   - Test results (exact command output)
   - Full gate result
   - Git diff summary
   - Current status

### This Document (TIER3_SYSTEM.md)

- Describe **implemented** architecture only (not "planned")
- Update with new module responsibilities once verified
- Update completion definition as phases complete
- Do not describe proposed functions as implemented until code exists and tests pass

---

## Change Control

### Before Editing

```bash
git status -sb
git diff --check
```

### After Editing

```bash
git status -sb
git diff --check
git diff --stat
git diff
```

### Staging Rules

- Stage only explicit intended paths (no `git add .`)
- Do not stage unrelated generated files (PDFs, ROOT files)
- Do not stage formatting-only changes
- Verify all staged files with `git diff --cached`

---

## Known Limitations

1. **CLs workflow deferred**: Signal analysis and limit-setting code exists but is not exercised in canonical workflows
2. **Systematics dictionary experimental**: `--sysfile` argument exists but is not used in canonical J100/J50 workflows
3. **Schema-version-1 reading legacy**: Support for legacy manifests exists but canonical runs produce v2 only
4. **Prefit logic not yet extracted**: PreFitter class remains external; integration TBD
5. **Plot generation non-scientific**: PDF outputs are not required artifacts and may be skipped

---

## Completion Definition

Tier 3 is complete when:

1. ✓ **All phases executed**: Phases 0–9 completed and documented
2. ✓ **All modules extracted**: Seven focused modules created and tested
3. ✓ **All functions have focused tests**: Every new function has ≥3 unit tests
4. ✓ **run_anaFit.py reduced**: Coordinator is 465 lines, with the original
   200–300-line estimate documented as unmet
5. ✓ **All gates pass**: Fast, full, dependency, runtime, scientific gates all exit 0
6. ✓ **Frozen reference unchanged**: J100/J50 p_chi2 values match baseline
7. ✓ **No new dependencies**: No pip packages added
8. ✓ **New modules in quality targets**: All new .py files in explicit Ruff/Black/pytest lists
9. ✓ **TIER3_SYSTEM.md final**: All sections describe verified, implemented architecture
10. ✓ **ACTIVITY_LOG.md complete**: All phases recorded with verification outputs
11. **Git history**: Phase changes remain uncommitted; explicit commit and push
   are required before hosted merge, but were not performed by this session

---

## References

- **Controlling plan**: `doc/TIER3_REFACTORING_PLAN.md`
- **Audit report**: `TIER3_AUDIT_REPORT.md`
- **Protected Tier 1 contracts**: `doc/TIER1_SYSTEM.md`
- **Protected Tier 2 environment**: `doc/TIER2_SYSTEM.md`
- **Chronological record**: `doc/ACTIVITY_LOG.md`
- **Repository baseline**: Commit `a7e8db56408a2413122af0e4a6880b3580012f07` (2026-08-24)
