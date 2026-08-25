# Tier 3 Refactoring Plan

## 1. Tier 3 objective

Tier 3 will convert the current analysis implementation into a clear, testable, and maintainable structure without changing its accepted scientific behaviour.

The primary target is the analysis logic currently coordinated through `python/run_anaFit.py` and the authoritative launchers:

```text
scripts/run_anaFit_J100.sh
scripts/run_anaFit_J50.sh
```

The refactored system must continue to reproduce the accepted J100 and J50 background-only results through the existing executable characterization gate. The canonical workflows, fit configurations, schema-version-2 manifests, provenance records, output contracts, and numerical comparison policy must remain unchanged unless a separate, explicitly approved scientific change is proposed.

Tier 3 is structural work only. It must not introduce:

- CLs processing
- Signal-analysis changes
- Different fit models
- Different input files or histogram paths
- Different fit ranges
- New numerical tolerances
- Tier 4 orchestration
- Repository-wide Ruff or Black formatting
- Unrelated installer or dependency changes

## 2. Tier 3 source-of-truth documents

Four documents should control Tier 3.

### 2.1 `doc/TIER3_SYSTEM.md`

Create this document before substantial refactoring begins.

It will be the primary Tier 3 specification and operating guide. Every GitHub Copilot-generated proposal must be compared against it before implementation.

It should define:

- Tier 3 purpose and scope
- Current analysis entry points
- Protected scientific behaviour
- Intended module structure
- Responsibilities of each module
- Allowed dependency directions
- Testing requirements
- Required Tier 1 and Tier 2 gates
- Documentation requirements
- Change-control procedure
- Completion criteria
- Explicit exclusions

### 2.2 `doc/ACTIVITY_LOG.md`

Continue treating this as the authoritative chronological evidence record.

Every substantial Tier 3 change must be appended as a new dated and titled section. Existing entries must not be rewritten, reordered, condensed, or removed. Later entries may state that an earlier intermediate status has been superseded, but the original historical entry must remain unchanged.

### 2.3 Existing Tier 1 and Tier 2 documents

The following remain authoritative constraints:

```text
doc/TIER1_SYSTEM.md
doc/TIER1_ENVIRONMENT_PROVENANCE.md
doc/TIER2_SYSTEM.md
```

Tier 3 documentation must refer to these documents rather than duplicating or weakening their contracts. They record the accepted scientific workflow, runtime split, gate commands, dependency revisions, installer status, test policies, and known limitations.

### 2.4 `doc/TIER3_REFACTORING_PLAN.md`

This file records the planned implementation sequence and migration checkpoints.

The distinction is:

- `TIER3_REFACTORING_PLAN.md`: planned sequence and migration checkpoints
- `TIER3_SYSTEM.md`: accepted, implemented Tier 3 architecture and operating instructions

Once Tier 3 is complete, `TIER3_SYSTEM.md` becomes the durable source of truth. This plan remains as design context.

## 3. Non-negotiable safety rules

### Rule 1: Refactor without changing scientific behaviour

A change is acceptable only if all relevant tests pass and the authoritative J100/J50 characterization gate continues to reproduce the frozen scientific reference.

The existing gate protects:

- J100 and J50 fit parameters
- J100 and J50 chi-square p-values
- Expected unmasked behaviour
- Absence of BumpHunter output in the canonical runs
- Empty CLs results
- Fresh required scientific artifacts
- Schema-version-2 provenance
- Runtime and dependency identity

These protections must not be replaced with weaker Tier 3 tests.

### Rule 2: Make small, reviewable changes

Each refactoring unit should normally:

1. Extract or simplify one responsibility.
2. Add or update focused tests.
3. Run focused tests.
4. Run Ruff and Black through the approved quality gate.
5. Run the full lightweight gate.
6. Review the diff.
7. Append the result to `doc/ACTIVITY_LOG.md`.
8. Commit the change separately.

Do not combine multiple major extractions in one commit.

### Rule 3: Tests should precede or accompany extraction

Before changing logic, identify the behaviour being protected.

For every newly created function:

- Add a focused unit test.
- Cover its successful path.
- Cover meaningful failure paths.
- Check return values and externally visible side effects.
- Avoid testing private implementation details unnecessarily.
- Confirm that the original analysis path calls the new function.
- Retain integration coverage through the existing launchers.

A function should not be considered accepted merely because the full gate passes. It needs direct tests appropriate to its responsibility.

### Rule 4: No broad automated cleanup

Do not run:

```bash
python -m ruff check .
python -m black --check .
python -m black .
```

Continue using the explicit targets controlled by:

```bash
python scripts/quality_check.py --mode full
```

This preserves the Tier 2 explicit-target policy and avoids unrelated repository-wide changes.

### Rule 5: Do not allow GitHub Copilot to redefine scope

GitHub Copilot may propose implementations, tests, documentation, names, and decompositions. It must not independently:

- Change numerical values
- Change scientific configuration
- Change the frozen reference
- Relax assertions or tolerances
- Remove failure handling
- Remove provenance fields
- Change accepted artifact requirements
- Mark failing tests as skipped or expected failures
- Add dependencies without review
- Begin Tier 4 orchestration

## 4. Proposed target architecture

The exact filenames should be confirmed after a dependency and responsibility audit, but a reasonable target is:

```text
python/
├── run_anaFit.py
├── analysis_config.py
├── analysis_commands.py
├── analysis_artifacts.py
├── analysis_results.py
├── analysis_provenance.py
├── analysis_bumphunter.py
└── analysis_reference.py
```

The existing `run_anaFit.py` should gradually become a thin coordinator rather than being replaced in one large rewrite.

### Verified implementation adjustment

The verified implementation adds three focused modules to the original target
architecture:

- `analysis_fit.py` owns the ROOT-backed fit and post-fit extraction stage.
- `analysis_templates.py` owns generated XML template replacement.
- `analysis_cli.py` owns command-line parsing and normalization.
- `analysis_results.py` owns schema-version-2 manifest assembly, validation, and
  atomic writing; `analysis_fit.py` owns ROOT-backed result extraction.

These additions preserve the plan’s dependency direction and structural-only
scope. `analysis_commands.py` and `analysis_bumphunter.py` also provide explicit
command-builder functions, while the established scientific command strings
remain unchanged.

### 4.1 `analysis_config.py`

Responsible for:

- Validated analysis configuration
- Fit-range representation
- Analysis mode flags
- Input and output path resolution
- Configuration validation

Tests should cover valid configurations, missing values, invalid ranges, invalid flags, and path-handling behaviour.

### 4.2 `analysis_commands.py`

Responsible for:

- Required subprocess execution
- Exit-code validation
- Required-output validation
- Command-result reporting

Tests should cover success, nonzero status, missing outputs, empty outputs where prohibited, and clear error reporting.

### 4.3 `analysis_artifacts.py`

Responsible for:

- Required artifact definitions
- Freshness checks
- Non-empty checks
- Stale-output removal
- Unexpected masked-output detection

Tests should use temporary directories and synthetic files rather than running ROOT.

### 4.4 `analysis_results.py`

Responsible for:

- Fit-result extraction
- Manifest construction
- Atomic manifest writing
- Result-payload validation

Tests should cover valid manifests, incomplete results, invalid types, failed analysis behaviour, and atomic-write guarantees.

### 4.5 `analysis_provenance.py`

Responsible for:

- SHA-256 calculation
- Git revision collection
- Scientific runtime details
- Dependency revisions
- Input and configuration provenance
- Schema-version-2 provenance validation

Existing provenance tests should be migrated carefully rather than duplicated or weakened.

### 4.6 `analysis_bumphunter.py`

Responsible for:

- BumpHunter command preparation
- Stale result removal
- Result loading
- Mask-range validation
- Conditional masking decisions

Existing BumpHunter safety tests should continue to cover malformed JSON, missing fields, invalid bounds, failed execution, and stale-output protection.

### 4.7 `run_anaFit.py`

Ultimately responsible only for:

1. Receiving the analysis request.
2. Validating configuration.
3. Calling the established analysis stages.
4. Handling the conditional masking path.
5. Constructing the final result.
6. Writing the success manifest only after successful completion.
7. Returning a meaningful process status.

