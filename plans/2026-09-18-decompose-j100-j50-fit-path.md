# Decompose the J100/J50 fit path into tested single-purpose functions

Written 2026-09-18 for branch `claude-skills-2`, before any of the work it describes.

## Context

The J100 and J50 analyses run through nine files totalling ~2 400 lines, and the work is
concentrated in a handful of very large functions: `run_anaFit()` is 338 lines with 25
parameters, `PostfitExtractor.Extract()` is 137, `PreFitter.Fit()` is 131, `getChi2()` is 86,
`plot_postfit()` is 257, and `python/plotPostFit.py` has no functions at all — 94 lines of
module-level script. Inside these, unrelated kinds of work are welded together: `getChi2` opens
nothing but computes a chi2, builds a summary histogram, prints six lines and writes seven
dictionaries onto an object passed in as an argument.

Nothing on this path has a unit test. The only safety net is `tests/repro.py`, an end-to-end
reproducibility lock over exactly these two analyses that takes 3.5–6 minutes per run and compares
plot *filenames*, never plot contents. `tests/repro.py selfcheck` tests the comparator, not the
framework.

The goal is that every function on this path does one kind of work and has a test pinning its
inputs against its outputs, so a future developer changing the code gets told immediately if the
underlying numbers moved.

### What this buys, and what it does not

Worth stating plainly, because the distinction governs how the plan is sequenced:

A green per-function suite proves each extracted function computes, in isolation, the same
numbers the current code computes for the inputs we captured. It does not prove the pipeline
still produces the same physics. Every serious hazard here is a *composition* hazard, not a
*function* hazard — `getChi2` is called four times in a fixed order and mutates state on its
caller; `self.datafirstbin` is reassigned mid-loop so a second call to `Extract` computes
different bin edges; `PreFitter.__init__` changes process-global ROOT state; and nine live ROOT
objects are owned by a `TFile` closed on the last line of `Extract`. No single-function test can
observe any of those. `tests/repro.py check` remains the only thing that can, which is why it
runs at **every** section boundary rather than at the end.

### Standing rules for this work

1. **The refactor moves zero physics numbers.** `repro.py check` must be green at every
   boundary. A red check means I broke something — never "I fixed something".
2. **No baseline is re-cut anywhere in this plan.** If a change would require one, it is not a
   refactor and it stops for a separate decision.
3. **Defects found are recorded, not fixed.** Each gets a `KNOWN_ISSUES.md` entry and a test
   pinning *today's* behaviour, however wrong that behaviour looks.
4. **Extracted helpers are private** (`_name`) unless something outside the module already calls
   them. Public signatures, return values and printed output are preserved exactly.
5. Sections are implemented one at a time, documentation written in the same section as its
   code, and nothing is committed until reviewed — per `CLAUDE.md`.

### Conventions used below

**Original code** gives the line range in the file as it stands today. **Inputs** and **Outputs**
name each value and say what it carries. Values that are currently read off `self` are listed as
inputs, because an extracted helper takes them as arguments rather than reaching for them.
**Test** lists what the test must establish; where a test is not worth writing, that is said
instead of padding the list.

## The three preserved defects

Filed in §1 before any code moves, then pinned by tests, then left alone:

| Where | What | Why it is not fixed here |
|---|---|---|
| `python/ExtractPostfitFromWS.py:270` | Scales `hpdf`, where the surrounding block means `hpdf_bkg`; `hpdf_bkg` is then read unscaled at :284 | Collapsing the duplicated blocks would silently correct it and move the background-only p-value |
| `python/PreFit.py:110-119` | Ten literal `SetParameter(0..9, …)` calls overwrite every value `RandomizeParameters()` just set, so the sampling loop evaluates the same chi2 on every iteration | Changing it changes the prefit starting parameters of every fit in the repository |
| `python/ExtractPostfitFromWS.py:314,322` | `Extract()` reassigns the constructor argument `self.datafirstbin`, so a second call computes different bin edges | Genuine refactor blocker — handled in §6 by using a local instead, which is behaviour-preserving for the single call the drivers make |

A fourth, already recorded as issue 41, is pinned rather than fixed: `getChi2` skips any bin with
`valueErrorData <= 0` or `postFitValue <= 0` from the chi2 **and** from the bin count **and** from
the residual histogram, silently.

---

## §1 — Test harness and a fast post-fit regression test

No decomposition in this section. It builds the thing every later section is verified with.

`run/run_481_3000_sixPar/FitResult_anaFit_sixPar_bkgOnly.root` (40 KB) holds both `combWS` and
`fitResult`; `PostFit_anaFit_sixPar_bkgOnly.root` (133 KB) holds `data`, `postfit`, `residuals`
and `chi2` per channel directory — the inputs *and* the expected outputs of every downstream
target, already on disk. Copy them; do not regenerate them.

- **`tests/conftest.py`** — inserts `python/` on `sys.path` (that directory is not a package and
  must not become one). Docstring records that the suite runs only after `. setup.sh`: system
  ROOT 6.40 rejects `from ROOT import *`, which `ExtractPostfitFromWS.py:4` and
  `ExtractFitParameters.py:4` both use, so the LCG_102a ROOT 6.26 is not optional.
- **`tests/fixtures/`** — the two files above, the J50 masked pair (the only recorded run where
  `maskmin`/`maskmax` are not `-1`, hence the only real exercise of the mask branch), and a
  `BHresults.json` excerpt. ~350 KB. Verified not caught by `.gitignore`; note `tests/run/`
  **would** be, hence `fixtures/`.
- **`tests/test_extract_golden.py`** — construct `PostfitExtractor` against the fixture
  workspace, `WriteRoot` to `tmp_path`, compare every histogram bin against the recorded
  `PostFit_*.root`. Starts *after* quickFit, so it needs no binaries and no fit: it turns the
  6-minute loop into seconds for §2 and §6.
- **Runner** — pytest 7.0.1 from the LCG_102a view, already present in the environment
  `repro.py env` pins. No new dependency, no `pyproject.toml`, no ini file (pytest's defaults
  collect `tests/test_*.py` and do not collect `repro.py`). Invocation: `. setup.sh` then
  `python3 -m pytest tests -q`. Footgun to document: a bare shell picks up a broken pytest 8.4.2
  from `~/.local`; sourcing `setup.sh` first resolves it.
- **Autouse fixture** saving and restoring `ROOT.gErrorIgnoreLevel`, so no test can silently mute
  ROOT diagnostics for every test after it.
- File the four preserved defects in `KNOWN_ISSUES.md`.
- `tests/repro.py` is not touched.

### Wiring the unit suite into the reproducibility check

The unit suite must not be a second thing a developer can forget. `README.md` says **commit only
on PASS**, and if `check` is green while the unit suite is red, that sentence is misleading.

**`tests/run_all.sh`** — a thin wrapper, roughly ten lines, which runs the unit suite first as a
fail-fast gate and then `repro.py check`, passing `--quick` through:

```bash
python3 -m pytest tests -q || exit 1        # seconds; a red unit suite stops here
python3 tests/repro.py check "$@"           # 2-6 min
```

Ordering matters: the unit suite is seconds and `check` is minutes, so a broken extraction is
reported in seconds rather than after a full re-fit. `README.md`'s Reproducibility section gains
one line saying this is the command to run before committing.

**`tests/repro.py` is still not edited.** Adding a subcommand to it means changing the 1 117-line
file that is the safety net for this entire refactor, to gain something a wrapper already gives.
If it later turns out the wrapper is routinely bypassed, moving it inside `repro.py` is a small,
separate change.

**One open question, to be settled in this section rather than assumed.** `README.md` documents
`check` being run under the plain lxplus system `python3` (3.9.25, ROOT 6.40), and `repro.py`'s
`_import_root()` docstring explicitly warns against a sourced lsetup environment. The unit suite
requires the opposite: the LCG_102a view, because `ExtractPostfitFromWS.py:4` and
`ExtractFitParameters.py:4` use `from ROOT import *`, which ROOT 6.40 refuses outright.

Verified 2026-09-18 that after the LCG_102a setup a single `python3` satisfies both — ROOT
6.26/08 importable, wildcard import accepted, pytest 7.0.1 resolved from the view rather than the
broken 8.4.2 in `~/.local`, and `repro.py`'s `_import_root()` returning 6.26/08. What is **not**
yet verified is that a full `repro.py check` **passes** under that interpreter, since the
baselines were cut under the documented one. That is a 4–6 minute experiment, and it is the first
thing done in this section.

- If `check` passes unchanged under the LCG view, the wrapper is one environment and one command,
  and `repro.py`'s docstring warning is narrowed to the pyBumpHunter venv, which is what it is
  really about.
- If it does not, the wrapper sources the two environments in separate subshells and says so, and
  the discrepancy is filed as an issue — a reproducibility lock whose verdict depends on which
  ROOT reads the output files is a finding in its own right, not a detail to work around.

---

## §2 — `python/ExtractPostfitFromWS.py`: the chi2 group

### Objective

Refactor `getChi2()` into functions with a single purpose. Preserve the arithmetic, the six-bin
summary histogram's bin order and labels, the printed output, and the seven dictionaries written
onto the extractor. The gate at `run_anaFit.py:189` reads its p-value, so nothing here may move.

### `_compute_chi2_terms(...)`

**Original code:** lines 45–76.

**Responsibility:** Accumulate the chi2 over the bins the mask leaves in, and collect the per-bin
residuals.

**Inputs:**
- `h_data`: ROOT histogram of observed counts, already cropped to the postfit binning
- `h_postfit`: ROOT histogram of fitted values, same binning as `h_data`
- `nbins`: integer number of bins to iterate, taken from the residual template
- `maskmin`: float lower edge of the excluded window; `-1` excludes nothing
- `maskmax`: float upper edge of the excluded window; `-1` excludes nothing
- `maskisbinnumber`: True or False, selecting `ibin + 0.5` instead of the data bin centre as the
  quantity compared against the window
