# Tier-3 system: structural refactoring of the coordinator and plotting layer

This guide describes the finished Tier-3 refactoring: splitting
`python/run_anaFit.py`, `plot_edm.py`, `python/plotPostFit.py`, and
`plot_postfit.cpp` into focused, individually-tested functions and
modules, with every public entry point's external behavior preserved
exactly. It is modeled on `doc/TIER1_SYSTEM.md` and
`doc/TIER2_SYSTEM.md`'s structure. Every claim below cites the specific
test function(s) or gate run that proves it, per
`doc/TIER3_COMPLETION_PLAN.md` Chunk 12's own requirement.

## Purpose and audience

Tier 3 is "assisted structural refactoring" (per `Claude science raw
output.md`'s original framing): moving and decomposing existing code
using extract-function/extract-module technique, never changing what any
of it computes. This document is for anyone reading or extending the
seven `run_anaFit.py` modules, `plot_edm.py`, `python/plotPostFit.py`, or
`plot_postfit.cpp` after this refactor - it answers "where did function X
go", "what does module Y depend on", and "which test file exercises this"
without needing to replay the full chunk-by-chunk history in
`doc/ACTIVITY_LOG.md`.

For how these seven modules and the plotting layer sit inside a real,
complete run - and which non-Tier-3 files (`python/PreFit.py`,
`ExtractPostfitFromWS.py`, `ExtractFitParameters.py`, `createBinning.py`,
`FindBHWindow.py`) a real J100/J50 run actually calls along the way - see
`doc/TIER3_EXECUTION_TRACE.md`, which traces `scripts/run_anaFit_J100.sh`
end to end and records one defect (`python/createBinning.py`'s
`IndentationError`) found and fixed while doing so.

## Current status

All twelve chunks (`doc/TIER3_COMPLETION_PLAN.md` Chunks 0-12) are
complete. `python/run_anaFit.py` is reduced to `run_anaFit()` and a thin
`main(args)` plus the `if __name__ == "__main__":` guard - confirmed by
the plan's own AST-based Chunk 8 acceptance check (only `{'main',
'run_anaFit'}` remain at module scope). `plot_edm.py` and
`python/plotPostFit.py` each went from zero/one function to a small set
of independently-tested functions. `plot_postfit.cpp` went from one
257-line function to four, with its public entry point's name and
parameter order unchanged.

Latest full lightweight gate (`python scripts/quality_check.py --mode
full`): 172 passed, 8 deselected, Ruff clean, Black clean (29 files
unchanged), exit code 0. Latest scientific gate (`python -m pytest
tests/test_analysis_workflows_integration.py -m "integration and
requires_root" -v`, rerun against `run_fit.py`/`run_templates.py`'s
fail-fast-ordering and dead-parameter fixes): 1 passed, 2 deselected,
172.97 seconds, exit code 0 - `test_authoritative_j100_j50_workflows_match_frozen_reference`
still matches the frozen `tests/references/analysis_reference.json`
exactly, confirming this entire refactor moved no science.

## Scope

Tier 3 covers, per `doc/TIER3_COMPLETION_PLAN.md` Section 3:

- splitting `python/run_anaFit.py` into seven single-responsibility
  modules plus a thin coordinator (Chunks 1-8);
- splitting `plot_edm.py` into a parse function and a plot function
  (Chunk 9);
- splitting `python/plotPostFit.py` from zero functions into named
  functions plus `main()` (Chunk 10);
- splitting `plot_postfit.cpp`'s single function into smaller free
  functions with its public entry point unchanged (Chunk 11);