The public command-line interface and launcher compatibility must remain stable.

## 5. Refactoring phases

### Phase 0: Establish the pre-refactor checkpoint

Before editing analysis structure, run the full lightweight gate:

```bash
source .venv/bin/activate
python scripts/quality_check.py --mode full
```

Run the prepared-dependency gate:

```bash
python -m pytest tests/test_repo_utils.py \
  -m "requires_analysis_dependencies" -v
```

Run scientific runtime readiness:

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -k authoritative_setup_provides_scientific_runtime -v
```

Run the authoritative scientific gate:

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v
```

Record:

- Branch and commit
- Python and tool versions
- Test counts
- Gate durations
- Exit codes
- Working-tree status
- Any known warnings
- Confirmation that the reference files were not modified

Append a dated `Tier 3 pre-refactor baseline` section to `doc/ACTIVITY_LOG.md`.

No Tier 3 extraction should begin if this checkpoint is failing.

### Phase 1: Document the current analysis structure

Before proposing a final target structure, document the existing flow.

The audit should identify:

- Entry points
- Function call sequence
- External commands
- Input files
- Generated configurations
- Workspaces and fit outputs
- BumpHunter branch
- Manifest-writing point
- Failure-propagation paths
- Global state
- Environment-variable dependencies
- File-system side effects
- ROOT-specific boundaries
- Pure logic that can be tested without ROOT

This phase should not alter behaviour.

Add the findings to `doc/TIER3_REFACTORING_PLAN.md`, not to the historical descriptions in Tier 1 or Tier 2.

### Phase 2: Create `doc/TIER3_SYSTEM.md`

Use the same concise style as the established system documents:

```markdown
## Tier-3 system: test-protected structural refactoring

### Current status

### Purpose

### Scope

### Protected scientific contracts

### Target architecture

### Module responsibilities

### Dependency rules

### Test policy

### Refactoring workflow

### Gate commands

### Documentation policy

### Change control

### Known limitations

### Completion definition
```

Initially label the system clearly as planned or in progress. Do not describe proposed modules as implemented until they exist and have passed verification.

### Phase 3: Extract pure functions first

Begin with logic that does not require ROOT, subprocesses, or actual analysis outputs.

Good first candidates include:

- Path construction
- Configuration normalization
- Fit-range validation
- Flag validation
- Expected artifact-list construction
- Manifest payload assembly
- Mask-range validation
- Command-argument construction

For each extraction:

1. Add characterization tests for current behaviour if missing.
2. Extract one function.
3. Give it explicit inputs and a return value.
4. Avoid reading globals within the function.
5. Add direct unit tests.
6. Replace the original inline logic with the function call.
7. Run focused and full lightweight checks.

### Phase 4: Isolate file-system operations

Move file handling behind small functions with explicit paths.

Cover:

- Required file checks
- Freshness checks
- Non-empty artifact checks
- Stale-output removal
- JSON reading and writing
- Atomic replacement
- Output-directory creation

Use `tmp_path` in tests. Do not use canonical `run/fits` directories in unit tests.

### Phase 5: Isolate external command execution

Preserve the current mandatory command contract while making command execution testable.

Requirements include:

- Explicit argument lists where practical
- Captured exit status
- Required output assertions
- Clear exception messages
- No hidden continuation after failure
- No manifest creation after failure
- No stale-output acceptance

Use controlled test doubles or monkeypatching. Do not run ROOT or scientific executables in ordinary unit tests.

### Phase 6: Separate BumpHunter logic

Keep the masking path isolated and explicitly conditional.

Tests must prove:

- No masking path when it is not triggered
- Stale `BHresults.json` is removed
- Failed BumpHunter execution stops the analysis
- Missing fresh output stops the analysis
- Malformed output stops the analysis
- Invalid mask bounds stop the analysis
- Valid bounds reach the masked-refit stage
- The canonical J100/J50 runs remain unmasked

### Phase 7: Separate provenance and manifest generation

Schema-version-2 output is an accepted Tier 1 contract and must remain stable.

Tests should establish:

- Required provenance fields are preserved.
- Hashes are associated with the correct files.
- Dependency revisions remain complete.
- Runtime identity remains recorded.
- Invocation settings remain recorded.
- Schema-version-1 reading remains supported.
- New canonical runs write schema version 2.
- Failed analyses cannot write successful manifests.

Do not regenerate or modify frozen references merely to make a refactor pass.

### Phase 8: Reduce `run_anaFit.py` to orchestration

Only after extracted modules are tested should the main routine be simplified.

The refactored coordinator should visibly express the pipeline stages, while detailed validation and side effects are delegated to tested functions.

Avoid changing the full call structure in one commit.

### Phase 9: Final verification and documentation

Run every authoritative gate.

Review:

```bash
git status -sb
git diff --check
git diff --stat
git diff
```

Confirm:

- No frozen reference changed unexpectedly.
- No canonical scientific configuration changed.
- No dependency revision changed.
- No unrelated file was formatted.
- No Tier 1 or Tier 2 assertion was weakened.
- New modules are included in the explicit Ruff and Black target lists.
- New test files are included in the explicit pytest targets.
- `doc/TIER3_SYSTEM.md` describes only verified behaviour.
- `doc/ACTIVITY_LOG.md` contains the final checkpoint.

## 6. Per-change checklist for GitHub Copilot

Use this checklist for every GitHub Copilot-assisted change.

```text
1. Read doc/TIER3_SYSTEM.md.
2. Read the relevant sections of:
   - doc/TIER1_SYSTEM.md
   - doc/TIER2_SYSTEM.md
   - doc/TIER1_ENVIRONMENT_PROVENANCE.md
   - doc/ACTIVITY_LOG.md
3. State the single responsibility being refactored.
4. Identify the existing behaviour and tests protecting it.
5. Identify any missing focused tests.
6. Add or update focused tests before or alongside the extraction.
7. Make the smallest viable structural change.
8. Do not change scientific constants, references, tolerances, or workflow arguments.
9. Run focused tests.
10. Run the approved full lightweight gate.
11. Run heavier gates when the change crosses their boundary.
12. Review the complete diff.
13. Compare the result against doc/TIER3_SYSTEM.md.
14. Update doc/TIER3_SYSTEM.md if verified architecture changed.
15. Append a new dated section to doc/ACTIVITY_LOG.md.
16. Stage explicit paths only.
```

## 7. Required source-of-truth review

Before accepting any change, compare it with this file and answer all of the following:

- Does the change address one clearly stated Tier 3 responsibility?
- Is the change structural rather than scientific?
- Are all scientific constants and workflow arguments unchanged?
- Are frozen references and numerical tolerances unchanged?
- Does the change preserve schema-version-2 provenance?
- Does the change preserve failure propagation and stale-output protection?
- Is every new function covered by focused tests?
- Is the production execution path proven to call the new function?
- Are new production and test files included in the explicit quality targets?
- Have the required Tier 1 and Tier 2 checks passed?
- Has `doc/TIER3_SYSTEM.md` been updated only with verified behaviour?
- Has a new dated section been appended to `doc/ACTIVITY_LOG.md`?
- Have existing activity-log entries remained unchanged?

If any answer is no, the change is not ready to be accepted.

## 8. Gate frequency

### After every extracted function

Run focused tests:

```bash
python -m pytest tests/<relevant_test_file>.py -q
```

Run formatting and linting through the accepted target mechanism. If the new files have not yet been added to `scripts/quality_check.py`, add them explicitly with corresponding policy-test updates.

### After every coherent refactoring commit

Run:

```bash
python scripts/quality_check.py --mode full
```

### After changes affecting dependencies or prepared checkouts

Run:

```bash
python -m pytest tests/test_repo_utils.py \
  -m "requires_analysis_dependencies" -v
```

### After changes affecting setup, runtime selection, command execution, ROOT interaction, output artifacts, manifests, provenance, or workflow coordination

Run runtime readiness and the authoritative scientific gate:

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -k authoritative_setup_provides_scientific_runtime -v

python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v
```

### Before any Tier 3 merge or completion claim

Run all four gates and record every exit code in `doc/ACTIVITY_LOG.md`.

## 9. Activity-log entry template

```markdown
## YYYY-MM-DD: Tier-3 <specific change title>

### Objective