- `useSumW2`: True or False, selecting the data error instead of `sqrt(postfit)` as the
  denominator

**Outputs:**
- `chi2`: float sum of squared residuals over the retained bins
- `chi2bins`: integer count of bins that entered the sum
- `maskedchi2bins`: integer count of bins excluded by the mask
- `residuals`: list of `(bin number, residual)` pairs for every bin with a defined residual

**Test:**
- With postfit equal to data over three bins, verify `chi2` is exactly 0 and `chi2bins` is 3.
- With one bin holding data 110, postfit 100 and error 5, verify the Pearson denominator is used
  when `useSumW2=False` (chi2 = 1.0) and the data error when `useSumW2=True` (chi2 = 4.0).
- With a window covering the middle bin of three, verify that bin appears in `maskedchi2bins`,
  does not appear in `chi2bins`, and still appears in `residuals`.
- With `maskisbinnumber=True` and a window of `(1.4, 1.6)`, verify bin 2 is excluded although its
  bin centre lies far outside that window.
- With `maskmin=-1` and `maskmax=-1`, verify no bin is excluded.
- **Pins issue 41:** with one bin of zero data error and one bin of zero postfit, verify both are
  absent from `chi2`, from `chi2bins`, from `maskedchi2bins` and from `residuals` — they vanish
  entirely rather than being counted as agreeing.

### `_degrees_of_freedom(chi2bins, npars)`

**Original code:** line 77.

**Responsibility:** Return the degrees of freedom for the chi2.

**Inputs:** `chi2bins` integer, `npars` integer.

**Output:** `ndof` integer.

**Test:** Not worth a dedicated test as arithmetic. Worth one assertion recording that `ndof` can
reach zero or below when `npars >= chi2bins`, and that the current code then raises
`ZeroDivisionError` at the `chi2/ndof` on line 86 — a fails-closed behaviour that the refactor
preserves rather than guards.

### `_chi2_probability(chi2, ndof)`

**Original code:** line 80.

**Responsibility:** Convert the chi2 and degrees of freedom into a p-value.

**Inputs:** `chi2` float, `ndof` integer.

**Output:** `pval` float, the upper-tail probability.

**Test:** Verify one reference pair against `ROOT.Math.chisquared_cdf_c` computed independently in
the test, and verify a chi2 of 0 gives 1.0. This is a one-line wrapper; the test exists to catch a
future substitution of the wrong tail.

### `_build_residual_histogram(h_postfit, channelname, residuals)`

**Original code:** lines 41–43, 66–67.

**Responsibility:** Build the residual histogram on the postfit binning and fill it.

**Inputs:**
- `h_postfit`: ROOT histogram supplying the binning
- `channelname`: string used in the clone's name
- `residuals`: list of `(bin number, residual)` pairs

**Output:** `h_residuals`, a ROOT histogram detached from any directory.

**Test:**
- The clone is named `<channelname>/residuals`, as today.
- `SetDirectory(0)` has been applied, so the histogram outlives any open file.
- Bins named in `residuals` carry their value; every other bin is 0.
- Every bin error is 0.

### `_build_chi2_summary(chi2, chi2bins, npars, ndof, pval)`

**Original code:** lines 82–95, 105–110.

**Responsibility:** Pack the five chi2 quantities into the six-bin labelled summary histogram.

**Inputs:** `chi2` float, `chi2bins` integer, `npars` integer, `ndof` integer, `pval` float.

**Output:** `h_chi2`, a six-bin ROOT histogram detached from any directory.

**Test:** This histogram is a cross-file contract — `plotPostFit.py:50` reads bin 2,
`plot_postfit.cpp:140-141` reads bins 2 and 6, and `tests/repro.py` reads all six by label. The
test verifies:
- bins 1–6 hold chi2, chi2/ndof, nbins, npars, ndof and pval in that order;
- the six axis labels are exactly `chi2`, `chi2/ndof`, `nbins`, `npars`, `ndof`, `pval`;
- the bin 2 error is `ndoferr*chi2/(ndof*ndof)`, which is currently always 0 because `ndoferr` is
  the hardcoded 0 on line 78 — pinned so that a future non-zero `ndoferr` is a visible change;
- `SetDirectory(0)` has been applied.

### `_record_chi2(extractor, channelname, chi2, chi2bins, npars, ndof, pval, h_residuals, h_chi2)`

**Original code:** lines 112–119.

**Responsibility:** Store the computed quantities on the extractor.

**Inputs:** the extractor and the values above.

**Output:** None. Seven dictionaries on the extractor gain the channel key.

**Test:** Verify all seven dictionaries receive the key and the value handed in. This function is
the mutation that makes `getChi2` order-dependent; isolating it is what makes that visible, and
the test is one assertion per dictionary.

### `_print_chi2_summary(chi2, chi2bins, npars, ndof, pval)`

**Original code:** lines 97–103.

**Responsibility:** Print the six `TEST …` diagnostic lines.

**Inputs:** the five values. **Output:** None; writes to standard output.

**Test:** None. This is diagnostic output that nothing parses. If it is later found to be parsed,
a captured-stdout test is added then.

### Final role of `getChi2()`

**Original code:** lines 34–119. The signature `getChi2(extractor, channelname, npars,
useSumW2=False)` and the absence of a return value are preserved, because `Extract()` calls it
four times by keyword.

After extraction it coordinates: read `h_data` and `h_postfit` off the extractor; compute the chi2
terms; derive `ndof` and the p-value; build the residual histogram; build the summary histogram;
print the summary; record everything on the extractor.

### Existing functions retained

- **`getNPars(pdf, obs, exclSyst)`**, lines 13–26 — counts the non-constant, non-observable,
  non-nuisance parameters. One clear job. **Test:** build a two-parameter Gaussian in an in-memory
  `RooWorkspace` via `factory("Gaussian::g(x[0,10],m[5],s[1])")` and verify the observable is not
  counted, a constant parameter is not counted, and the remainder is.
- **`expHist(h)`**, lines 28–32 — undoes a logarithmic transformation in place. One clear job, and
  its statement order is load-bearing: the error is scaled by the **new** content, which is the
  correct `d(e^x) = e^x dx` propagation. **Test:** a three-bin histogram with one zero bin,
  verifying the zero bin is untouched and that the error of a non-zero bin is multiplied by
  `exp(content)` rather than by the original content.
- **`normalizePostFit(h_postfit, h_data)`**, lines 176–190 — its only call site in this repository
  is commented out at lines 290–291, so it is dead. **Decision for review:** delete it, or retain
  it with one test verifying the rescale uses the integrals outside the mask window. Deleting is
  the recommendation; it is trivially reversible.

---

## §3 — `python/run_anaFit.py`

### Objective

Refactor `build_fit_extract()` and `run_anaFit()` into functions with a single purpose. Preserve
the shell command strings character for character, the card substitution order, the derived
filenames, the p(chi2) gate and the return values. The orchestrators keep their signatures,
because the drivers and `main()` call them by keyword.

### Group A — command construction and failure reporting

#### `_failure_message(what, rtv, logfile)`

**Original code:** lines 53–61.

**Responsibility:** Build the text of the error raised when a shelled-out binary exits non-zero.

**Inputs:** `what` string naming the step, `rtv` integer exit code, `logfile` string path or None.

**Output:** `message` string.

**Test:** With `rtv=139`, verify the message says it was killed by signal 11. With `rtv=1`, verify
no signal sentence appears. With a `logfile`, verify the path appears; without one, verify no
dangling reference to a log.

#### `_xmlreader_command(topfile)` and `_quickfit_command(wsfile, poi_option, range_option, fitresultfile, logfile)`

**Original code:** lines 97–98 and 123.

**Responsibility:** Build the two binary invocations.

**Inputs:** as named; `poi_option` and `range_option` are the strings produced by the two helpers
below.

**Output:** `command` string.

**Test:** Verify the returned string equals the current command for one fixed set of arguments.
The assertion is deliberately an exact string match: these carry `--minStrat 2`, `--nllOffset 0`,
`--minTolerance 1E-6` and `--chi2fit 1`, every one of which changes a fitted number, and an exact
match is the only test that catches a dropped flag.

#### `_poi_option(poi)`

**Original code:** lines 99–106.

**Responsibility:** Turn the parameter of interest into the quickFit flag, and say which fit is
being run.

**Inputs:** `poi` string or None. **Output:** `poi_option` string, empty when `poi` is None.

**Test:** With a name, verify `-p <name>`. With None, verify the empty string.

#### `_mask_options(maskrange, channel)`

**Original code:** lines 108–117.

**Responsibility:** Turn the BumpHunter window into the quickFit range flag and the two mask
boundaries.

**Inputs:** `maskrange` pair of numbers or None, `channel` string.

**Outputs:** `range_option` string, `maskmin` number, `maskmax` number.

**Test:**
- With a window, verify `--range SBLo_<chan>,SBHi_<chan>` and that the two boundaries are returned
  unchanged.
- With None, verify the empty string and that **both** boundaries are `-1`. The pair matters: a
  single `-1` would make `_compute_chi2_terms` mask everything on one side, and nothing else in
  the code enforces that they travel together.

#### `_derived_output_paths(fitresultfile)`

**Original code:** lines 119–120, 131–132.

**Responsibility:** Derive every filename that is named after the fit result file.

**Inputs:** `fitresultfile` string.

**Output:** a mapping with `logfile`, `edmplot`, `postfitfile` and `parameterfile`.

**Test:** For `.../FitResult_anaFit_sixPar_bkgOnly.root`, verify all four derived names. Add one
assertion that the postfit name matches the `Form()` string `plot_postfit.cpp:34` builds
independently, quoting that line in the test — this contract currently exists only by convention
across five files and has no other check.

### Group B — inputs to the extractor

#### `_data_first_bin(datafile, datahist, rangelow)`

**Original code:** lines 134–137.

**Responsibility:** Read the data histogram and return the bin index just below the fit range.

**Inputs:** `datafile` string path, `datahist` string path within the file, `rangelow` number.