- characterization tests against each target's unmodified behavior
  first, human-verified, before any extraction (`doc/TIER3_COMPLETION_PLAN.md`
  Section 5's Step A/Step B model);
- new tests for every newly-introduced function;
- registering every new source and test file this plan required to be
  registered in `scripts/quality_check.py`;
- this document.

It does not cover: CLs processing, signal-analysis changes, different
fit models/inputs/histograms/ranges/tolerances; Tier 4 orchestration;
repository-wide Ruff/Black/C++ formatting; unrelated installer, CI, or
dependency changes; structural extraction of any file other than the
four named above (`python/analysis_reference.py`, `python/repo_utils.py`,
`python/run_injections_anaFit.py`, and every other script under
`python/` remain untouched, as they were before Tier 3); changing the
ROOT/C++ build system or linking any new library; or fixing pre-existing,
unrelated issues noticed along the way (see "Known limitations" below for
the specific ones this plan deliberately left in place).

## Module map: `python/run_anaFit.py` -> 7 modules + coordinator

Every import between these modules, and every import `run_anaFit.py`
makes of them, uses the flat sibling style (`from run_execution import
execute`) - confirmed still correct: `run_anaFit.py` is invoked in
production as a direct executable by absolute path after `cd`-ing to the
repository root, and Python auto-prepends the invoked script's own
directory (`python/`) to `sys.path[0]`.

| Module | Final functions (as implemented) | ROOT-touching? | Import placement |
|---|---|---|---|
| `run_execution.py` | `execute(cmd)`; `execute_required(cmd, description, expected_outputs=())` | No | top-level |
| `run_manifest.py` | `write_analysis_results(folder, p_chi2, masked, provenance)` | No | top-level |
| `run_provenance.py` | `get_repository_root()`; `resolve_analysis_path(path, repository_root=None)`; `calculate_file_sha256(path)`; `build_file_provenance(path, repository_root=None)`; `get_git_revision(repository_path)`; `collect_scientific_runtime()`; `build_analysis_provenance(datafile, datahist, topfile, categoryfile, backgroundfile, signalfile, rangelow, rangehigh, dosignal, dolimit, doprefit, maskthreshold)` | Only `collect_scientific_runtime()` | `import ROOT` deferred inside that one function; `get_repository_root()` calls `repo_utils.find_repo_root()` for the base path, layering the `.git` existence check on top locally (Chunk 3.B) |
| `run_masking.py` | `load_bumphunter_results(results_file)`; `run_bumphunter(postfitfile, folder)`; `should_mask(p_value, threshold)` (new - a shared predicate extracting the masking rule the coordinator previously wrote out inline at two call sites as `p_value > threshold`; implemented as `not (p_value > threshold)`, not the tempting `p_value <= threshold`, after a GitHub Copilot review finding: the two agree for ordinary floats but not for `NaN`, where both `>` and `<=` are False, so only the explicit negation reproduces the original's behavior of sending a `NaN` p-value down the masking branch. Proven by `tests/test_run_masking.py::test_should_mask_treats_nan_p_value_as_requiring_masking`) | No | top-level |
| `run_templates.py` | `replaceinfile(f, old_new_list)`; `_seed_prefit_parameters(datafile, datahist, rangelow, rangehigh, backgroundfile, tmpbackgroundfile)` (private; an unused `nbkg` parameter present through Chunk 12 was dropped later - see "Decisions recorded during extraction" below); `_stage_xml_templates(folder, topfile, categoryfile, backgroundfile, signalfile, signame, wsfile, sigmean, sigwidth, datafile, datahist, rangelow, rangehigh, nbkg, nsig, doprefit, systdict)` (private); `prepare_run_templates(...)` (public entry point, same parameters as `_stage_xml_templates`, thin wrapper) | Only the `doprefit` branch | `from PreFit import PreFitter` deferred inside `_seed_prefit_parameters()` |
| `run_fit.py` | `build_fit_extract(topfile, datafile, datahist, rangelow, rangehigh, wsfile, fitresultfile, poi=None, maskrange=None)` | The whole function | `import ROOT`, `from ExtractPostfitFromWS import PostfitExtractor`, `from ExtractFitParameters import FitParameterExtractor` deferred inside the function, placed immediately before the first `ROOT.TFile(...)` use (after both `execute_required` calls) |
| `run_cli.py` | `build_arg_parser()`; `normalize_signal_name(sigmean, sigwidth, signame)` | No | top-level |
| `run_anaFit.py` (coordinator) | `run_anaFit(datafile, datahist, topfile, categoryfile, wsfile, outputfile, nbkg, nsig, rangelow, rangehigh, signame, backgroundfile=None, signalfile=None, dosignal=False, dolimit=False, sigmean=1000, sigwidth=7.0, maskthreshold=0.01, doprefit=False, folder="run/", systdict=None, covariancedict=None)`; `main(args)` | No (delegates to the modules above) | n/a |

`run_anaFit.py` imports only from the seven modules above (never the
reverse) - confirmed by `grep -rn "run_anaFit" python/run_execution.py
python/run_manifest.py python/run_provenance.py python/run_masking.py
python/run_templates.py python/run_fit.py python/run_cli.py` returning
nothing.

## Module map: plotting layer (`plot_edm.py`, `python/plotPostFit.py`, `plot_postfit.cpp`)

| File | Final functions/structs (as implemented) | Notes |
|---|---|---|
| `plot_edm.py` | `parse_minuit_edm_log(filename) -> (cumulative_x, edm_values, star_indices)`; `plot_minuit_edm_trace(cumulative_x, edm_values, star_indices, outname) -> None`; `plot_minuit_continuous(filename, outname) -> None` (thin orchestrator) | `import matplotlib.pyplot as plt` deferred inside `plot_minuit_edm_trace()`, placed **after** its empty-data early return, so both `parse_minuit_edm_log()` and the empty-data path need zero matplotlib presence. |
| `python/plotPostFit.py` | `PostfitHistograms` (`typing.NamedTuple`: `postfit`, `data`, `chi2`); `parse_args(argv=None) -> argparse.Namespace`; `load_postfit_histograms(input_file) -> (PostfitHistograms, TFile)`; `build_ratio_histogram(data, postfit) -> TH1`; `draw_postfit_canvas(data, postfit, chi2_hist, ratio_hist) -> TCanvas`; `main(argv=None) -> None`; `if __name__ == "__main__": main()` | `import ROOT` is not module-level at all - deferred separately inside `load_postfit_histograms()`, `draw_postfit_canvas()`, and `main()` (a `TYPE_CHECKING`-guarded import satisfies `PostfitHistograms`'s string type hints for static analysis only). `parse_args()` and `build_ratio_histogram()` need no ROOT import at all. |
| `plot_postfit.cpp` | `struct BumpHunterInfo`; `BumpHunterInfo read_bumphunter_results(string const & bh_log_name)`; `struct PostfitHistograms` (ten `TH1D*` fields); `PostfitHistograms load_postfit_histograms(TFile * native, TFile * masked, TFile * native_params, TFile * masked_params)`; `enum class ResidualPanelKind { kParams, kNative, kNativeRebinned }`; `struct ResidualPanelInfo`; `void draw_residual_panel(TCanvas * can, TH1D * first, TH1D * second, bool bump_hunter, BumpHunterInfo const & bh, char const * pars_str, char const * out_file_name, ResidualPanelInfo const & info)`; `void plot_postfit(char const * in_dir, char const * pars_str)` (public entry point - name and parameter order unchanged) | `ResidualPanelKind`/`ResidualPanelInfo` are additions beyond `doc/TIER3_COMPLETION_PLAN.md`'s literal 7-parameter `draw_residual_panel()` table (see "Decisions recorded during extraction" below - the plan's stated signature could not express which panel a call draws or the scalar values it displays). |

## Decisions recorded during extraction

Several chunks explicitly deferred a design decision to be resolved and
documented here. All are now resolved:

**Chunk 5 (`run_templates.py` internal decomposition)**: split into
`_stage_xml_templates()` (path/file-copy/substitution orchestration) and
`_seed_prefit_parameters()` (the `doprefit` branch: `nPars` detection,
`[PARn,lo,hi]` regex parsing, the `PreFitter` call, background-file PAR
substitution) - not moved as one intact function, since the plan required
internal decomposition, not just relocation. The `nPars` detection's
standalone `if "three" in backgroundfile: nPars = 3` followed by a
**separate** `elif` chain for `"four"` through `"ten"` (not one unified
`if/elif` ladder, meaning a filename matching both `"three"` and
`"four"` resolves to `nPars = 4`) was copied exactly, including this
quirk - existing behavior, not something this refactor may "clean up".
Proven by `tests/test_run_templates.py`. `_seed_prefit_parameters()`'s
original signature carried an `nbkg` parameter through Chunk 12, matching
`_stage_xml_templates()`'s own `nbkg` (which the `doprefit` branch's
result then overwrites in its caller). Found later, by direct reading,
to be dead: the parameter is never referenced before being unconditionally
reassigned from the `PreFitter`'s own fitted background count - true of
the original single-scope script's identical local-variable reassignment
too, so this was inert parameter-passing noise introduced by the
extraction, not a behavior difference. Removed; no caller outside
`_stage_xml_templates()` referenced it.

**Chunk 9 (`plot_edm.py`'s `parse_minuit_edm_log()` error handling)**: the
original function caught `FileNotFoundError` and called `sys.exit(1)`
itself. The extracted `parse_minuit_edm_log()` instead lets
`FileNotFoundError` propagate naturally - a pure function should not
terminate the whole process, and doing so would force every caller to
handle `SystemExit` instead of a specific exception type.
`plot_minuit_continuous()` is the thin CLI-facing wrapper that still
prints and calls `sys.exit(1)`, preserving the exact original external
behavior. Proven by
`tests/test_plot_edm.py::test_parse_minuit_edm_log_raises_file_not_found_for_missing_file`
and
`tests/test_plot_edm.py::test_plot_minuit_continuous_exits_with_status_1_for_missing_file`.

**Chunk 10 (`python/plotPostFit.py`'s styling placement and ROOT
lifetime)**: histogram styling (marker/line style) stays inside
`load_postfit_histograms()` rather than a separate
`style_postfit_histograms()` - it is applied unconditionally to every
histogram this function loads, with no call site needing the unstyled
objects, so splitting it would only relocate code without changing what
is tested or reused. `ROOT.gStyle.SetOptStat(0)`/`ROOT.gROOT.SetBatch(True)`
moved from module scope (the original ran them at import time) into the
top of `main()`, preserving their exact ordering relative to everything
else for the one real call path. `load_postfit_histograms()` returns
`(PostfitHistograms, TFile)`, not just the triple the plan's table
listed - verified directly that returning only the triple lets its local
`TFile` be garbage-collected before the caller uses the returned
histograms (`AttributeError: 'CPyCppyy_NoneType' object has no attribute
...`); returning the file too preserves the original single-scope
script's object lifetime. `draw_postfit_canvas()`'s legend needed
`ROOT.SetOwnership(legend, False)` for the same underlying reason (a
locally-constructed cppyy-owned object with no surviving Python
reference was found to be silently dropped from the finished canvas).
Proven by `tests/test_plot_post_fit.py::test_load_postfit_histograms_applies_styling_and_keeps_file_open`
and `tests/test_plot_post_fit.py::test_draw_postfit_canvas_draws_expected_content_in_each_pad`
(the latter was confirmed to fail with the ownership fix reverted).

**Chunk 11 (`plot_postfit.cpp`'s `exit(1)` placement and panel
dispatch)**: the "exit(1) if native histograms missing" check stays
inside `load_postfit_histograms()`, immediately after loading, rather
than moving to the caller - it validates exactly what the function just
built, so `load_postfit_histograms()` never hands back an incomplete
result for a caller to separately re-validate. `draw_residual_panel()`
gained an eighth parameter, `ResidualPanelInfo const & info` (bundling a
`ResidualPanelKind` tag with the four chi2/ndof/p-value scalars a panel
displays) beyond the plan's literal signature - the original loop
dispatched panel-specific content (Y-axis range, draw option, which text
boxes appear) on pointer identity against outer-scope variables the
extracted function has no access to, and on scalar values no struct in
the plan's table carries. The automated test,
`tests/test_plot_postfit_macro.py::test_plot_postfit_macro_produces_nonempty_pdf_for_real_fixture`,
proves the rewritten macro runs to exit `0` and produces a real,
non-empty `post_fit.pdf` - it deliberately does not assert byte-identical
output (same documented policy as `tests/test_plot_post_fit.py`: ROOT's
PDF output is not guaranteed bit-reproducible across environments/fonts).
The byte-identical claim itself - `post_fit.pdf` at exactly 41589 bytes,
matching both Step A's characterization run and the already-committed
reference PDF - was a one-time manual verification performed during this
chunk's development (a direct macro invocation outside pytest), recorded
in `doc/ACTIVITY_LOG.md`'s Chunk 11.B entry; it is not an assertion the
automated test repeats or enforces on every run.

## Test-file map

| Module/file | Test file(s) | Real-ROOT/CVMFS needed? |
|---|---|---|
| `run_execution.py` | `tests/test_run_execution.py` | No |
| `run_manifest.py` | `tests/test_run_manifest.py` | No |
| `run_provenance.py` | `tests/test_run_provenance.py` | Only `collect_scientific_runtime()` tests (stub `sys.modules["ROOT"]`) |
| `run_masking.py` | `tests/test_run_masking.py` | No |
| `run_templates.py` | `tests/test_run_templates.py` | Only `doprefit=True` tests (stub `sys.modules["PreFit"]`) |
| `run_fit.py` | `tests/test_run_fit.py` | No (failure-path tests return before the deferred ROOT/extractor imports) |
| `run_cli.py` | `tests/test_run_cli.py` | No |
| `run_anaFit.py` | `tests/test_run_anaFit.py` | No (stubs `ROOT`/`ExtractPostfitFromWS`/`ExtractFitParameters`/`PreFit` for module loading) |
| `plot_edm.py` | `tests/test_plot_edm.py` | Only tests reaching `plot_minuit_edm_trace()`'s non-empty-data path (stub `sys.modules["matplotlib"]`/`["matplotlib.pyplot"]`) |
| `python/plotPostFit.py` | `tests/test_plot_post_fit.py` | Only `load_postfit_histograms()`/`build_ratio_histogram()`/`draw_postfit_canvas()`/end-to-end tests (real subprocess against sourced `scripts/setup_buildAndFit.sh`); `parse_args()` tests need none |
| `plot_postfit.cpp` | `tests/test_plot_postfit_macro.py` (end-to-end: invokes `plot_postfit.cpp` itself through `root -l -b -q`, not via `tests/root_macros/`) | Yes, always (whole-macro subprocess) |
| `plot_postfit.cpp`'s `read_bumphunter_results()` | `tests/test_read_bumphunter_results.py` (thin wrapper) + `tests/root_macros/test_read_bumphunter_results.cpp` (the actual ROOT-macro unit test) + `tests/root_macros/BHresults_sample.json` (tracked fixture) | Yes, always |

Every real-ROOT/CVMFS-needing test above is marked both
`@pytest.mark.requires_root` and `@pytest.mark.requires_analysis_dependencies`
- the second marker is what keeps a test that sources
`scripts/setup_buildAndFit.sh` out of the ordinary,
CVMFS-less `quality_check.py --mode full` gate (confirmed the hard way:
an earlier commit in this plan marked four such tests `requires_root`
only, which passed on this developer's own CVMFS-mounted host but failed
in GitHub Actions CI, which has no CVMFS mount at all - fixed by adding
the second marker, matching `test_authoritative_setup_provides_scientific_runtime`'s
own pre-existing markers).

`scripts/quality_check.py`'s `python_targets`/`test_targets` cover every
Python production module and test file from this plan, including the two
ROOT-macro wrapper test files
(`tests/test_plot_postfit_macro.py`/`tests/test_read_bumphunter_results.py`).
Registering them buys Ruff/Black coverage only: every test they contain
carries `requires_analysis_dependencies`, so the ordinary gate's pytest
phase (`-m "not requires_analysis_dependencies"`) deselects all of them,
which is why they were originally left unregistered. A GitHub Copilot
review of PR #6 pointed out that leaving them out meant both files
escaped Ruff/Black entirely and that neither ROOT-macro regression test
ran in any CI job at all; both halves of that gap are now closed - see
the plotting-layer gate below, which the hosted scientific workflow runs.

## Gate commands

### Lightweight full gate

```bash
python scripts/quality_check.py --mode full
```

Latest verified result: 172 passed, 8 deselected, Ruff clean, Black clean
(29 files unchanged), exit code 0. (The deselected count rose from 6 to 8,
and the formatted-file count from 27 to 29, when the two ROOT-macro
wrapper test files were registered - see the paragraph above.)

### Plotting-layer real-ROOT gate (not part of the ordinary ­gate above)

```bash
python -m pytest \
  tests/test_plot_post_fit.py \
  tests/test_plot_postfit_macro.py \
  tests/test_read_bumphunter_results.py \
  -m "requires_analysis_dependencies" -v
```

This is the command `.github/workflows/scientific-analysis.yml`'s "Run
plotting-layer real-ROOT regression gates" step runs, after sourcing
`scripts/setup_buildAndFit.sh` on its CVMFS-mounted runner. It selects
exactly the 6 tests the lightweight gate deselects; the other 5
(`parse_args()`'s) need no ROOT and already run there. Dropping the `-m`
filter runs all 11 and is equivalent on a CVMFS host.

Latest verified result on this host: 11 passed, 92.21 seconds, exit code
0 (and 6 selected / 5 deselected under the marker filter above), run
against this host's actual CVMFS/LCG scientific runtime. The hosted
runner's first execution of this step is its own first verification -
`plot_postfit.cpp` had never been compiled in CI before it was added.

### Scientific gate

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v
```

Latest verified result: 1 passed, 2 deselected, 172.97 seconds, exit code
0 (rerun against `run_fit.py`/`run_templates.py`'s fail-fast-ordering and
dead-parameter fixes; see `doc/ACTIVITY_LOG.md`'s corresponding entry).

These gates together cover every module this plan touched, but each
covers a different part, and the scientific gate deliberately does not
cover the plotting layer:

- the lightweight gate runs every extracted Python module's unit tests;
- the scientific gate reruns the real J100/J50 launchers end-to-end,
  exercising `python/run_anaFit.py` (and, transitively, all seven of its
  modules) plus `plot_edm.py`, which `run_fit.py`'s `build_fit_extract()`
  invokes unconditionally. It does **not** exercise
  `python/plotPostFit.py` or `plot_postfit.cpp`: the gate sets
  `ANAFIT_SKIP_PLOTS=1`
  (`tests/test_analysis_workflows_integration.py`), and
  `scripts/run_anaFit_J100.sh`/`run_anaFit_J50.sh` gate both plotting
  invocations on that variable - by design, per Tier 1's "plotting
  separated from scientific acceptance" decision;
- the plotting-layer gate is therefore the only gate covering
  `python/plotPostFit.py` and `plot_postfit.cpp` at all, which is why it
  needed its own CI step.

## Pytest markers

Unchanged from `doc/TIER2_SYSTEM.md`:

- `integration`: executes authoritative workflows
- `requires_root`: needs the configured ROOT/RooFit runtime
- `requires_analysis_dependencies`: needs prepared external checkouts (or,
  as clarified during this plan, any real CVMFS mount at all - see the
  test-file map above)

## Known limitations

- **`plot_postfit.cpp`'s `load_postfit_histograms()` has no dedicated
  unit test.** Per `doc/TIER3_COMPLETION_PLAN.md` Chunk 11's own
  instruction: it is "harder to test in isolation without a real `TFile`",
  and inventing a synthetic ROOT-file-construction fixture for it was
  explicitly scoped out of this chunk. It remains covered only by
  `tests/test_plot_postfit_macro.py`'s end-to-end test.
- **`plot_postfit.cpp`'s `bump_hunter == true` (masked-fit) code path is
  not exercised by any automated test.** No masked-fit fixture
  (`PostFit_*_masked.root`, `FitParameters_*_masked.root`, a real
  `BHresults.json` alongside a masked run) exists in this repository -
  this was already true before this refactor, since the only committed
  J100/J50 fixtures are unmasked. This refactor introduces no new risk
  here: C++ still compiles the `if (bump_hunter) { ... }` branch
  regardless of whether it executes, so `plot_postfit.cpp`'s successful
  compilation is at least a syntax/type-correctness check on that branch,
  even though its runtime behavior is unverified by any test.
- **`run_provenance.py`'s `collect_scientific_runtime()` and
  `run_templates.py`'s `doprefit=True` path are tested only with
  `sys.modules`-stubbed `ROOT`/`PreFit`, never real ones**, matching this
  entire plan's established approach (this repository's own pytest dev
  venv cannot import `ROOT` at all). Their real behavior is exercised
  only by the scientific gate above, end-to-end, not by any unit test
  that isolates them individually.
- **A pre-existing null-pointer landmine in `plot_postfit.cpp`'s
  `load_postfit_histograms()`** (`native_params`/`masked_params` are
  dereferenced unconditionally inside the `if (native)`/`if (masked)`
  guards, with no null check of their own) was deliberately preserved,
  not fixed, per this plan's guardrail against fixing pre-existing,
  unrelated issues found incidentally. If a `PostFit_*` file ever opens
  successfully while its corresponding `FitParameters_*` file does not,
  this will crash. The function's own comment now states this
  paired-pointer requirement explicitly, rather than describing the four
  pointers as independently nullable (GitHub Copilot review, PR #6).
- **The `nPars` detection quirk in `run_templates.py`'s
  `_seed_prefit_parameters()`** (a standalone `if "three" in
  backgroundfile` followed by a separate `elif` chain for `"four"`
  through `"ten"`, meaning a filename matching both `"three"` and
  `"four"` resolves to `nPars = 4`) was deliberately preserved, not
  fixed, for the same reason.
- **This plan's scope is exactly the four files named above** - no other
  script under `python/` (signal injection, limit-setting, toy studies,
  `python/run_injections_anaFit.py`'s own internals, etc.) was touched,
  per Section 3's explicit out-of-scope list.
- **`analysis_results.json`'s `repository_dirty` field was added under
  the existing `schema_version: 2`, not a new version.** This is a
  repeat of an established, already-precedented pattern in this
  repository (an earlier 2026-08-27 schema change made the identical
  choice), not something this plan introduced or is in scope to revisit:
  each such addition ships with a full regeneration of the two tracked
  canonical manifests in the same commit, so no `schema_version: 2`
  manifest with the old field set is left committed anywhere in this
  repository. A manifest written by code *predating* `a83e888` and kept
  outside this repository would fail `_validate_analysis_provenance()`'s
  now-required-key check; that risk is pre-existing to this plan and
  unchanged by it.
- **`pyproject.toml`'s `pythonpath = [".", "python"]` makes some modules
  importable two ways** - `import run_execution` (from `python/`'s own
  auto-prepended directory, mirroring production) and `import
  python.run_execution` (via the `"."` entry) load two distinct module
  objects in the same interpreter, confirmed directly
  (`python.run_execution is not run_execution`). Harmless today - every
  test that monkeypatches a sibling module's attribute does so on the
  same module object it imported the function-under-test through, so no
  test currently straddles both import styles for the same module - but
  latent: a future test that patches `python.run_execution.execute` and
  expects a sibling module reached via the flat style to observe it would
  silently fail. Left as a documented risk rather than changed, since
  removing either `pythonpath` entry would break real, currently-passing
  tests that rely on it (the flat-style entry is required by
  `tests/test_run_anaFit.py`'s own module-loading helper; the dotted
  entry is required by every other test file's `from python.<module>
  import ...` style).

## Authoritative files

Coordinator and its seven modules:

- `python/run_anaFit.py`
- `python/run_execution.py`
- `python/run_manifest.py`
- `python/run_provenance.py`
- `python/run_masking.py`
- `python/run_templates.py`
- `python/run_fit.py`
- `python/run_cli.py`

Plotting layer:

- `plot_edm.py`
- `python/plotPostFit.py`
- `plot_postfit.cpp`

Tests:

- `tests/test_run_anaFit.py`
- `tests/test_run_execution.py`
- `tests/test_run_manifest.py`
- `tests/test_run_provenance.py`
- `tests/test_run_masking.py`
- `tests/test_run_templates.py`
- `tests/test_run_fit.py`
- `tests/test_run_cli.py`
- `tests/test_plot_edm.py`
- `tests/test_plot_post_fit.py`
- `tests/test_plot_postfit_macro.py`
- `tests/test_read_bumphunter_results.py`
- `tests/root_macros/test_read_bumphunter_results.cpp`
- `tests/root_macros/BHresults_sample.json`

Quality gate:

- `scripts/quality_check.py`

## Change control

```bash
git status -sb
git diff --check
git status --short
git diff --stat
```

Append every substantial change to `doc/ACTIVITY_LOG.md` (append-only -
never edit or delete an existing entry).

## Completion definition

Tier 3 is complete when: `python/run_anaFit.py` contains only
`run_anaFit()`/`main()`; `plot_edm.py` and `python/plotPostFit.py` each
expose the named functions in the module maps above; `plot_postfit.cpp`
exposes the four functions/structs above with `plot_postfit()`'s public
signature unchanged; every newly-introduced function has a dedicated test
except the two documented scope boundaries above; every new source and
test file this plan required is registered in `scripts/quality_check.py`;
the lightweight gate, the plotting-layer real-ROOT gates, and the
scientific gate all pass; and this document (`doc/TIER3_SYSTEM.md`)
exists and is current. All of the above are true as of this document's
creation (Chunk 12, following commit `b026efd`).
