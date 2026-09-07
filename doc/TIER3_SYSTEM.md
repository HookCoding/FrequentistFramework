# Tier-3 system: structural refactoring of the coordinator, plotting layer, and hot-path support scripts

This guide describes the Tier-3 structural refactoring: splitting
`python/run_anaFit.py`, the plotting layer, and five additional hot-path
support scripts into focused, individually-tested functions and modules,
with every public entry point's external behavior preserved exactly. It
is modeled on `doc/TIER1_SYSTEM.md` and `doc/TIER2_SYSTEM.md`'s
structure.

## Purpose and audience

Tier 3 is assisted structural refactoring: moving and decomposing
existing code using extract-function/extract-module technique, never
changing what any of it computes. This document is for anyone reading or
extending the seven `run_anaFit.py` modules, the plotting layer, or the
five hot-path support scripts below - it answers "where did function X
go", "what does module Y depend on", and "which test file exercises
this."

For how these modules sit inside a real, complete run, see
`doc/TIER3_EXECUTION_TRACE.md`, which traces `scripts/run_anaFit_J100.sh`
end to end.

## Current status

`python/run_anaFit.py` is reduced to `run_anaFit()` and a thin
`main(args)` plus the `if __name__ == "__main__":` guard - only
`{'main', 'run_anaFit'}` remain at module scope. `plot_edm.py` and
`python/plotPostFit.py` each expose a small set of independently-tested
functions. `plot_postfit.cpp` exposes four free functions/structs, with
its public entry point's name and parameter order unchanged.
`python/createBinning.py`, `python/FindBHWindow.py`,
`python/ExtractFitParameters.py`, `python/ExtractPostfitFromWS.py`, and
`python/PreFit.py` - five additional scripts that sit on the same hot
path outside the coordinator and the plotting layer - are each
decomposed (where their own structure supports it), each has a dedicated
test file exercising its real behavior directly, and each is registered
in `scripts/quality_check.py`.

Latest full lightweight gate (`python scripts/quality_check.py --mode
full`): 202 passed, 20 deselected, Ruff clean, Black clean (39 files
unchanged), exit code 0.

Latest scientific gate (`python -m pytest
tests/test_analysis_workflows_integration.py -m "integration and
requires_root" -v`): 1 passed, 2 deselected, 182.11 seconds, exit code 0
- `test_authoritative_j100_j50_workflows_match_frozen_reference` still
matches the frozen `tests/references/analysis_reference.json` exactly,
confirming this refactor moved no science. This gate's pass does **not**
by itself prove `python/FindBHWindow.py`'s or fully
`python/createBinning.py`'s own correctness, since the committed
J100/J50 fixtures never exercise either file's real branch (unmasked
runs only; both binning fixtures already exist on disk) - see "Gate
commands" below for the gates that do.

## Scope

Tier 3 covers:

- splitting `python/run_anaFit.py` into seven single-responsibility
  modules plus a thin coordinator;
- splitting `plot_edm.py` into a parse function and a plot function;
- splitting `python/plotPostFit.py` from zero functions into named
  functions plus `main()`;
- splitting `plot_postfit.cpp`'s single function into smaller free
  functions with its public entry point unchanged;
- decomposing `python/createBinning.py`, `python/FindBHWindow.py`,
  `python/ExtractFitParameters.py`, `python/ExtractPostfitFromWS.py`,
  and `python/PreFit.py` - five additional hot-path support scripts
  outside the coordinator and plotting layer - to the extent each
  file's own structure supports it;
- characterization tests against each target's unmodified behavior
  first, before any extraction;
- new tests for every newly-introduced function;
- registering every new source and test file in
  `scripts/quality_check.py`;
- this document.

It does not cover: CLs processing, signal-analysis changes, different
fit models/inputs/histograms/ranges/tolerances; Tier 4 orchestration;
repository-wide Ruff/Black/C++ formatting; unrelated installer, CI, or
dependency changes; structural extraction of any file other than the
nine named above - `python/analysis_reference.py`,
`python/run_injections_anaFit.py`, and every other script under
`python/` remain untouched, since none of them sits on the J100/J50
workflow this document describes; changing the ROOT/C++ build system or
linking any new library; or fixing pre-existing, unrelated issues
noticed along the way (see "Known limitations" below for the specific
ones deliberately left in place).

`python/repo_utils.py` is a tenth file on this same workflow - its
`find_repo_root()` is called by `run_provenance.py`'s
`get_repository_root()` on every run - but it needed no work under this
document, because Tier 1/2's own earlier work already brought it to the
same standard this document requires: four small, single-purpose,
individually-tested functions (`find_repo_root()`; `build_repo_snapshot()`;
`write_repo_snapshot(path, snapshot)`; `read_repo_snapshot(path)` - only
the first is on the J100/J50 hot path, the other three support Tier 2's
own repo-snapshot comparison feature), registered in
`scripts/quality_check.py`. See `doc/TIER1_SYSTEM.md`'s own
"Authoritative files" for its ownership.