**Output:** `datafirstbin` integer.

**Test:** Against a synthetic file with known bin edges, verify the returned index is
`FindBin(rangelow) - 1`. Verify the file is closed before the function returns — this is the one
place in the module that already extracts a scalar before closing, and it is the pattern the rest
of the refactor follows.

#### `_resolve_binning(rebinfile, rebinhist, rangelow)`

**Original code:** lines 139–154.

**Responsibility:** Choose the rebinning histogram, generating it if the chosen file is absent.

**Inputs:** `rebinfile` string or None, `rebinhist` string or None, `rangelow` number.

**Outputs:** `binningFileName` string, `binningHistName` string.

**Test:**
- With both supplied, verify they are returned unchanged and no generation is attempted.
- With neither, verify the `dijetisrTLA` fallback names are built from `rangelow`.
- With a fallback path that does not exist, verify `createBinning.py` is invoked — and that its
  **return code is ignored**, as today. Pinning this is the point: the fallback truncates at
  1000 GeV, and both Run 2 drivers avoid it by supplying the pair.

#### `_extract_postfit(...)` and `_extract_parameters(fitresultfile, parameterfile)`

**Original code:** lines 156–192 and 195–196.

**Responsibility:** Construct the extractor, read the gating p-value, and write the two output
files.

**Inputs:** the extractor's arguments as listed at lines 168–180, plus `postfitfile` and
`channel`.

**Output:** `pval` float.

**Test:** Against the §1 fixture, verify the p-value equals the value recorded in the fixture's
`<channel>_bkgonly_rebinned/chi2` bin 6, and that the two output files are written. This is where
the `EXECUTE: pfe = PostfitExtractor(` banner at lines 156–166 goes: it prints a constructor call
that is *not* the one made, and it is the only consumer of those lines, so the refactor keeps it
but moves it next to the real construction where the divergence is visible.

### Group C — fit quality

#### `_read_fit_quality(fitresultfile)`

**Original code:** lines 73–82.

**Responsibility:** Read the fit status and covariance quality out of the fit result file.

**Inputs:** `fitresultfile` string path.

**Outputs:** `status` integer and `covqual` integer, or None when the file holds no `fitResult`.

**Test:** Against the §1 fixture, verify the recorded status and `covQual=2` are returned. Against
a file with no `fitResult`, verify None is returned, the warning is printed, and the file is
closed.

#### `_require_covqual(status, covqual, mincovqual, fitresultfile)`

**Original code:** lines 83–92.

**Responsibility:** Print the quality line and refuse a covariance worse than the floor.

**Inputs:** `status` integer, `covqual` integer, `mincovqual` integer, `fitresultfile` string.

**Output:** None; raises on an unacceptable fit.

**Test:** Pure integers, no ROOT.
- `covqual=2`, `mincovqual=2` passes.
- `covqual=1`, `mincovqual=2` raises, and the message names both numbers.
- Each of `-1, 0, 1, 2, 3` prints its documented meaning; an unrecognised value prints `unknown`.

`report_fit_quality()` keeps its name and signature and becomes the two-step coordinator.

### Group D — card preparation

#### `_check_rebin_pair(rebinfile, rebinhist)`

**Original code:** lines 226–238.

**Responsibility:** Refuse a half-given `--rebinfile`/`--rebinhist` pair.

**Inputs:** the two values. **Output:** None; raises `ValueError`.

**Test:** Both given passes; both absent passes; either one alone raises. Four cases, and the same
function replaces the duplicate guard at `ExtractPostfitFromWS.py:143-147` so the two cannot
drift.

#### `_temp_card_paths(folder, sigwidth, sigmean)`

**Original code:** lines 260–268.

**Responsibility:** Build the four temporary card paths inside the run folder.

**Inputs:** `folder` string, `sigwidth` float, `sigmean` number.

**Outputs:** `tmptopfile`, `tmpcategoryfile`, `tmpsignalfile`, `tmpbackgroundfile` strings.

**Test:** With `sigwidth=8`, verify the plain names. With `sigwidth=-999`, verify the top and
category names carry `_mR<sigmean>` and the other two do not — this is the Z′ sentinel, unreached
by either driver, and the test is the only thing that will exercise it.

#### `_link_dtd(folder)`

**Original code:** lines 255–259.

**Responsibility:** Symlink the DTD into the run folder if it is not already there.

**Inputs:** `folder` string. **Output:** None.

**Test:** With an empty directory, verify the link is created and points at
`config/dijetisrTLA/AnaWSBuilder.dtd` — note the `dijetisrTLA` copy is used for the `dijetTLA`
analyses, which is deliberate today. With the file already present, verify nothing is executed.

#### `_stage_cards(topfile, categoryfile, signalfile, tmptopfile, tmpcategoryfile, tmpsignalfile)`

**Original code:** lines 273–276.

**Responsibility:** Copy the template cards into the run folder.

**Inputs:** the three source paths and their three destinations.

**Output:** None.

**Test:** Verify each source is copied to its destination, and that a `signalfile` of None copies
nothing.

#### `_fill_top_card(tmptopfile, tmpcategoryfile, wsfile, signame)`

**Original code:** lines 278–282.

**Responsibility:** Substitute the three top-card placeholders.

**Inputs:** the path and the three values. **Output:** None; the file is rewritten.

**Test:** Against a three-line synthetic card, verify `CATEGORYFILE`, `OUTPUTFILE` and `SIGNAME`
are each replaced with the value supplied.

#### `_fill_category_card(tmpcategoryfile, datafile, datahist, rangelow, rangehigh, nbins, nbkg, nsig, signame, tmpsignalfile)`

**Original code:** lines 372–382.

**Responsibility:** Substitute the nine category-card placeholders.

**Inputs:** as named. **Output:** None; the file is rewritten.

**Test:** Against a synthetic card carrying all nine placeholders, verify each is replaced. Add
one assertion that `RANGELOW` is not corrupted by `RANGEHIGH` sharing its prefix — it does not
today, because neither is a prefix of the other, and the test records that so a future rename
cannot quietly break it.

#### `_signal_replacements(signame, sigmean, sigwidth, systdict)`

**Original code:** lines 384–423.

**Responsibility:** Build the ordered list of signal-card substitutions.

**Inputs:** `signame` string, `sigmean` number, `sigwidth` float, `systdict` mapping or None.

**Output:** `replacements`, a list of `(pattern, replacement)` pairs.

**Test:** Pure list building, no files.
- With `systdict=None`, verify exactly four entries: the three named values plus the
  `\[MAG_[a-zA-Z0-9_\-]*\]` → `[0]` sweep.
- Verify the sweep is **last**, since it exists to zero whatever the systematics did not fill.
- With a `systdict`, verify the six `NOMINAL_*` entries and one entry per scale and resolution
  source, and that a missing key raises rather than silently omitting a systematic.

### Group E — the prefit parameter plumbing

#### `_npars_from_filename(backgroundfile)`

**Original code:** lines 289–307.

**Responsibility:** Derive the number of background parameters from the card's file name.

**Inputs:** `backgroundfile` string path.

**Output:** `nPars` integer.

**Test:** Pure strings.
- `..._sixPar.template` gives 6; each of three, four, five, seven, eight, nine, ten gives its
  number.
- **Pins issue 42:** a name matching no keyword gives 5 rather than raising.
- **Pins the `if`/`elif` split:** a name containing both `three` and `four` gives 4, because
  `three` is tested with a separate `if` and every later keyword is an `elif`. This is a real
  ordering quirk and the test records it rather than repairing it.

#### `_parse_card_par_ranges(tmpbackgroundfile)`

**Original code:** lines 313–317.

**Responsibility:** Read the `[PARn, low, high]` placeholders out of the background card.

**Inputs:** `tmpbackgroundfile` string path.

**Output:** `cardmatches`, a list of `(index, low, high)` string triples.

**Test:** Against a synthetic card:
- a `<ModelItem` line yields its placeholders;
- a line containing `<!--` is skipped even when it holds placeholders;
- a line without `<ModelItem` is skipped;
- several placeholders on one line are all captured;
- negative and decimal bounds parse.

#### `_check_card_pars(cardmatches, nPars, backgroundfile)`

**Original code:** lines 319–334.

**Responsibility:** Refuse a card whose highest parameter index disagrees with `nPars`.

**Inputs:** `cardmatches` list, `nPars` integer, `backgroundfile` string.

**Output:** None; prints a warning, or exits.

**Test:** Pure values.
- Matching indices pass silently.
- An empty `cardmatches` warns and does not exit.
- A card declaring `PAR7` against `nPars=6` exits, and the message names both numbers.

#### `_card_par_ranges(cardmatches, nPars)`

**Original code:** lines 308–310, 336–341.

**Responsibility:** Build the parameter bounds, starting from the defaults and overriding with
whatever the card declares.

**Inputs:** `cardmatches` list, `nPars` integer.

**Outputs:** `parRangeLow` and `parRangeHigh`, lists of floats of length `nPars`.

**Test:**
- With no matches, verify `[1] + [-30]*(nPars-1)` and `[1] + [30]*(nPars-1)`.
- With a match for `PAR3`, verify only index 2 changes.
- Verify the first entry stays 1 in both lists unless the card overrides `PAR1`.

#### `_substitute_prefit_parameters(tmpbackgroundfile, initPars, nPars)`

**Original code:** lines 367–370.

**Responsibility:** Write the fitted starting values back into the background card.

**Inputs:** the path, `initPars` sequence of floats, `nPars` integer.

**Output:** None; the file is rewritten.

**Test:** Against a synthetic card holding `PAR1` … `PAR10`, verify each placeholder receives its
value. **Pins the unnumbered `PAR1`-before-`PAR10` entry in `KNOWN_ISSUES.md`:** with ten
parameters, `PAR10` is corrupted because `PAR1` is substituted first and matches its prefix. The
test records that this is the behaviour today and that it is harmless at five or six parameters,
which is all either driver uses.

#### `_format_nbkg(_nbkg)`