Describe the single structural problem addressed.

### Pre-change protection

List the existing tests and contracts that protected the behaviour before editing.

### Changes completed

- List each changed or added file.
- Describe each extracted responsibility.
- State explicitly whether scientific behaviour was intended to change.

### Tests added or updated

- Name each test file.
- Describe successful and failure paths covered.
- Explain how the new functions are called by the production path.

### Verification performed

- Focused pytest command and result
- Full lightweight gate result
- Prepared-dependency result, if applicable
- Runtime-readiness result, if applicable
- Scientific characterization result, if applicable
- Ruff result
- Black result
- `git diff --check` result

### Source-of-truth review

Confirm that the change was reviewed against:

- `doc/TIER3_REFACTORING_PLAN.md`
- `doc/TIER3_SYSTEM.md`
- `doc/TIER1_SYSTEM.md`
- `doc/TIER2_SYSTEM.md`
- `doc/TIER1_ENVIRONMENT_PROVENANCE.md`

### Current status

State what is complete and what remains.

### Scope boundary

Confirm that no scientific configuration, frozen reference, tolerance, CLs behaviour, or Tier-4 orchestration was changed.
```

## 10. Documentation policy

Documentation must distinguish clearly between:

- Proposed architecture
- Work in progress
- Verified implementation
- Known limitation
- Deferred work

Do not describe a proposed module, check, or workflow as implemented until its code exists and the relevant verification has passed.

When the implementation changes:

1. Update `doc/TIER3_SYSTEM.md` with the verified current system.
2. Append the evidence to `doc/ACTIVITY_LOG.md`.
3. Update this plan only if the intended migration sequence or scope changes.
4. Do not rewrite historical activity-log entries.
5. Do not duplicate Tier 1 or Tier 2 contracts where a direct reference is sufficient.

Use the concise style established by the existing Tier system documents:

- Short sections
- Direct statements
- Bulleted responsibilities
- Exact file paths
- Exact gate commands
- Recorded results and exit codes
- Clear scope boundaries
- Explicit known limitations

## 11. Git and change-control policy

Before editing:

```bash
git status -sb
git diff --check
```

After editing:

```bash
git status -sb
git diff --check
git diff --stat
git diff
```

Requirements:

- Stage explicit paths only.
- Do not use `git add .`.
- Do not use `git commit -a`.
- Keep each commit limited to one coherent refactoring responsibility.
- Include tests and documentation with the production change they protect.
- Do not include unrelated generated outputs.
- Do not rewrite or squash the historical activity log within ordinary Tier 3 changes.
- Do not change canonical manifests or frozen references unless a separately reviewed scientific change explicitly requires it.

## 12. Tier 3 completion definition

Tier 3 is complete only when:

- `python/run_anaFit.py` has a clear coordination role.
- Major responsibilities are separated into appropriately named modules.
- Every new production function has effective focused coverage.
- Failure paths remain protected.
- Tier 1 scientific contracts remain unchanged.
- Schema-version-2 provenance remains valid.
- The lightweight gate passes.
- The prepared-dependency gate passes.
- Runtime readiness passes.
- The authoritative J100/J50 scientific gate passes.
- Ruff and Black pass over explicit approved targets.
- `doc/TIER3_SYSTEM.md` accurately describes the implemented system.
- `doc/ACTIVITY_LOG.md` records every substantial change.
- No earlier activity-log history has been rewritten.
- No proposed feature is documented as complete without verification.
- The branch is reviewed, committed, pushed, and the hosted lightweight gate passes.
- Known limitations remain documented honestly.

## 13. Current scope boundary

Tier 3 is limited to test-protected structural refactoring of the existing background-only J100/J50 analysis system.

The following remain outside scope:

- CLs implementation or characterization
- Signal-analysis changes
- New physics models
- New canonical inputs
- Changed fit ranges or histogram paths
- Changed numerical references or tolerances
- Tier 4 orchestration
- Hamilton, Snakemake, or another workflow engine
- Repository-wide style cleanup
- Unrelated dependency or installer redesign

Any future proposal to cross this boundary requires a separate plan, explicit review, new acceptance criteria, and updated source-of-truth documentation.