## Module map: `python/run_anaFit.py` -> 7 modules + coordinator

Every import between these modules, and every import `run_anaFit.py`
makes of them, uses the flat sibling style (`from run_execution import
execute`) - required because `run_anaFit.py` is invoked in production as
a direct executable by absolute path after `cd`-ing to the repository
root, and Python auto-prepends the invoked script's own directory
(`python/`) to `sys.path[0]`.

| Module | Final functions (as implemented) | ROOT-touching? | Import placement |
|---|---|---|---|
| `run_execution.py` | `execute(cmd)`; `execute_required(cmd, description, expected_outputs=())` | No | top-level |
| `run_manifest.py` | `write_analysis_results(folder, p_chi2, masked, provenance)` | No | top-level |
| `run_provenance.py` | `get_repository_root()`; `resolve_analysis_path(path, repository_root=None)`; `calculate_file_sha256(path)`; `build_file_provenance(path, repository_root=None)`; `get_git_revision(repository_path)`; `collect_scientific_runtime()`; `build_analysis_provenance(datafile, datahist, topfile, categoryfile, backgroundfile, signalfile, rangelow, rangehigh, dosignal, dolimit, doprefit, maskthreshold)` | Only `collect_scientific_runtime()` | `import ROOT` deferred inside that one function; `get_repository_root()` calls `repo_utils.find_repo_root()` for the base path, layering the `.git` existence check on top locally |
| `run_masking.py` | `load_bumphunter_results(results_file)`; `run_bumphunter(postfitfile, folder)`; `should_mask(p_value, threshold)` (a shared predicate extracting the masking rule the coordinator previously wrote out inline at two call sites as `p_value > threshold`; implemented as `not (p_value > threshold)`, not `p_value <= threshold` - the two agree for ordinary floats but not for `NaN`, where both `>` and `<=` are False, so only the explicit negation reproduces sending a `NaN` p-value down the masking branch. Proven by `tests/test_run_masking.py::test_should_mask_treats_nan_p_value_as_requiring_masking`) | No | top-level |
| `run_templates.py` | `replaceinfile(f, old_new_list)`; `_seed_prefit_parameters(datafile, datahist, rangelow, rangehigh, backgroundfile, tmpbackgroundfile)` (private); `_stage_xml_templates(folder, topfile, categoryfile, backgroundfile, signalfile, signame, wsfile, sigmean, sigwidth, datafile, datahist, rangelow, rangehigh, nbkg, nsig, doprefit, systdict)` (private); `prepare_run_templates(...)` (public entry point, same parameters as `_stage_xml_templates`, thin wrapper) | Only the `doprefit` branch | `from PreFit import PreFitter` deferred inside `_seed_prefit_parameters()` |
| `run_fit.py` | `build_fit_extract(topfile, datafile, datahist, rangelow, rangehigh, wsfile, fitresultfile, poi=None, maskrange=None)` | The whole function | `import ROOT`, `from ExtractPostfitFromWS import PostfitExtractor`, `from ExtractFitParameters import FitParameterExtractor` deferred inside the function, placed immediately before the first `ROOT.TFile(...)` use (after both `execute_required` calls) |
| `run_cli.py` | `build_arg_parser()`; `normalize_signal_name(sigmean, sigwidth, signame)` | No | top-level |
| `run_anaFit.py` (coordinator) | `run_anaFit(datafile, datahist, topfile, categoryfile, wsfile, outputfile, nbkg, nsig, rangelow, rangehigh, signame, backgroundfile=None, signalfile=None, dosignal=False, dolimit=False, sigmean=1000, sigwidth=7.0, maskthreshold=0.01, doprefit=False, folder="run/", systdict=None, covariancedict=None)`; `main(args)` | No (delegates to the modules above) | n/a |

`run_anaFit.py` imports only from the seven modules above (never the
reverse) - confirmed by `grep -rn "run_anaFit" python/run_execution.py
python/run_manifest.py python/run_provenance.py python/run_masking.py
python/run_templates.py python/run_fit.py python/run_cli.py` returning
nothing.

### Design notes

`run_templates.py` splits into `_stage_xml_templates()`
(path/file-copy/substitution orchestration) and
`_seed_prefit_parameters()` (the `doprefit` branch: `nPars` detection,
`[PARn,lo,hi]` regex parsing, the `PreFitter` call, background-file PAR
substitution) - not moved as one intact function, since internal
decomposition was required, not just relocation. The `nPars` detection's
standalone `if "three" in backgroundfile: nPars = 3` followed by a
**separate** `elif` chain for `"four"` through `"ten"` (not one unified
`if/elif` ladder, meaning a filename matching both `"three"` and
`"four"` resolves to `nPars = 4`) is preserved exactly, including this
quirk - existing behavior, not something this refactor cleans up.
Proven by `tests/test_run_templates.py`.

## Module map: plotting layer (`plot_edm.py`, `python/plotPostFit.py`, `plot_postfit.cpp`)