**Original code:** line 362.

**Responsibility:** Format the prefit background yield as the card's `value, min, max` triple.

**Inputs:** `_nbkg` float. **Output:** string.

**Test:** Verify `1.0e5` gives `1.0E+05, 0, 2.0E+05`, and that the upper bound is twice the
value. The card's fit range for `nbkg` comes from here, so the factor of two is a physics choice
worth pinning.

### Group F — the masking branch

#### `_fit_accepted(pval, maskthreshold)`

**Original code:** line 455, repeated at 518 and 529.

**Responsibility:** Decide whether a p(chi2) passes the gate.

**Inputs:** `pval` float, `maskthreshold` float. **Output:** True or False.

**Test:** Verify a p-value above the threshold passes and one below fails, and — the case worth
having — that a p-value **exactly equal** to the threshold fails, because the comparison is a
strict `>`. One boundary assertion guarding a publish-or-not decision.

#### `_run_bumphunter(postfitfile, channel, folder)`

**Original code:** lines 461–467.

**Responsibility:** Run the BumpHunter window search in its own virtual environment.

**Inputs:** `postfitfile` string, `channel` string, `folder` string.

**Output:** None; writes `<folder>/BHresults.json`.

**Test:** Verify the composed shell string activates the venv, passes
`<channel>_rebinned/postfit` and `<channel>_rebinned/data`, and deactivates. Exact-string match,
as in Group A. Worth recording in the test that these are the **non**-background-only histograms,
while the gate at line 189 reads the background-only one — a real asymmetry, not a typo to fix
here.

#### `_read_bh_results(folder)`

**Original code:** lines 485–486.

**Responsibility:** Load the BumpHunter results.

**Inputs:** `folder` string. **Output:** mapping with `MaskMin`, `MaskMax`, `BlindRange`.

**Test:** Against the §1 fixture excerpt, verify the three keys are read. Verify a truncated file
raises rather than returning partial results.

#### `_masked_card_paths(tmptopfile, tmpcategoryfile, wsfile, outputfile)`

**Original code:** lines 463, 488–490.

**Responsibility:** Derive the four masked-variant paths.

**Inputs:** the four unmasked paths. **Outputs:** the four masked paths.

**Test:** Verify `.xml` becomes `_masked.xml` and `.root` becomes `_masked.root` for each. One
assertion that a path containing `.root` elsewhere in a directory name is not corrupted, since
these use `str.replace` and not a suffix operation.

#### `_write_masked_cards(tmptopfilemasked, tmpcategoryfilemasked, tmptopfile, tmpcategoryfile, wsfile, wsfilemasked, blindrange)`

**Original code:** lines 492–500.

**Responsibility:** Copy the cards and inject the blinding attributes.

**Inputs:** as named; `blindrange` string as read from the BumpHunter results.

**Output:** None; two files are written.

**Test:** Against synthetic cards, verify `Blind="true"` is appended to the `OutputFile` attribute
and not elsewhere, that the category path and workspace path are repointed at their masked
variants, and that `BlindRange="<range>"` is appended to the `Binning` attribute.

#### `_run_limit(wsfile, poi, outputfile)`

**Original code:** lines 528–535.

**Responsibility:** Run `quickLimit`.

**Inputs:** `wsfile` string, `poi` string, `outputfile` string. **Output:** None.

**Test:** Exact-string match on the composed command. Flagged in the test docstring as
**unreached by either locked analysis**, so `repro.py` does not cover it and the string match is
the only check it has.

### Final role of `build_fit_extract()`

**Original code:** lines 95–198. Signature and the `(pval, postfitfile, parameterfile)` return
value preserved; it is called twice, at lines 439 and 502.

After extraction it coordinates: build the workspace; compose and run the fit; check fit quality;
plot the EDM trace; derive the output paths; read the first data bin; resolve the binning; extract
the postfit and the fit parameters; return the gating p-value and the two paths.

### Final role of `run_anaFit()`

**Original code:** lines 200–537. All 25 parameters and the `0` / `-1` return values preserved;
`main()` calls it by keyword and the drivers depend on the exit status.

After extraction it coordinates: validate the rebin pair; derive the channel and bin count; link
the DTD; stage and fill the cards; run the prefit and substitute its results; name the parameter
of interest; run the first fit; and, if the gate fails, run BumpHunter, write the masked cards,
run the second fit, and return `-1` if that also fails. Then the optional limit.

**Deleted first, as its own commit:** the `locals()` dump at lines 250–252. It prints whatever
local names happen to exist at that point, so it makes every later reordering a visible diff in
the log for no benefit. `repro.py` compares ROOT contents and the directory listing, never log
text, so removing it is free — and it removes the constraint that no line above it may move.

### Existing functions retained

- **`execute(cmd)`**, lines 12–16 — prints, flushes, shells out, returns the code. One job.
  **Test:** verify a successful command returns 0 and a failing one returns its code; verify
  stdout is flushed before the subprocess runs, which is what keeps the log interleaved.
- **`replaceinfile(f, old_new_list)`**, lines 18–31 — reads, applies a list of regex
  substitutions, writes back. One job. **Test:** verify substitutions apply in the order given;
  verify a non-list argument prints the error and exits rather than raising; verify the file is
  rewritten in place.
- **`getchannel(categoryfile)`**, lines 33–40 — reads the channel name out of the category card.
  One job. **Test:** a card with `Channel Name="J100yStar06"` returns that string; a card without
  one exits. Add an assertion that the result equals what the drivers' `sed` at
  `run_anaFit_run2.sh:78` extracts from the same card, since the two derivations must not diverge.
- **`execute_checked(cmd, what, logfile)`**, lines 42–62 — becomes a two-line coordinator over
  `execute()` and `_failure_message()`.

### `main()`

**Original code:** lines 539–628. Split into `_build_parser()` (the 23 `add_argument` calls),
`_load_systdict(sysfile, sigmean)` (lines 593–595) and the remaining coordination.

**Test for `_build_parser()`:** parse the exact argument list the J100 driver passes and verify
every value arrives with the right type — `rangelow` as a number, `rebinhist` with its spaces
intact, and the three store-true flags. This is the boundary between the shell and the Python and
nothing currently checks it.

**Test for `_load_systdict()`:** with no `--sysfile`, returns None; with one, returns the entry
keyed by `str(sigmean)`; with a sigmean absent from the file, raises where the file is read rather
than 400 lines later where the keys are used.

---

## §4 — `python/PreFit.py`

### Objective

Refactor `PreFitter.Fit()` into private functions with a single purpose. Preserve the current
formulas, ROOT operations, seed behaviour, public interface and return values.

This section follows the breakdown supplied by the repository owner, with additions noted where
the code contradicts the obvious reading.

### `_load_histogram()`

**Original code:** lines 44–46.

**Responsibility:** Open the configured ROOT file and retrieve the selected histogram.

**Inputs:**
- `datafile`: string containing the path to the ROOT data file
- `datahist`: string containing the histogram path within the ROOT file

**Outputs:**
- `root_file`: opened ROOT file object
- `histogram`: ROOT histogram retrieved from the file

The file object is returned alongside the histogram deliberately: the histogram is not detached
from its directory, so it stays valid only while the file is open. The caller closes it at line
171.

**Test:** Use a small ROOT stub and verify that the supplied file path is opened in read mode,
the supplied histogram path is passed to `Get()`, and the file and histogram objects returned by
the stub are returned unchanged.

### `_prepare_histogram(histogram, xMin, xMax, fitLog)`

**Original code:** lines 48–60.

**Responsibility:** Calculate the background-event count and apply the logarithmic transformation
when requested.

**Inputs:**
- `histogram`: ROOT histogram containing the data
- `xMin`: float containing the lower fit boundary
- `xMax`: float containing the upper fit boundary
- `fitLog`: True or False

**Outputs:**
- `nbkg`: float containing the histogram integral within the fit range
- `integral`: float containing the prepared histogram integral

The supplied histogram is also modified when `fitLog=True`.

**Tests:**
- With `fitLog=False`, verify that the correct range is used to calculate `nbkg` and that the
  histogram is not modified.
- With `fitLog=True`, supply a small histogram containing positive and zero-valued bins. Verify
  that positive bins and their errors are transformed correctly, while zero-valued bins remain
  unchanged.
- Verify that `nbkg` is calculated before the logarithmic transformation.
- **Addition:** verify the error is divided by the **original** content, because line 56 runs
  before line 57. A refactor that reorders those two statements changes every prefit error, and
  nothing else would catch it.
- **Addition:** verify `nbkg` uses `FindBin(xMin)` to `FindBin(xMax)` inclusive, while `integral`
  on line 59 is over the **whole** histogram and not the fit range. The two are deliberately
  different and read as if they were not.

### `_build_candidate_functions(xMin, xMax)`

**Original code:** lines 62–85.

**Responsibility:** Construct the normal and logarithmic candidate TF1 functions.

**Inputs:**
- `xMin`: float containing the lower fit boundary
- `xMax`: float containing the upper fit boundary

**Outputs:**
- `normal_functions`: dictionary mapping parameter counts to normal TF1 objects
- `log_functions`: dictionary mapping parameter counts to logarithmic TF1 objects

Each dictionary contains functions for parameter counts from 1 to 10.

**Test:** Use a fake TF1 constructor that records its arguments. Verify that both dictionaries
contain keys from 1 to 10, the expected function names are used, every function receives the
configured fit range, and a small representative selection of formulas matches the original
formula text. The test does not copy all twenty formulas into the test file.

**Addition:** whether these are generated from a table or left as twenty literals is a judgement
for review. Generating them removes ~1 200 characters of duplication and twenty copies of the
hardcoded `13000.`; keeping them literal removes any risk that a generator changes a formula. If
they are generated, the test asserts the generated strings equal the current literals character
for character, and additionally that `LogN(pars)(x) == log(N(pars)(x))` for matched parameters —
which is the only thing that would catch a single-character typo in one of twenty near-identical
strings.

### `_select_fit_function(normal_functions, log_functions, fitLog, nPars, parRangeLow, parRangeHigh)`

**Original code:** lines 87–93.

**Responsibility:** Select the required fitting function and apply its parameter limits.

**Inputs:**
- `normal_functions`: dictionary of normal candidate functions
- `log_functions`: dictionary of logarithmic candidate functions
- `fitLog`: True or False
- `nPars`: integer giving the required number of parameters
- `parRangeLow`: list of floats containing the lower parameter limits
- `parRangeHigh`: list of floats containing the upper parameter limits

**Output:** `fit_function`, the selected and configured TF1 object.

**Tests:**
- With `fitLog=True`, verify that the function is selected from the logarithmic collection.
- With `fitLog=False`, verify that the function is selected from the normal collection.
- Verify that the selected function has the number of parameters specified by `nPars`.
- Verify that each active parameter receives its corresponding lower and upper limits.

### `_find_best_parameter_sets(fit_function, integral, score_function, nRetries1, nRetries2, fitLog, xMin, xMax)`

**Original code:** lines 95–139. The range includes candidate generation, scoring, ranking,
progress output and sampling timing. The core ranking logic is on lines 102–132.

**Responsibility:** Generate trial parameter sets, score them, and retain the best candidates.

**Inputs:**
- `fit_function`: TF1 object whose parameters will be varied
- `integral`: float used to calculate the initial normalisation parameter
- `score_function`: callable accepting the fit function and returning a float
- `nRetries1`: integer giving the number of candidates to generate
- `nRetries2`: integer giving the number of candidates to retain
- `fitLog`, `xMin`, `xMax`: needed by the per-iteration limit on parameter 0 at lines 121–124

In production, `score_function` calls the histogram's chi-square operation. Passing it in keeps
the ranking function separate from the histogram.

**Output:** `best_candidates`, a list of tuples containing a `score` float and an independent
sequence of floating-point parameter values, holding `nRetries2` entries ordered from lowest to
highest score.

**Test:** Use a short, predetermined sequence of unsorted floating-point scores. Verify that the
scoring function is called `nRetries1` times, exactly `nRetries2` candidates are returned, the
returned candidates have the lowest scores from the supplied sequence, the results are ordered by
score, and each candidate contains an independent copy of its parameters. One controlled score
sequence is sufficient; a second randomised ranking test is unnecessary.

**Addition — the sampling loop is inert and must stay inert.** Lines 110–119 call
`SetParameter(0..9, …)` with literal values immediately after `RandomizeParameters()`, so every
randomized value is overwritten before scoring. With ten or fewer parameters the loop therefore
evaluates the same chi2 on every iteration, and `p0` at line 109 is a deterministic function of
`integral`. This is the second preserved defect. Two consequences for this section:

- The extracted function keeps those ten calls exactly where they are.
- One additional test asserts that two calls with **different seeds** return identical
  candidates. That test fails the moment someone "repairs" the randomization, which is the
  intent: it turns a silent physics change into a red test.

**Addition — the sentinel.** `best_chi2Pars` is seeded with `(inf, [])` at line 95 and trimmed by
`pop()` at line 132, so the sentinel survives whenever fewer than `nRetries2` candidates beat it.
`SetParameters` at line 147 would then receive an empty list. One test pins what happens today
with a score sequence shorter than `nRetries2`, rather than adding a guard.

### `_fit_best_candidates(histogram, fit_function, candidates, xMin, xMax)`

**Original code:** lines 141–156.

**Responsibility:** Run the final ROOT fit for each retained candidate and select the best-fitted
result.

**Inputs:**
- `histogram`: ROOT histogram to be fitted
- `fit_function`: configured TF1 object
- `candidates`: list containing score and parameter-sequence pairs
- `xMin`: float containing the lower fit boundary
- `xMax`: float containing the upper fit boundary

**Outputs:**
- `best_chi2`: float containing the lowest fitted chi-square
- `best_parameters`: sequence of floating-point parameters from the best fit

**Test:** Use a fake histogram that returns a controlled chi-square for each candidate. Verify
that each candidate's parameters are loaded into the fitting function, the histogram is fitted
once for each candidate, the configured fit range and existing fit options are used, and the
parameters associated with the lowest fitted chi-square are returned.

**Addition:** the fit options string `"R0QS"` is asserted exactly. `S` is what makes `Fit()`
return a result object at all, and `Q` suppresses the per-fit output; dropping either changes the
behaviour of the line that follows.

### `_report_fit_result(best_chi2, best_parameters, npar)`

**Original code:** lines 158–169.

**Responsibility:** Print the fitting completion message and final parameter values.

**Inputs:** `best_chi2` float, `best_parameters` sequence of floats, `npar` integer.

**Output:** None. The function writes the summary to standard output.

**Test:** A dedicated test is optional. If the console output is important to users, capture
standard output and verify that it contains the completion message, the best chi-square, and one
line for each fitted parameter. There is no need to test separators, spacing or stopwatch output
unless another program depends on their exact format. If the output is purely diagnostic, this
block may remain within `Fit()` rather than become a separate function.

### Final role of `Fit()`

**Original code:** lines 43–173. After extraction it coordinates the stages:

1. Load the histogram.
2. Prepare the histogram and calculate `nbkg`.
3. Build the candidate functions.
4. Select and configure the required function.
5. Find the best starting parameter sets.
6. Fit the retained candidates.
7. Report the result.
8. Close the input file.
9. Return the best parameters and `nbkg`.

**Output:** `bestPars`, a sequence of floating-point fitted parameter values, and `nbkg`, a float
containing the number of background events in the fit range.

### Existing function retained

**`RandomizeParameters(function)`**, lines 39–41. This function already performs one clear job and
does not need to be split.

**Responsibility:** Assign a random value to each active parameter within its configured range.

**Inputs:** `function`, a TF1-like object containing parameters; `parRangeLow` and `parRangeHigh`,
lists of floats stored on the `PreFitter` instance.

**Output:** None. The supplied function's parameters are modified.

**Test:** Use a fake function and a controlled random-number generator. Verify that one random
value is requested for each parameter, the correct lower and upper limits are used for each
request, and each resulting value is assigned to the corresponding parameter.

### `__init__` — one change

**Original code:** lines 35–37. Constructing a `PreFitter` currently sets
`SetDefaultMaxFunctionCalls(50000)` and `gErrorIgnoreLevel = 6001` process-wide, so merely
creating the object silences ROOT errors for the remainder of the run. These move into an explicit
`_configure_root()` that `Fit()` calls, leaving the constructor to store arguments and seed the
generator.

**Test:** Verify that constructing a `PreFitter` does not change `ROOT.gErrorIgnoreLevel`, and
that `_configure_root()` does. This is a behaviour change in the sense that the global is set
slightly later in the run; it is behaviour-preserving for the drivers, which construct and
immediately fit, and `repro.py check` is the evidence.

---

## §5 — `python/ExtractFitParameters.py`

### Objective

Refactor `FitParameterExtractor.Extract()` into functions with a single purpose. The output file's
three histograms, their names, bin labels and contents are preserved: `plot_postfit.cpp:64` reads
`postfit_params`.

### `_read_fit_result(wsfile)`

**Original code:** lines 18–26.

**Responsibility:** Open the fit result file and return the fitted quantities.

**Inputs:** `wsfile`, string path to the `FitResult_*.root` file.

**Outputs:**
- `parameters`: list of `(name, value, error)` triples, one per floating parameter
- `covariance`: list of lists of floats
- `correlation`: list of lists of floats

Returning plain values rather than the `RooFitResult` is deliberate: `argset`, `mat_cov` and
`mat_cor` are all owned by the file, so a helper that returned them would hand back objects that
die when the caller closes it.

**Test:** Against the §1 fixture, verify six parameters are returned with the recorded names,
values and errors, and that the covariance and correlation are six by six. Verify the file is
closed before the function returns.

### `_build_parameter_histogram(parameters)`

**Original code:** lines 28, 32, 36–41.

**Responsibility:** Build the one-dimensional histogram of postfit parameter values and errors.

**Inputs:** `parameters`, the list of triples.

**Output:** `h1_params`, a ROOT histogram named `postfit_params`, one bin per parameter, detached
from any directory.

**Test:** With three synthetic parameters, verify the histogram name, that bin *i* carries the
*i*-th value and error, and that each bin is labelled with the parameter name. Verify
`SetDirectory(0)`.

### `_matrix_to_histogram(matrix, name, title, labels)`

**Original code:** lines 29–30, 33–34, 47–56.

**Responsibility:** Build a two-dimensional histogram from a square matrix.

**Inputs:** `matrix` list of lists of floats, `name` string, `title` string, `labels` list of
strings.

**Output:** a ROOT two-dimensional histogram, detached from any directory.

**Test:** With a three-by-three asymmetric matrix, verify that element `[i][j]` lands in the bin
`GetBin(i+1, j+1)` — asymmetric so a transposition is caught — that both axes carry the labels,
and that `SetDirectory(0)` is applied. One test covers both the covariance and the correlation,
which are currently two near-identical blocks.

### `_find_signal_yield(parameters)`

**Original code:** lines 43–45.

**Responsibility:** Pick out the signal yield and its error from the parameter list.

**Inputs:** `parameters`, the list of triples.

**Outputs:** `nsig` float or None, `nsigErr` float or None.

**Test:** With a parameter named `nsig_myModel`, verify both are returned. With no such parameter,
verify both are None. With two matching parameters, verify the **last** wins, as today — worth
pinning because the match is a substring test, not an exact one.

### Final role of `Extract()`

**Original code:** lines 17–58. After extraction it coordinates: read the fit result; build the
parameter histogram; build the two matrix histograms; find the signal yield; store all five on the
instance.

### Existing functions retained

- **`WriteRoot(outfile)`**, lines 85–95 — extracts if needed, opens the output, writes the three
  histograms, closes. One job. **Test:** against the fixture, verify the output file contains
  `postfit_params`, `h2_cov` and `h2_cor`, and that calling it on a fresh extractor triggers
  `Extract()` exactly once.