| File | Final functions/structs (as implemented) | Notes |
|---|---|---|
| `plot_edm.py` | `parse_minuit_edm_log(filename) -> (cumulative_x, edm_values, star_indices)`; `plot_minuit_edm_trace(cumulative_x, edm_values, star_indices, outname) -> None`; `plot_minuit_continuous(filename, outname) -> None` (thin orchestrator) | `import matplotlib.pyplot as plt` deferred inside `plot_minuit_edm_trace()`, placed **after** its empty-data early return, so both `parse_minuit_edm_log()` and the empty-data path need zero matplotlib presence. |
| `python/plotPostFit.py` | `PostfitHistograms` (`typing.NamedTuple`: `postfit`, `data`, `chi2`); `parse_args(argv=None) -> argparse.Namespace`; `load_postfit_histograms(input_file) -> (PostfitHistograms, TFile)`; `build_ratio_histogram(data, postfit) -> TH1`; `draw_postfit_canvas(data, postfit, chi2_hist, ratio_hist) -> TCanvas`; `main(argv=None) -> None`; `if __name__ == "__main__": main()` | `import ROOT` is not module-level at all - deferred separately inside `load_postfit_histograms()`, `draw_postfit_canvas()`, and `main()` (a `TYPE_CHECKING`-guarded import satisfies `PostfitHistograms`'s string type hints for static analysis only). `parse_args()` and `build_ratio_histogram()` need no ROOT import at all. |
| `plot_postfit.cpp` | `struct BumpHunterInfo`; `BumpHunterInfo read_bumphunter_results(string const & bh_log_name)`; `struct PostfitHistograms` (ten `TH1D*` fields); `PostfitHistograms load_postfit_histograms(TFile * native, TFile * masked, TFile * native_params, TFile * masked_params)`; `enum class ResidualPanelKind { kParams, kNative, kNativeRebinned }`; `struct ResidualPanelInfo`; `void draw_residual_panel(TCanvas * can, TH1D * first, TH1D * second, bool bump_hunter, BumpHunterInfo const & bh, char const * pars_str, char const * out_file_name, ResidualPanelInfo const & info)`; `void plot_postfit(char const * in_dir, char const * pars_str)` (public entry point - name and parameter order unchanged) | `ResidualPanelKind`/`ResidualPanelInfo` bundle a panel-kind tag with the four chi2/ndof/p-value scalars a panel displays - see "Design notes" below. |

### Design notes

`plot_edm.py`'s `parse_minuit_edm_log()` lets `FileNotFoundError`
propagate naturally rather than catching it and calling `sys.exit(1)`
itself - a pure function should not terminate the whole process, and
doing so would force every caller to handle `SystemExit` instead of a
specific exception type. `plot_minuit_continuous()` is the thin
CLI-facing wrapper that still prints and calls `sys.exit(1)`, preserving
the original external behavior. Proven by
`tests/test_plot_edm.py::test_parse_minuit_edm_log_raises_file_not_found_for_missing_file`
and
`tests/test_plot_edm.py::test_plot_minuit_continuous_exits_with_status_1_for_missing_file`.

`python/plotPostFit.py`'s histogram styling (marker/line style) stays
inside `load_postfit_histograms()` rather than a separate
`style_postfit_histograms()` - it is applied unconditionally to every
histogram this function loads, with no call site needing the unstyled
objects, so splitting it would only relocate code without changing what
is tested or reused. `ROOT.gStyle.SetOptStat(0)`/
`ROOT.gROOT.SetBatch(True)` moved from module scope into the top of
`main()`, preserving their exact ordering relative to everything else
for the one real call path. `load_postfit_histograms()` returns
`(PostfitHistograms, TFile)`, not just the triple - returning only the
triple lets its local `TFile` be garbage-collected before the caller
uses the returned histograms; returning the file too preserves the
original object lifetime. `draw_postfit_canvas()`'s legend needs
`ROOT.SetOwnership(legend, False)` for the same underlying reason (a
locally-constructed cppyy-owned object with no surviving Python
reference is otherwise silently dropped from the finished canvas).
Proven by
`tests/test_plot_post_fit.py::test_load_postfit_histograms_applies_styling_and_keeps_file_open`
and
`tests/test_plot_post_fit.py::test_draw_postfit_canvas_draws_expected_content_in_each_pad`.

`plot_postfit.cpp`'s "exit(1) if native histograms missing" check stays
inside `load_postfit_histograms()`, immediately after loading, rather
than moving to the caller - it validates exactly what the function just
built, so `load_postfit_histograms()` never hands back an incomplete
result for a caller to separately re-validate. `draw_residual_panel()`
takes an eighth parameter, `ResidualPanelInfo const & info` (bundling a
`ResidualPanelKind` tag with the four chi2/ndof/p-value scalars a panel
displays) - the original inline loop dispatched panel-specific content
(Y-axis range, draw option, which text boxes appear) on pointer identity
against outer-scope variables the extracted function has no access to,
and on scalar values no simpler struct carries. The automated test,
`tests/test_plot_postfit_macro.py::test_plot_postfit_macro_produces_nonempty_pdf_for_real_fixture`,
proves the macro runs to exit `0` and produces a real, non-empty
`post_fit.pdf` - it deliberately does not assert byte-identical output
(ROOT's PDF output is not guaranteed bit-reproducible across
environments/fonts).

## Module map: hot-path support scripts

`doc/TIER3_EXECUTION_TRACE.md` traces a real
`scripts/run_anaFit_J100.sh` run end to end and finds these five files
sitting directly on that hot path, outside the seven-module coordinator
and the plotting layer above. All five are ROOT- or heavy-dependency-
coupled end to end, or nearly so, so the decomposition value varies per
file - a uniform split was not forced where a file's own structure did
not support one.

| File | Final functions/methods (as implemented) | Notes |
|---|---|---|
| `python/createBinning.py` | `parse_args(argv=None)`; `load_resolution_fit(input_path=...)`; `resolve_bin_edges(reso_fit, rangelow, rangehigh)`; `build_binning_histogram(bin_edges)`; `main(argv=None)`, plus an `if __name__ == "__main__":` guard | `import ROOT` deferred inside `load_resolution_fit()`/`build_binning_histogram()`/`main()`; `parse_args()`/`resolve_bin_edges()` are ROOT-free at both module and call scope - `resolve_bin_edges()` is the one fragment testable with zero ROOT, needing only an object exposing `.Eval(x)`. |
| `python/FindBHWindow.py` | `NpEncoder`; `parse_args(argv=None)`; `load_histograms(input_file, bkghist, datahist)`; `crop_data_to_background_range(bins, bins_data, data)`; `run_bump_hunter(data, bkg, bins)`; `compute_mask_window(state, bins, firstbindata, use_bin_numbers)`; `save_bump_plots(hunter, data, bkg)`; `write_mask_window_json(out_dict, outputjson)`; `main(argv=None)` (the file's only real entry point - always invoked as a whole subprocess under its own dedicated interpreter, never imported) | `numpy` stays at module scope; `uproot` deferred inside `load_histograms()`; `matplotlib`/`pyBumpHunter` deferred inside `run_bump_hunter()`/`save_bump_plots()`. `crop_data_to_background_range()` is the one fragment testable with only a `numpy` stub, once given plain arrays; `compute_mask_window()` keeps the `--usebinnumbers` vs. default formulas as two distinct, separately-tested branches. |
| `python/ExtractFitParameters.py` | `FitParameterExtractor.__init__(self, wsfile)`; `.Extract()`; `.GetH1Params()`; `.GetH2Cov()`; `.GetH2Cor()`; `.GetNsig()`; `.GetNsigErr()`; `.WriteRoot(outfile)`; `main(args)` | No decomposition of `Extract()`/`WriteRoot()`/the 5 accessors: `Extract()` (42 lines) is one cohesive block, and forcing a split would relocate, not reduce, its complexity. |
| `python/ExtractPostfitFromWS.py` | Free functions `getNPars(pdf, obs, exclSyst)`/`expHist(h)`/`getChi2(extractor, channelname, npars, useSumW2=False)` (`getChi2`'s external mutation of the `extractor` it's passed is preserved exactly); `PostfitExtractor.__init__`; `._open_workspace_and_data()`; `._build_channel_postfit_histogram(pdfi, x, channelname, npars, data)`; `._build_bkgonly_variant(w, channelname, x, hpdf, nBins, binEdges, npars)`; `._apply_external_rebinning(channelname, channelname_bkg, npars)`; `.Extract()` (orchestrator); `.WriteRoot(outfile, dirPerCategory=False)`; the 8 accessors (`GetChi2`/`GetNbins`/`GetNpars`/`GetNdof`/`GetPval`/`GetH1Chi2`/`GetH1Postfit`/`GetH1Residuals`); `.GetCategories()`; `main(args)` | `Extract()` (137 lines, the largest method across all nine files) decomposes into the four private helpers; `WriteRoot()`/the 8 accessors/`GetCategories()` stay undecomposed one-liners. |
| `python/PreFit.py` | `PreFitter.__init__`; `.RandomizeParameters(function)`; `._build_candidate_functions()`; `._select_best_parameter_sets(fitFunction, integral, score_fn, nRetries1, nRetries2)`; `.Fit()` (orchestrator); `main(args)` | `_select_best_parameter_sets()` takes a `score_fn` callable (`Fit()` passes a `lambda fn: h.Chisquare(fn)` closure) instead of the data histogram itself, so it never touches the data histogram directly - it still calls `ROOT.TStopwatch`/`ROOT.TMath` for timing and the `Exp`/`Log` initial-guess math, which is what makes `tests/test_pre_fit.py` a histogram-independent, ROOT-stubbed unit test of this file's own logic rather than a fully ROOT-free one. |

All five files do have a real, `requires_analysis_dependencies`-marked
subprocess/fixture tier. Four of the five also carry `requires_root` on
those tests; `tests/test_find_bh_window.py` does not, because
`FindBHWindow.py` never imports ROOT (it uses `uproot`/`pyBumpHunter`
under its own dedicated interpreter), so its marked test deliberately
carries `requires_analysis_dependencies` alone.

Their *fast* tiers, by contrast, are not all the same shape, and one
file has none at all: `createBinning.py`'s fast
fragment (`resolve_bin_edges()`) is genuinely ROOT-free at call scope,
needing no stub; `FindBHWindow.py`'s fast fragments are `numpy`-only,
reached by deferring every heavy import rather than by stubbing
`sys.modules["ROOT"]`; `ExtractFitParameters.py` and `PreFit.py` each
add a `sys.modules["ROOT"]`-stubbed fast tier; `ExtractPostfitFromWS.py`
has no fast tier - its decomposition only produced private helpers that
still need a real workspace/histogram, so every one of its tests is the
real, marked tier.

### Design notes

`ExtractFitParameters.FitParameterExtractor.__init__`'s `wsfile`
parameter and `ExtractPostfitFromWS.PostfitExtractor.__init__`'s
same-named parameter both receive the fit-result file in production
(`run_fit.py`'s `FitParameterExtractor(wsfile=fitresultfile)` and
`PostfitExtractor(wsfile=fitresultfile, ...)` respectively) - never the
RooFit workspace file either name suggests. Documented, not renamed; see
"Known limitations" below.

`ExtractPostfitFromWS.py`'s `try: hpdf.Scale(...) except: pass` blocks
(both the main-channel and bkgonly-channel `Scale` calls) keep their
bare `except:` exactly as written (with `# noqa: E722`) rather than
narrowing to `except Exception:` - a bare `except` also catches
`SystemExit`/`KeyboardInterrupt`/`GeneratorExit`, and preserving that is
a deliberate choice, not an oversight. `_build_bkgonly_variant`'s
`pdf_bkg_unscaled`/`yield_bkg` locals (assigned via `w.obj(...)`, never
read) are likewise preserved, with `# noqa: F841` - a `RooWorkspace.obj()`
call may have a caching/registration side effect beyond its return
value, so removing an unread-but-possibly-side-effecting call is not a
safe simplification.

`PreFit.py`'s `parRangeLow`/`parRangeHigh` default to 7-element lists
while `nPars` can be requested up to 10; see "Known limitations" below.

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
| `python/createBinning.py` | `tests/test_create_binning.py` | Only `load_resolution_fit()`/the end-to-end script tests (real ROOT, some via a synthetic on-the-fly fixture); `parse_args()`/`resolve_bin_edges()` tests need none |
| `python/FindBHWindow.py` | `tests/test_find_bh_window.py` | Only the end-to-end script test (`requires_analysis_dependencies` alone - this script never imports ROOT); `NpEncoder`/`parse_args()`/`crop_data_to_background_range()`/`compute_mask_window()`/`write_mask_window_json()` tests need none (numpy-stub or real numpy) |
| `python/ExtractFitParameters.py` | `tests/test_extract_fit_parameters.py` | Only the real-fixture `Extract()`/accessors/`WriteRoot()` test (real-ROOT subprocess snippet against the committed J100 `FitResult_*.root` fixture); the two `GetNsig()`/`GetNsigErr()` falsy-refire tests stub `sys.modules["ROOT"]` |
| `python/ExtractPostfitFromWS.py` | `tests/test_extract_postfit_from_ws.py` | Yes, always - every test is a real-ROOT subprocess snippet against committed J100 fixtures (no ROOT-free fragment exists in this file) |
| `python/PreFit.py` | `tests/test_pre_fit.py` | Only the two `Fit()` tests (real-ROOT subprocess snippet against the committed J100 `mjj_spectra_J100_dataAll.root` fixture); `_build_candidate_functions()`/`_select_best_parameter_sets()` tests stub `sys.modules["ROOT"]` |
| `python/repo_utils.py` | `tests/test_repo_utils.py` | No for `find_repo_root()`/`build_repo_snapshot()`/`write_repo_snapshot()`/`read_repo_snapshot()`'s own tests (pure `pathlib`/`json`); two other, unrelated tests in this same file (external-submodule-revision checks, Tier 1/2's own installation policy) are separately marked `requires_analysis_dependencies` |

Every real-ROOT/CVMFS-needing test above is marked
`@pytest.mark.requires_analysis_dependencies`, and every one of them
that actually needs ROOT is additionally marked
`@pytest.mark.requires_root`. The single exception to the second marker
is `tests/test_find_bh_window.py`'s end-to-end test, which needs CVMFS
but not ROOT (`FindBHWindow.py` imports `uproot`/`pyBumpHunter`, never
ROOT) and so carries `requires_analysis_dependencies` alone - which is
exactly why that marker, not `requires_root`, is the one every such
test must carry: `requires_analysis_dependencies` is what keeps a test
that sources `scripts/setup_buildAndFit.sh` out of the ordinary,
CVMFS-less `quality_check.py --mode full` gate (`requires_root` alone
passes on a CVMFS-mounted host but fails in GitHub Actions CI, which
has no CVMFS mount at all).

`scripts/quality_check.py`'s `python_targets`/`test_targets` cover every
Python production module and test file in this document, including the
two ROOT-macro wrapper test files
(`tests/test_plot_postfit_macro.py`/`tests/test_read_bumphunter_results.py`).
Registering them buys Ruff/Black coverage only: every test they contain
carries `requires_analysis_dependencies`, so the ordinary gate's pytest
phase (`-m "not requires_analysis_dependencies"`) deselects all of them
- see the plotting-layer gate below, which the hosted scientific
workflow runs instead.

## Gate commands

### Run every gate in one command

```bash
bash scripts/run_all_gates.sh
```

Runs all five gates in sequence - the lightweight gate, the
prepared-dependency gate, the scientific runtime-readiness gate, the
scientific gate, and the plotting-layer real-ROOT gate - printing a
PASSED/FAILED line for each and exiting non-zero if any failed. Three
of the five have their own sections below; the prepared-dependency and
scientific runtime-readiness gates belong to Tiers 2 and 1 and are
documented in [Tier 1 system](TIER1_SYSTEM.md)'s own Gate commands
instead. The first two need no ROOT and always run; the last three
require a real ROOT runtime here (`scripts/setup_buildAndFit.sh`
succeeds), and the script fails loudly rather than skipping when that
isn't available, since its purpose is to run everything.
`tests/test_repo_utils.py::test_run_all_gates_script_covers_every_requires_analysis_dependencies_test_file`
and
`tests/test_repo_utils.py::test_ci_scientific_workflow_covers_every_requires_analysis_dependencies_test_file`
pin that this script and the CI workflow below both stay in sync with
every `requires_analysis_dependencies` test file that exists - the
class of gap that let `tests/test_pre_fit.py`'s own real-ROOT tests run
in no CI job for a time.

### Lightweight full gate

```bash
python scripts/quality_check.py --mode full
```

Latest verified result: 202 passed, 20 deselected, Ruff clean, Black
clean (39 files unchanged), exit code 0.

### Plotting-layer real-ROOT gate (not part of the ordinary gate above)

```bash
python -m pytest \
  tests/test_plot_post_fit.py \
  tests/test_plot_postfit_macro.py \
  tests/test_read_bumphunter_results.py \
  tests/test_create_binning.py \
  tests/test_extract_fit_parameters.py \
  tests/test_extract_postfit_from_ws.py \
  tests/test_find_bh_window.py \
  tests/test_pre_fit.py \
  -m "requires_analysis_dependencies" -v
```

This is the command `.github/workflows/scientific-analysis.yml`'s "Run
plotting-layer real-ROOT regression gates" step runs, after sourcing
`scripts/setup_buildAndFit.sh` on its CVMFS-mounted runner. It selects
exactly the 18 tests across these 8 files that the lightweight gate
deselects; every other test in them (`parse_args()`'s and similar
stub-friendly tests) needs no ROOT and already runs there. Dropping the
`-m` filter runs all 48 and is equivalent on a CVMFS host. Every test
file with a `requires_analysis_dependencies` test must be added to this
command (and to the CI workflow step it mirrors) in the same commit that
introduces it - this list has been found out of date more than once
before.

Latest verified result: 48 passed, 51.20 seconds, exit code 0 (and 18
selected / 29 deselected under the marker filter above), run against a
real CVMFS/LCG scientific runtime.

### Scientific gate

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v
```

Latest verified result: 1 passed, 2 deselected, 182.11 seconds, exit
code 0.

### FindBHWindow.py manual reproduction command (not a separate gate)

```bash
repo_dir="$PWD"
source scripts/setup_buildAndFit.sh
export PYTHONPATH="$repo_dir/pyBumpHunter:$PYTHONPATH"
python3 python/FindBHWindow.py \
  --inputfile <a real PostFit_*.root> \
  --bkghist Run3TLA_rebinned/postfit --datahist Run3TLA_rebinned/data \
  --outputjson <tmp path>
```

The standard scientific gate above never exercises `FindBHWindow.py`'s
real behavior at all: both committed J100/J50 fixtures are unmasked, so
`run_masking.run_bumphunter()` (the only production call site) is never
invoked in that gate - running it there only proves `should_mask()`/
`run_bumphunter()` are still correctly *not* invoked on the unmasked
path. The automated proof of `FindBHWindow.py`'s own correctness is
`tests/test_find_bh_window.py`'s marked end-to-end test, which the
plotting-layer gate above runs (and which
`.github/workflows/scientific-analysis.yml` runs in CI): it invokes the
script as a real subprocess against the committed J100 PostFit fixture
and asserts the resulting `MaskMin`/`MaskMax`/`BlindRange` and both
output PNGs. The command above is the hand-runnable equivalent of that
test, for debugging - not a separate gate, and
`scripts/run_all_gates.sh` deliberately does not run it as one, since
doing so would duplicate that test exactly while asserting only an
exit status. Both use the same working ambient-
interpreter + `PYTHONPATH` combination - `pyBumpHunter/pyBH_env` is
confirmed broken in this environment (missing `uproot` and `matplotlib`
in its own site-packages) - not the broken dedicated venv this
repository's production code (`run_masking.run_bumphunter()`) still
invokes unchanged. `createBinning.py`'s own equivalent real-fixture
proof is a plain pytest test (`tests/test_create_binning.py`'s
`requires_root`+`requires_analysis_dependencies` tests, including one
against a synthetic on-the-fly fixture), not a separate dedicated-
interpreter command, since `createBinning.py` needs no interpreter or
`PYTHONPATH` beyond what `scripts/setup_buildAndFit.sh` already
provides.

These gates together cover every module this document describes, but
each covers a different part, and the scientific gate deliberately does
not cover the plotting layer:

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
  `python/plotPostFit.py` and `plot_postfit.cpp` at all;
- the scientific gate's pass likewise does **not** by itself prove
  `python/FindBHWindow.py`'s or fully `python/createBinning.py`'s own
  correctness, for the identical reason (both files' real branches sit
  behind the same unmasked-fixture / already-exists-on-disk conditions)
  - `tests/test_find_bh_window.py`'s and
  `tests/test_create_binning.py`'s own marked real-fixture tests, both
  run by the plotting-layer gate, are what actually prove those two
  files' behavior.

## Pytest markers

Unchanged from `doc/TIER2_SYSTEM.md`:

- `integration`: executes authoritative workflows
- `requires_root`: needs the configured ROOT/RooFit runtime
- `requires_analysis_dependencies`: needs prepared external checkouts (or
  any real CVMFS mount at all - see the test-file map above)

## Known limitations

- **`plot_postfit.cpp`'s `load_postfit_histograms()` has no dedicated
  unit test.** It is harder to test in isolation without a real `TFile`,
  and inventing a synthetic ROOT-file-construction fixture for it was
  scoped out. It remains covered only by
  `tests/test_plot_postfit_macro.py`'s end-to-end test.
- **`plot_postfit.cpp`'s `bump_hunter == true` (masked-fit) code path is
  not exercised by any automated test.** No masked-fit fixture
  (`PostFit_*_masked.root`, `FitParameters_*_masked.root`, a real
  `BHresults.json` alongside a masked run) exists in this repository,
  since the only committed J100/J50 fixtures are unmasked. C++ still
  compiles the `if (bump_hunter) { ... }` branch regardless of whether it
  executes, so `plot_postfit.cpp`'s successful compilation is at least a
  syntax/type-correctness check on that branch, even though its runtime
  behavior is unverified by any test.
- **`FindBHWindow.py`'s masked-fit code path has the same gate-coverage
  gap.** The standard scientific gate's committed J100/J50 runs are
  unmasked (no `BHresults.json` in either fixture directory), so it
  never exercises this file's real behavior at all - running it there
  only proves `should_mask()`/`run_bumphunter()` are still correctly
  *not* invoked on the unmasked path. `tests/test_find_bh_window.py`'s
  marked end-to-end test - run by the plotting-layer gate above, and by
  CI - is the only real proof of this file's own correctness, and even
  it uses the ambient interpreter rather than the broken
  `pyBumpHunter/pyBH_env` one production actually invokes.
- **`run_provenance.py`'s `collect_scientific_runtime()` and
  `run_templates.py`'s `doprefit=True` path are tested only with
  `sys.modules`-stubbed `ROOT`/`PreFit`, never real ones** (this
  repository's own pytest dev venv cannot import `ROOT` at all). Their
  real behavior is exercised only by the scientific gate above,
  end-to-end, not by any unit test that isolates them individually.
- **A pre-existing null-pointer landmine in `plot_postfit.cpp`'s
  `load_postfit_histograms()`** (`native_params`/`masked_params` are
  dereferenced unconditionally inside the `if (native)`/`if (masked)`
  guards, with no null check of their own) is deliberately preserved,
  not fixed. If a `PostFit_*` file ever opens successfully while its
  corresponding `FitParameters_*` file does not, this will crash. The
  function's own comment states this paired-pointer requirement
  explicitly.
- **The `nPars` detection quirk in `run_templates.py`'s
  `_seed_prefit_parameters()`** (a standalone `if "three" in
  backgroundfile` followed by a separate `elif` chain for `"four"`
  through `"ten"`, meaning a filename matching both `"three"` and
  `"four"` resolves to `nPars = 4`) is deliberately preserved, not
  fixed.
- **This document's scope is exactly the nine files named above, plus
  `python/repo_utils.py`'s pre-existing standard** (see "Scope" above)
  - no other script under `python/` (signal injection, limit-setting,
  toy studies, `python/run_injections_anaFit.py`'s own internals, etc.)
  sits on the J100/J50 workflow this document describes.
- **`ExtractPostfitFromWS.py` has one dormant bug still preserved and
  documented, not fixed.** `_build_bkgonly_variant`'s `try/except` block
  calls `hpdf.Scale(...)` - the **main** channel's already-fully-consumed
  histogram - not `hpdf_bkg.Scale(...)` as the adjacent commented-out
  line suggests was intended, so `hpdf_bkg` is in practice never
  actually scaled by `expectedEvents_bkg`. A code comment at the call
  site notes this.
- **The `wsfile` parameter name means two different things across the
  two extractor classes' shared naming, and both mean the "wrong" thing
  relative to the name.** `ExtractFitParameters.FitParameterExtractor.__init__`'s
  `wsfile` and `ExtractPostfitFromWS.PostfitExtractor.__init__`'s
  `wsfile` both receive the fit-result file in production
  (`run_fit.py`'s `FitParameterExtractor(wsfile=fitresultfile)` and
  `PostfitExtractor(wsfile=fitresultfile, ...)` respectively) - never the
  RooFit workspace file either name suggests. Documented, not renamed.
- **`PreFit.py`'s `parRangeLow`/`parRangeHigh` default to 7-element lists
  while `nPars` can be requested up to 10.** Constructing a `PreFitter`
  with `nPars > 7` under the default ranges raises `IndexError` partway
  through `Fit()`'s first `RandomizeParameters()` call - characterized,
  not fixed, by
  `tests/test_pre_fit.py::test_fit_raises_indexerror_for_npars_above_seven_with_default_ranges`.
  `run_templates.py`'s own `PreFitter` call site already works around
  this by building its own longer `parRangeLow`/`parRangeHigh` lists
  whenever `nPars > 7`.
- **`createBinning.py`'s call site does not check `execute()`'s return
  code.** `run_fit.py`'s `build_fit_extract()` calls
  `execute(f"python3 python/createBinning.py ...")`, not
  `execute_required(...)` - if the script fails, the run silently
  continues with a missing rebin file and fails later inside
  `PostfitExtractor` with a more confusing, unrelated ROOT-level error.
  See `doc/TIER3_EXECUTION_TRACE.md` Section 5 for the full history;
  deliberately left unfixed here, since changing `run_fit.py`'s own call
  site is out of scope.
- **`FindBHWindow.py`'s fast test tier needs a `numpy` `ModuleType`
  stub.** This repository's own pytest dev venv has no `numpy` installed
  at all, confirmed directly, so `NpEncoder.default()`'s
  `isinstance(obj, (np.integer, np.floating, np.ndarray))` checks need a
  fake `numpy` module exposing real, instantiable
  `integer`/`floating`/`ndarray` classes to even import the file. Only
  `NpEncoder`/`crop_data_to_background_range()`/`compute_mask_window()`
  need it.
- **`analysis_results.json`'s `repository_dirty` field was added under
  the existing `schema_version: 2`, not a new version.** This repeats an
  already-precedented pattern in this repository: each such addition
  ships with a full regeneration of the two tracked canonical manifests
  in the same commit, so no `schema_version: 2` manifest with the old
  field set is left committed anywhere in this repository. A manifest
  written by older code and kept outside this repository would fail
  `_validate_analysis_provenance()`'s now-required-key check; that risk
  is pre-existing and unrelated to this refactor.
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
  expects a sibling module reached via the flat style to observe it
  would silently fail. Left as a documented risk rather than changed,
  since removing either `pythonpath` entry would break real,
  currently-passing tests that rely on it (the flat-style entry is
  required by `tests/test_run_anaFit.py`'s own module-loading helper;
  the dotted entry is required by every other test file's `from
  python.<module> import ...` style).

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

Hot-path support scripts:

- `python/createBinning.py`
- `python/FindBHWindow.py`
- `python/ExtractFitParameters.py`
- `python/ExtractPostfitFromWS.py`
- `python/PreFit.py`

Also on the same hot path, owned by `doc/TIER1_SYSTEM.md` (imported by
`run_provenance.py`, not decomposed by this document - see "Scope"
above):

- `python/repo_utils.py`

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
- `tests/test_create_binning.py`
- `tests/test_find_bh_window.py`
- `tests/test_extract_fit_parameters.py`
- `tests/test_extract_postfit_from_ws.py`
- `tests/test_pre_fit.py`

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
signature unchanged; `python/createBinning.py`, `python/FindBHWindow.py`,
`python/ExtractFitParameters.py`, `python/ExtractPostfitFromWS.py`, and
`python/PreFit.py` each match their module-map entry above; every
newly-introduced function has a dedicated test except the documented
scope boundaries above; every new source and test file is registered in
`scripts/quality_check.py`; the lightweight gate, the plotting-layer
real-ROOT gate, and the scientific gate all pass - **except** that the
scientific gate's pass does not by itself prove
`python/FindBHWindow.py`'s or fully
`python/createBinning.py`'s own correctness (both files' real branches
sit behind unmasked-fixture / already-exists-on-disk conditions the
committed J100/J50 workflows never trigger);
`tests/test_find_bh_window.py`'s and `tests/test_create_binning.py`'s
own marked real-fixture tests, both run by the plotting-layer gate, are
what actually prove those two files' behavior; and this document exists
and is current.