- **The five lazy accessors**, lines 60–83 — each is three lines doing one thing. Left alone.
  **Test:** one parametrized test verifying each triggers `Extract()` when its cache is empty.
  Note `GetNsig()` and `GetNsigErr()` test falsiness, so a genuine yield of exactly 0.0 re-runs
  the extraction on every call; recorded, not fixed.

---

## §6 — `python/ExtractPostfitFromWS.py`: `PostfitExtractor.Extract()`

### Objective

Refactor the 137-line `Extract()` into functions with a single purpose without moving any number.
This is the most dangerous section in the plan and is placed after §1 so that it has a
seconds-long regression test, and after §2 so that the chi2 it calls four times is already pinned.

**Three constraints specific to this section:**

1. **ROOT lifetime.** `w`, `model`, `pdf`, `cat`, `obs`, `data`, `dataList`, `pdfi`, `x` and
   `pdf_bkg` are all owned by the workspace, which is owned by the file closed at line 327. Every
   extracted helper either takes already-detached histograms or returns plain values. No helper
   returns a workspace-owned object to a caller that might outlive the file.
2. **The four channel blocks are refactored in place, not collapsed.** Lines 229–263, 265–294,
   296–316 and 318–324 are near-identical, and merging them corrects the `hpdf`/`hpdf_bkg` scaling
   at line 270 and moves the background-only p-value.
3. **`self.datafirstbin` stops being reassigned.** Lines 314 and 322 overwrite a constructor
   argument that line 250 reads, so a second call to `Extract()` computes different bin edges. A
   local replaces it. This is behaviour-preserving for the single call the drivers make and is
   what makes the method safe to call from a test.

### `_open_workspace(wsfile, wsname)`

**Original code:** lines 193–194.

**Responsibility:** Open the workspace file and retrieve the workspace.

**Inputs:** `wsfile` string path, `wsname` string.

**Outputs:** `root_file` and `workspace`. Both returned, for the reason given in §4's
`_load_histogram()`: the workspace dies with the file.

**Test:** Against the §1 fixture, verify the workspace named `combWS` is returned and that a
missing name returns None rather than raising.

### `_load_data_histogram(datafile, datahist, undolog)`

**Original code:** lines 196–200.

**Responsibility:** Read the data histogram and detach it from its file.

**Inputs:** `datafile` string, `datahist` string, `undolog` True or False.

**Output:** `h_data`, a ROOT histogram detached from any directory.

**Test:** Against a synthetic file, verify the histogram is returned, that `SetDirectory(0)` has
been applied so it survives the file being closed, and that `undolog=True` applies `expHist`
while `undolog=False` leaves the contents alone.

### `_model_components(workspace, modelname)`

**Original code:** lines 202–213.

**Responsibility:** Pull the model, the combined pdf, the channel category and the split dataset
out of the workspace.

**Inputs:** `workspace`, `modelname` string.

**Outputs:** `pdf`, `cat`, `nChan` integer, `obs`, `data`, `dataList`. All but `nChan` are
workspace-owned and must not outlive it.

**Test:** Against the fixture, verify `nChan` is 1 and that the returned category's label is
`J100yStar06`. **Pins the multi-channel latent bug:** the test records that `cat.getLabel()` at
line 217 is read without advancing the category index, so `nChan > 1` would return the same label
every iteration and overwrite the dictionaries. Recorded, not fixed — both drivers are
single-channel.

### `_channel_npars(pdfi, x, externalnpars)`

**Original code:** lines 220–222.

**Responsibility:** Determine the parameter count used for the degrees of freedom.

**Inputs:** `pdfi`, `x`, `externalnpars` integer or None.

**Output:** `npars` integer.

**Test:** With `externalnpars=None`, verify `getNPars` is consulted; with a value, verify it
overrides. Against the fixture, verify the count is the recorded 6.

### `_background_only_pdf(workspace, channelname)`

**Original code:** lines 224–227.

**Responsibility:** Build the extended background-only pdf.

**Inputs:** `workspace`, `channelname` string.

**Output:** `pdf_bkg`, a workspace-owned pdf.

**Test:** Against the fixture, verify a pdf is returned and named
`pdf__background_ext_<channelname>`. **Records in its docstring** that this calls
`workspace.factory(...)`, i.e. it *mutates* a workspace opened `"READ"`, and that a second call
for the same channel would attempt to re-create an existing object. This is why the extractor is
single-use today.

### `_pdf_histogram(pdfi, x, expectedEvents, undolog)`

**Original code:** lines 229–240.

**Responsibility:** Turn a pdf into a histogram scaled to the expected number of events.

**Inputs:** `pdfi`, `x`, `expectedEvents` float, `undolog` True or False.

**Output:** `hpdf`, a ROOT histogram.

**Test:** With a synthetic pdf, verify the histogram integral equals `expectedEvents` after
scaling, and that a zero integral is swallowed by the bare `except` and leaves the histogram
unscaled — the current behaviour, pinned rather than replaced by a specific exception.

**This helper is used by the nominal block only.** The background-only block at lines 266–273
scales `hpdf` rather than `hpdf_bkg` and therefore cannot call it. That block keeps its own
inline scaling, with a comment naming the `KNOWN_ISSUES` entry, so the divergence is visible
rather than hidden behind a shared helper that does not match it.

### `_bin_edges_from_data(h_data, nBins, datafirstbin)`

**Original code:** lines 247–250.

**Responsibility:** Reconstruct the postfit bin edges from the data histogram.

**Inputs:** `h_data` ROOT histogram, `nBins` integer, `datafirstbin` integer.

**Output:** `binEdges`, a list of `nBins + 1` floats.

**Test:** With a ten-bin histogram of known edges, `nBins=3` and `datafirstbin=2`, verify the
returned edges are the data histogram's low edges 3 through 6. This offset is the only use of
`datafirstbin` in the method and is exactly what lines 314 and 322 currently corrupt.

### `_postfit_histogram(hpdf, nBins, binEdges)`

**Original code:** lines 252–257 (and 280–285).

**Responsibility:** Build the postfit histogram on the data binning and copy the pdf contents
into it.

**Inputs:** `hpdf` ROOT histogram, `nBins` integer, `binEdges` list of floats.

**Output:** `h_postfit`, a ROOT histogram detached from any directory.

**Test:** Verify the output has `nBins` bins on the supplied edges, that bin *i* carries
`hpdf`'s bin *i* content, that every error is 0, and that `SetDirectory(0)` is applied. Note the
histogram is named `postfit` for both the nominal and background-only cases, so two live at once
under the same ROOT name; the test records this rather than renaming them.

### `_crop_data(h_data, nBins, binEdges)`

**Original code:** lines 259–260 (and 287–288).

**Responsibility:** Rebin the data histogram onto the postfit binning.

**Inputs:** `h_data`, `nBins` integer, `binEdges` list of floats.

**Output:** a ROOT histogram detached from any directory.

**Test:** Verify the contents are the sums of the source bins within each new edge pair, and that
`SetDirectory(0)` is applied explicitly rather than inherited.

### `_rebin_edges(rebinfile, rebinhist, h_postfit)`

**Original code:** lines 296–309.

**Responsibility:** Read the resolution binning and clip it to the fitted range.

**Inputs:** `rebinfile` string, `rebinhist` string, `h_postfit` ROOT histogram supplying the
range.

**Output:** `binEdges`, a list of floats.

**Test:** With a synthetic binning histogram spanning wider than the postfit range, verify edges
below the postfit's first low edge and above its last are dropped and the rest are kept in order.
Verify the comparison uses `GetBinLowEdge(GetNbinsX()+2)` as the upper limit, which is one bin
beyond the last edge — currently deliberate, and a test is the only record of that.

### `_rebin_channel(h_postfit, h_data, binEdges, datahist)`

**Original code:** lines 312–313 (and 320–321).

**Responsibility:** Rebin a channel's postfit and data histograms onto the resolution binning.

**Inputs:** `h_postfit`, `h_data`, `binEdges` list of floats, `datahist` string used as the
rebinned data histogram's name.

**Outputs:** the two rebinned histograms.

**Test:** Verify both are rebinned onto the supplied edges and — the point of the test — that both
have `SetDirectory(0)` applied **explicitly**. Today they inherit directory-0 from their already
detached sources, which works only as long as that chain is unbroken, and these are the
histograms `run_anaFit.py:189` reads the gating p-value from.

### Final role of `Extract()`

**Original code:** lines 191–327. Signature and the absence of a return value preserved, since
`WriteRoot` and the nine accessors all call it.

After extraction it coordinates: open the workspace; load the data histogram; pull the model
components; then, per channel — derive the pdf and parameter count, build the nominal postfit and
its chi2, build the background-only postfit and its chi2, build the rebinned pair and their chi2s
— and finally close both files.

### `WriteRoot()` — one deletion

**Original code:** lines 329–352. The `dirPerCategory=False` branch at lines 344–350 calls
`self.channel_hpostfit.values()[-1]`, and `dict_values` is not subscriptable in Python 3, so this
branch has raised `TypeError` on every invocation under the interpreter this repository runs. It
is deleted rather than preserved; the parameter stays for signature compatibility with the
standalone `main()` at line 424, which is the only other caller.

**Test:** against the fixture, verify the output file has one directory per channel, each holding
`data`, `postfit`, `residuals` and `chi2`. This is the file `tests/repro.py` reads, so its shape
is a hard contract.

---

## §7 — `python/FindBHWindow.py`

### Objective

Refactor `main()` into functions with a single purpose. Preserve the BumpHunter configuration
exactly — `width_min=2`, `width_max=3`, `npe=10000`, `nworker=1`, `seed=666` all change the
result, and `tests/repro.py` compares `seed` and `npe` exactly. This module runs in its own
virtual environment and cannot be imported from the main one, so its tests exercise the extracted
pure functions only.

### `_load_histograms(inputfile, bkghist, datahist)`

**Original code:** lines 36–43.

**Responsibility:** Read the background and data histograms out of the postfit file.

**Inputs:** `inputfile` string path, `bkghist` string path within the file, `datahist` string
path.

**Outputs:** `bkg` array of floats, `bins` array of edges, `data` array of floats, `bins_data`
array of edges.

**Test:** Against the §1 fixture read with `uproot`, verify four arrays of the recorded lengths.
Skipped automatically when `uproot` is unavailable, which it is in the main environment.

### `_crop_data_to_bkg_range(data, bins_data, bins)`

**Original code:** lines 45–57.

**Responsibility:** Cut the data array down to the background histogram's range.

**Inputs:** `data` array of floats, `bins_data` array of edges, `bins` array of background edges.

**Outputs:** `data` cropped array, `firstbindata` integer index of the first retained edge.

**Test:** Pure arrays, no ROOT and no BumpHunter.
- With data edges extending below and above the background range, verify `firstbindata` is the
  index of the first data edge at or above `bins[0]`.
- **Pins the off-by-one:** `lastbindata` is the index of the last data edge at or **below**
  `bins[-1]`, and is then used as an **exclusive** slice end, so the final bin inside the range is
  dropped. The test asserts the current length, with a comment naming it as suspicious and
  unfixed. This is exactly the sort of thing the plan exists to make visible rather than to
  silently repair.
- With identical ranges, verify `firstbindata` is 0.

### `_configure_hunter(bins)`

**Original code:** lines 60–68.

**Responsibility:** Construct the BumpHunter instance with its fixed configuration.

**Inputs:** `bins` array of edges.

**Output:** a configured `BumpHunter1D`.

**Test:** Verify each of the seven configuration values is passed. `seed=666` and `nworker=1` are
asserted explicitly: `nworker` above 1 reorders the pseudo-experiments and changes `global_Pval`
even at a fixed seed.

### `_mask_window(state, bins, firstbindata, usebinnumbers)`

**Original code:** lines 98–105.

**Responsibility:** Convert the winning scan window into the mask boundaries and the blind range
string.

**Inputs:** `state` mapping from `save_state()`, holding `min_loc_ar` and `min_width_ar`; `bins`
array of edges; `firstbindata` integer; `usebinnumbers` True or False.

**Outputs:** `MaskMin`, `MaskMax` and `BlindRange` values.

**Test:** Pure arithmetic over a synthetic `state`.
- With `usebinnumbers=False`, verify the boundaries are the bin **edges** at `min_loc_ar[0]` and
  at `min_loc_ar[0] + min_width_ar[0]`.
- With `usebinnumbers=True`, verify they are bin **numbers** offset by `firstbindata`. Neither Run
  2 driver sets this flag, so this test is the only thing that exercises that branch.
- Verify `BlindRange` is the two values formatted as `%d,%d`, i.e. **truncated to integers** — the
  mask boundary that reaches the XML card is an integer even when the edge is not, and that
  rounding is a physics-visible choice.

### `_write_results(out_dict, outputjson)`

**Original code:** lines 107–110.

**Responsibility:** Write the results as JSON, encoding numpy scalars.

**Inputs:** `out_dict` mapping, `outputjson` string path.

**Output:** None.

**Test:** With a dictionary holding a numpy integer, a numpy float and a numpy array, verify the
file parses back as plain JSON types. Verify the four keys `plot_postfit.cpp:127-130` scrapes are
present at the level it expects — `MaskMin` and `MaskMax` at the top level, `global_Pval` and
`significance` nested under `pyBHresult`. The C++ regex searches the whole file, so it finds the
nested pair; the test records the nesting so a future flattening is a deliberate change.

### Final role of `main()`

**Original code:** lines 22–110. After extraction it parses arguments, loads the histograms, crops
the data, configures and runs the scan, saves the two plots, derives the mask window, and writes
the JSON.

**Left as it is:** the two plot filenames at lines 88 and 91 are bare relative paths, so they land
in whatever directory the process was started from — the repository root, for every run including
`repro.py check`. That is `KNOWN_ISSUES` issue 23, it predates this work, and it stays open.

### Existing class retained

**`NpEncoder`**, lines 12–20 — converts numpy scalars and arrays for the JSON encoder. One clear
job. **Test:** one assertion per type, plus one that an unhandled type still raises.

---

## §8 — `python/plotPostFit.py` and `plot_edm.py`

### Objective

`plotPostFit.py` has no functions at all and calls `parse_args()` at import, so it cannot be
imported without consuming `sys.argv`. Give it a `main()` and helpers; the rendered plot must be
unchanged.

### `plotPostFit.py`

#### `_parse_args(argv)`

**Original code:** lines 6–16. **Responsibility:** Define and parse the four options.
**Inputs:** `argv` list of strings. **Output:** the parsed arguments.

**Test:** Parse the exact argument list the drivers pass at `run_anaFit_run2.sh:133-135`,
including a channel name with no spaces and a label with spaces and a hyphen. Verify the defaults
for `-c` and `-l`.

#### `_load_histograms(postfit_file, channel)`

**Original code:** lines 18–20, 46.

**Responsibility:** Retrieve the three histograms this plot needs.

**Inputs:** an open ROOT file, `channel` string.

**Outputs:** `data`, `postfit` and `h_rchi2` histograms.

**Test:** Against a synthetic PostFit-shaped file, verify the three are read from
`<channel>/data`, `<channel>/postfit` and `<channel>/chi2`. **Records the asymmetry:** this reads
the *unrebinned, non-background-only* channel, while the gate reads
`<channel>_bkgonly_rebinned` and `plot_postfit.cpp` reads `<channel>_bkgonly`. Three consumers,
three conventions, one file — the test states it rather than changing it.

#### `_style_histograms(data, postfit)`

**Original code:** lines 21–26. **Responsibility:** Apply the marker and line styling.
**Inputs:** the two histograms. **Output:** None.

**Test:** Verify marker style 8, size 0.5, black, line width 0 on the data, and width 2 with
`kAzure+7` on the postfit. Cheap and it catches an accidental restyle.

#### `_draw_main_pad(data, postfit)`

**Original code:** lines 28–39. **Responsibility:** Build the top pad with its legend.
**Inputs:** the two histograms. **Outputs:** the canvas, the pad and the legend, all of which must
be kept alive by the caller.

**Test:** Verify the pad geometry `(0, 0.3, 1, 1.0)`, a bottom margin of 0 and two legend entries.
The objects are returned rather than left to garbage collection, which is the only reason the
plot survives the function boundary.

#### `_draw_fit_labels(rchi2, label)`

**Original code:** lines 41–57. **Responsibility:** Draw the chi2 line and the which-fit-is-this
label.

**Inputs:** `rchi2` float, `label` string.

**Output:** the `TLatex`, which must stay alive.

**Test:** Verify the chi2 text is formatted to three decimals; verify the label is drawn only when
non-empty. **Pins issue 45:** the value comes from bin 2 of the chi2 histogram, not bin 6, and the
test asserts the caller passed `GetBinContent(2)` — the mislabel this fixed is exactly the sort of
regression a later edit could reintroduce.

#### `_draw_ratio_pad(data, postfit)`

**Original code:** lines 60–88. **Responsibility:** Build the data-over-postfit ratio pad.

**Inputs:** the two histograms. **Outputs:** the pad and the ratio histogram.

**Test:** With data of 110 and postfit of 100 in one bin, verify the ratio is 1.1. Verify the
y-axis range `(0.85, 1.15)`, which is a hard clip: a ratio outside it is drawn off-scale rather
than flagged.

#### Final role of `main(argv)`

**Original code:** lines 1–94. Parses arguments, opens the file, loads and styles the histograms,
draws both pads and the labels, saves, closes. The two `ROOT.gStyle`/`gROOT` calls at lines 3–4
move inside `main()` so that importing the module no longer mutates ROOT.

### `plot_edm.py`

#### `parse_edm_trace(filename)`

**Original code:** lines 8–39.

**Responsibility:** Scrape the EDM values out of a quickFit Minuit2 log.

**Inputs:** `filename` string path.

**Outputs:** `cumulative_x` list of integers, `edm_values` list of floats, `star_indices` list of
integers marking where the log's internal counter restarts.

**Test:** Against a six-line synthetic log excerpt:
- a matching `VariableMetric` line yields its EDM;
- a line whose internal iteration is 0 adds an entry to `star_indices`;
- a non-matching line is skipped;
- scientific notation parses;
- a missing file prints the error and exits, rather than raising.

This is the only pure function in the file and the one place a silent regex drift would go
unnoticed, since `run_anaFit.py:129` calls this script with plain `execute()` and ignores its exit
code.

#### `_plot_edm_trace(cumulative_x, edm_values, star_indices, outname)`

**Original code:** lines 41–70. **Responsibility:** Render and save the trace.

**Inputs:** the three lists and the output path. **Output:** None.

**Test:** None beyond verifying the file is created. It is a diagnostic plot that nothing reads
programmatically.

**One addition:** the module imports `matplotlib.pyplot` at line 3 without selecting a
non-interactive backend, unlike `FindBHWindow.py` which sets `Agg` at line 2. It works today
because the drivers run headless. Setting `Agg` here too is a one-line change that removes a
latent dependence on `$DISPLAY` — offered for review, not assumed.

---

## §9 — The shell drivers

### Objective

`scripts/run_anaFit_run2.sh` and `scripts/run_anaFit_run2_J50.sh` differ only in comments and
fourteen variable assignments; from line ~79 onward they are byte-identical. Decompose the shared
body into single-purpose shell functions in `scripts/lib/anafit_driver.sh`, leaving each driver as
its configuration block plus one call. The failure mode this removes is "edited J100, forgot J50".

`tests/repro.py` invokes both drivers by path, and that stays true: each file keeps its name,
keeps being run the same way, and keeps its exit status.

### `_setup_environment(out_dir)`

**Original code:** `run_anaFit_run2.sh` lines 18–23.

**Responsibility:** Source the build environment and create the output directory.

**Inputs:** `out_dir` string.

**Output:** Returns non-zero when the setup guard fires.

**Test:** With the working directory outside the repository root, verify the driver stops with the
error message rather than continuing — this is issue 43, fixed once and easy to reintroduce,
because `return` inside a sourced script returns only from that script.

### `_build_flags(dosignal, dolimit, doprefit)`

**Original code:** lines 83–86.

**Responsibility:** Turn the three switches into the optional command-line flags.

**Inputs:** three integers.

**Output:** `flags` string.

**Test:** All eight combinations, verifying flag presence and order.

### `_run_anafit(...)`

**Original code:** lines 88–110.

**Responsibility:** Invoke `run_anaFit.py` with the configured arguments and record its exit
status.

**Inputs:** every configured value.

**Output:** the exit status.

**Test:** This is the point of the section. Add one line to the driver in the idiom it already
uses for `out_dir=${OUT_DIR:-$PWD/run}`:

```bash
run_anafit=${RUN_ANAFIT:-./python/run_anaFit.py}
```

Then `tests/test_drivers.py` runs each driver with `RUN_ANAFIT` pointing at a stub that echoes its
arguments and exits 0, and verifies:
- the J100 flags carry `--rangelow 481`, `--rangehigh 3000` and the J100 data and rebin paths;
- the J50 flags carry `302`, `2997` and the J50 paths;
- `--doprefit` is present and `--dosignal` and `--dolimit` are absent for both;
- `--rebinhist` survives with its spaces intact;
- **the two drivers emit the same set of flag names**, differing in exactly the ten known values.
  That last assertion fails the moment a flag is added to one driver and not the other.

Plus `bash -n` on both files. The whole file runs in under a second.

### `_select_postfit(folder, pars)`

**Original code:** lines 127–132.

**Responsibility:** Choose between the masked and unmasked postfit file and the matching label.

**Inputs:** `folder` string, `pars` string.

**Outputs:** `postfit_to_plot` path and `postfit_label` string.

**Test:** With only the unmasked file present, verify the unmasked path and the label
`unmasked fit`. With the masked file also present, verify the masked path and the masked label.
**This is issue 48**, which was fixed by exactly this branch; the test is what stops it being
undone.

### `_make_plots(postfit_to_plot, folder, channel, label, pars)`

**Original code:** lines 133–137.

**Responsibility:** Run the Python plotter and the ROOT macro.

**Inputs:** as named.

**Output:** None.

**Test:** With `python` and `root` replaced by recording stubs on `PATH`, verify both are invoked
with the expected arguments, including the quoted channel and label.

### `_report_failure(anafit_failed, out_dir)`

**Original code:** lines 141–150.

**Responsibility:** Print the failure banner and propagate the exit status.

**Inputs:** `anafit_failed` string, possibly empty; `out_dir` string.

**Output:** the exit status.

**Test:** With a status of 0, verify nothing is printed. With a non-zero status, verify the banner
is printed and the status propagates. **Records issue 47:** the banner claims the fit failed the
p(chi2) gate, but it fires on *any* non-zero exit, including a traceback or the `ValueError` from
the rebin-pair guard. The test asserts today's wording and links the issue; the wording is not
changed here.

### Final role of each driver

Its configuration block — the fourteen values — followed by one call into the shared body.

**Trade-off, stated for review:** hoisting the shared body into a sourced library means the two
drivers no longer read top to bottom as a single script, which is how every other driver in
`scripts/` is written. The alternative is to leave them duplicated and rely on the
same-set-of-flags test to catch divergence. The test is worth having either way; the hoist is the
part worth a decision.

---

## §10 — `plot_postfit.cpp`

### Objective

Decompose the 257-line `plot_postfit()` for readability. **Structural only**, per the repository
owner's decision: only the JSON scraper gets a unit test, and the rest is verified by comparing
the rendered PDF against one produced before the change. Placed last, done in one commit,
reviewed by eye.

**The honest ceiling:** `tests/repro.py` compares plot *filenames*, not contents. A decomposition
that drops a panel, loses the red masked overlay or mis-scales an axis passes every automated
check in this repository.

### `get_val(json_str, key)` — the one tested function

**Original code:** lines 118–125, currently a lambda capturing `json_str`.

**Responsibility:** Scrape one numeric value out of the BumpHunter JSON by key.

**Inputs:** `json_str` string, `key` string.

**Output:** float; `0.0f` when the key is absent.

Hoisted into a header `plot_postfit_utils.h` that the macro includes, and tested by
`tests/test_plot_postfit_utils.C` run under `root -l -b -q` from a one-line pytest wrapper.

**Test:** Verify a plain value, a value in scientific notation, a negative value, and — the one
that matters — that an absent key returns `0.0f`. The caller warns only when `global_Pval` **and**
`significance` are both zero, so a renamed `MaskMin` would silently draw the blinded window at
`[0, 0]` with no warning at all. The test pins that contract so the conflation is at least
written down.

### `open_inputs(in_dir, pars_str)`

**Original code:** lines 33–44.

**Responsibility:** Build the six filenames and open the four input files.

**Inputs:** `in_dir` and `pars_str` strings.

**Output:** a struct owning the four `unique_ptr<TFile>` and holding the two output paths.

**The lifetime constraint:** the ten histograms below are owned by these files. The struct is
returned by value and kept alive in `plot_postfit()` for the whole function, exactly as the four
local `unique_ptr`s are today. Any helper that returned histograms while letting the files go out
of scope would leave every pointer dangling — this is the single most dangerous split in the
plan, and the reason the loader returns the owners rather than the contents.

### `load_histograms(inputs, chan)`

**Original code:** lines 46–88.

**Responsibility:** Retrieve the ten histograms and apply the masked colouring.

**Inputs:** the struct from `open_inputs`, `chan` string.

**Output:** a struct of ten raw `TH1D*`, non-owning.

Verified by eye against a before-and-after PDF. Note the existing null-guard at line 82 covers
`h_native`, `h_native_rebinned` and `h_native_chi2` but **not** `h_native_params`, which is
dereferenced at line 177; and `h.second` is drawn at line 219 whenever `BHresults.json` exists,
even if the masked PostFit file does not. Both recorded as new `KNOWN_ISSUES` entries in this
section, neither fixed.

### `read_fit_summary(h_chi2, h_chi2_rebinned, h_params)`

**Original code:** lines 140–162.

**Responsibility:** Pull the chi2-per-ndof, the p-value and the background yield out of the
summary histograms.

**Inputs:** the three histograms, any of which may be null.

**Output:** a struct of five floats, zero-filled when a histogram is absent.

This collapses twelve parallel `native_*`/`masked_*` floats into two instances of one struct.
Bins 2 and 6 are read here and nowhere else, which is the point: they are currently read at four
separate sites and written at `ExtractPostfitFromWS.py:84-95`.

### `draw_panel(...)` and `draw_labels(...)`

**Original code:** lines 174–283, the loop body.

**Responsibility:** Draw one page of the output PDF, and draw the label block on it.

Split so the parameter panel's special cases — the different y-range at line 184, the suppressed
zero line at 198, the suppressed range label at 241 — read as conditions rather than as
`h.first == h_native_params` repeated six times.

### Verification for this section

1. Copy `run/run_481_3000_sixPar/post_fit.pdf` and the J50 one aside before the change.
2. Re-run the macro after it.
3. `pdftoppm -r 50 -png` both and compare with ImageMagick `compare -metric AE`; a non-zero count
   is investigated, not accepted. Raw PDF bytes always differ because ROOT embeds a timestamp,
   which is why the comparison is on the raster.
4. Open both PDFs and look at them. For this file that is not a formality — it is the primary
   check, and the raster comparison is the backstop.

---

## Verification

Per section, before stopping for review:

```bash
. setup.sh
bash tests/run_all.sh --quick                 # unit suite, then J100 only, ~2 min; while iterating
bash tests/run_all.sh                         # unit suite, then both analyses, ~4-6 min
```

`tests/run_all.sh` is built in §1 and runs the unit suite first as a fail-fast gate, so an
extraction that broke something is reported in seconds rather than after a full re-fit. The two
underlying commands stay available and are what a bisect uses:

```bash
python3 -m pytest tests -q                    # seconds
python3 tests/repro.py check --quick          # ~2 min
python3 tests/repro.py check                  # ~4-6 min
```

**Both suites green is the gate**, and a section is not offered for review on anything less. A
failure is diagnosed, not accommodated, and never resolved by `record --force`. §10 additionally
requires the raster and visual comparison described above.

Every test named in §2 through §10 is reached by that one command, because pytest collects
`tests/test_*.py` by default and the ROOT-macro test in §10 is invoked through a one-line pytest
wrapper rather than being run by hand. Nothing in this plan produces a check that only runs if
someone remembers it.

## Effort

Roughly 12–14 working days, dominated by §3 (`run_anaFit.py`, some forty extracted functions) and
§6. The §1 fixture-based regression test pays for itself by §2. The §10 estimate is the least
certain, because it is the only section where being wrong is discovered by looking at a picture.

## Files

Changed: `python/run_anaFit.py`, `python/PreFit.py`, `python/ExtractPostfitFromWS.py`,
`python/ExtractFitParameters.py`, `python/FindBHWindow.py`, `python/plotPostFit.py`,
`plot_edm.py`, `plot_postfit.cpp`, `scripts/run_anaFit_run2.sh`,
`scripts/run_anaFit_run2_J50.sh`, `KNOWN_ISSUES.md`, `README.md`, `CHANGELOG.md`.

Added: `tests/conftest.py`, `tests/run_all.sh`, `tests/fixtures/*.root`, `tests/test_*.py`,
`tests/test_plot_postfit_utils.C`, `plot_postfit_utils.h`, `scripts/lib/anafit_driver.sh`.

Untouched: `tests/repro.py`, `tests/baseline_J100.json`, `tests/baseline_J50.json`, and the four
pinned sub-framework clones.
